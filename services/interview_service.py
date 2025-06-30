from schemas.interview import OverallState
from prompts.prompts import chatbot_prompt, scoring_prompt,ender_prompt,should_end_prompt
from models.models import general_model

from pdfminer.high_level import extract_text

from langchain_core.prompts import ChatPromptTemplate



def parse_cv(file_path: str) -> str:
    # Use pdfminer or similar to extract text
    print("Reading your CV...")
    text_content = extract_text(file_path)
    return{"cv":text_content}

def generate_question(state: OverallState) -> str:
    # Use LLM to generate question
    print("Preparing an answer")
    chat_prompt = ChatPromptTemplate.from_template(chatbot_prompt)
    chat_chain = chat_prompt | general_model
    chat_response = chat_chain.invoke({"cv": state.cv, "past_messages": state.messages})
    print(f"Chatbot: {chat_response.content}")
    return chat_response.content

def score_answer(state: OverallState) -> int:
    # Use LLM to score answer
    score_prompt = ChatPromptTemplate.from_template(scoring_prompt)
    score_chain = score_prompt | general_model
    score_response = score_chain.invoke({"cv": state.cv, "past_messages": state.messages})
    print(f"Score: {score_response.content}")
    return int(score_response.content)

def should_end_interview(state: OverallState) -> bool:
    # Use LLM to decide if interview should end
    should_end_chain = ChatPromptTemplate.from_template(should_end_prompt) | model
    should_end_response = should_end_chain.invoke({"past_messages": state.messages})
    should_end = should_end_response.content.strip().lower() == "yes"
    return should_end