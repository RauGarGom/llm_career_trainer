import os, getpass
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
os.environ["LANGCHAIN_PROJECT"] = "langchain-academy"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
from langchain_google_genai import ChatGoogleGenerativeAI
# from pdfminer.high_level import extract_text # No longer needed here
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
from langchain_core.prompts import ChatPromptTemplate
from IPython.display import Image, display
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage, AnyMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Any, Optional
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END

class OverallState(BaseModel):
    messages: list[AnyMessage] = Field(description="A list of Langchain messages from the past conversation")
    cv: Optional[str] = Field(description="A string containing professional and academic background of a candidate") # Corrected typo in description
    score: Optional[int] = Field(description="A number ranging from 0 to 10, depending on how good the las answer from the human was")
    num_questions: int = Field(description="Number of questions asked to the human")
    should_end: bool = Field(default=False, description="Whether the LLM thinks the interview should end")
    current_human_input: Optional[str] = Field(default=None, description="The most recent input from the human user")


chatbot_prompt = '''
   You are a technical interviewer for an AI Engineer role. You're interviewing a person with the cv {cv}, and this is your past conversation:
   {past_messages}

   Based on the conversation and CV, provide a question related to the role and the cv of the candidate
   '''
scoring_prompt = '''
   {cv}
   {past_messages}

   Based on the conversation and CV, provide a numeric score, based on how exact last's answer was.

   The answer must be an integer, ranging from 0 to 10. Always follow this format. NEVER PROVIDE ANYTHING THAT IS NOT A NUMBER
   '''

ender_prompt = '''
   {cv}
   {past_messages}
   {score}

   Based on the conversation, CV and score of the previous answers, end the conversation with the human in a warm but professional way. 
   Inform the human that the conversation is over, and make a justified decision on whether to hire the candidate or not.

   In a separate line, explain thoroughfully the reason of your decision, and give advice to the candidate should they won't be hired.
   '''

should_end_prompt = '''
{past_messages}

Should the interview end now? Base your decision on the following points:
   -The human is asking to end the conversation.
   -The past messages contain repetitions of concepts, such as more than one question about the same technology or experience.
YOU MUST ONLY Respond with "yes" or "no" only.
'''

def cv_reader(state:OverallState):
    # CV text is now expected to be in state.cv, populated by app.py
    # This node can be used for any initial processing if needed,
    # or simply pass the state along.
    # For now, it ensures the cv is part of the returned state.
    print("CV Reader node: CV should be pre-loaded in state.")
    if not state.cv:
        print("Warning: CV text is missing in the state for cv_reader node.")
        # Optionally, handle this case, e.g., by returning an error or a default CV
        # For now, we'll proceed, but this indicates an issue in app.py's setup
    return {"cv": state.cv, "messages": state.messages} # Ensure messages are carried forward

def chatbot(state: OverallState):
    print("Preparing an answer")
    chat_prompt = ChatPromptTemplate.from_template(chatbot_prompt)
    chat_chain = chat_prompt | model
    score_prompt = ChatPromptTemplate.from_template(scoring_prompt)
    score_chain = score_prompt | model
    
    # Pass the variables as a dict
    chat_response = chat_chain.invoke({"cv": state.cv, "past_messages": state.messages})
    score_response = score_chain.invoke({"cv": state.cv, "past_messages": state.messages})
    # print(chat_response)
    # print(score_response)
    print(f"Score: {score_response.content}")
    print(f"Chatbot: {chat_response.content}")

    all_msg = state.messages + [AIMessage(content=chat_response.content)]
    
    should_end_chain = ChatPromptTemplate.from_template(should_end_prompt) | model
    should_end_response = should_end_chain.invoke({"past_messages": state.messages})
    should_end = should_end_response.content.strip().lower() == "yes"

    print(f"Chatbot DEBUG: should_end: {should_end}")
        
    return OverallState(
        messages=all_msg,
        cv=state.cv,
        score=int(score_response.content),
        num_questions= state.num_questions + 1,
        should_end=should_end
    )

def human_response(state: OverallState):
    response = input("Enter your response: ")
    all_msg = state.messages + [HumanMessage(content=response)]

    print(f"Human: {response}")

    response = state.current_human_input
    if response is None:
        # This case should ideally be handled by app.py or graph logic
        # to ensure human_response is only called when there's input.
        print("Error: human_response called without input.")
        # Adding a dummy HumanMessage to avoid breaking the chain,
        # but this signifies a flaw in the flow from app.py
        all_msg = state.messages + [HumanMessage(content="[No input provided]")]
    else:
        all_msg = state.messages + [HumanMessage(content=response)]
        print(f"Human: {response}")

    # Clear the input after processing
    return OverallState(
        messages=all_msg,
        cv=state.cv,
        score=state.score,
        num_questions=state.num_questions,
        should_end=state.should_end,
        current_human_input=None # Clear current input
    )

def questions_condition(state: OverallState):
    print(f"DEBUG: questions: {state.num_questions}")
    print(f"Chatbot DEBUG: should_end: {state.should_end}")
    if state.num_questions >= 3 or state.should_end == True:
        return "chatbot_ender"
    else:
        return "chatbot"

def chatbot_ender(state: OverallState):
    ending_prompt = ChatPromptTemplate.from_template(ender_prompt)
    ender_chain = ending_prompt | model
    response = ender_chain.invoke({"cv": state.cv, "past_messages": state.messages, "score": state.score})
    print(f"Ending: {response.content}")
    all_msg = state.messages + [AIMessage(content=response.content)]

    return OverallState(messages = all_msg, cv=state.cv, score = state.score, num_questions=state.num_questions)
    
builder = StateGraph(OverallState)
builder.add_node("cv_reader", cv_reader)
builder.add_node("chatbot", chatbot)
builder.add_node("human_response", human_response)
builder.add_node("chatbot_ender", chatbot_ender)


builder.add_edge(START, "cv_reader")
builder.add_edge("cv_reader", "chatbot")
builder.add_edge("chatbot", "human_response")
builder.add_conditional_edges("human_response", questions_condition, {"chatbot":"chatbot","chatbot_ender":"chatbot_ender" })
builder.add_edge( "chatbot_ender", END)
# builder.add_edge("chatbot", END)
graph = builder.compile()