from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from langchain_cohere import CohereEmbeddings
from dotenv import load_dotenv
import uvicorn
import os
import model as md
import asyncio
from pydantic import BaseModel, Field
from typing import Any, Optional
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage
from chatbot import graph, OverallState
from pdfminer.high_level import extract_text
import io


app = FastAPI()

# Mount the static files directory
app.mount("/assets", StaticFiles(directory="./templates/assets"), name="assets")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="./templates/html")

#Pydantic classes:


# Global variable to store chatbot state (for simplicity, use session for production)
chatbot_state: Optional[OverallState] = None

# Startup variables
load_dotenv(override=True)
cohere_api_key = os.getenv("COHERE_API_KEY")
pinecone_api_key = os.getenv("PINECONE_API_KEY")

if not cohere_api_key:
    print("Warning: COHERE_API_KEY not found in environment variables")
if not pinecone_api_key:
    print("Warning: PINECONE_API_KEY not found in environment variables")

current_question = None
print("Setting up embeddings model...")
embeddings = CohereEmbeddings(model="embed-english-light-v3.0")
print("Embeddings model initialized successfully")

print("Setting up endpoints...")
@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get('/generate-question', response_class=HTMLResponse)
async def generate_question(request: Request):
    global current_question
    current_question = md.generate_question()
    return templates.TemplateResponse("question.html", {"request": request, "question": current_question})

@app.post('/evaluate-answer', response_class=HTMLResponse)
async def evaluate_answer(request: Request, answer: str = Form(...)):
    global current_question
    thought,follow_up,grade, prev_answer = md.evaluate_answer_v2(answer,current_question)
    current_question = follow_up
    return templates.TemplateResponse("evaluation.html",
                                       {"request": request, "thought": thought, "follow_up": follow_up, "grade":grade, "prev_answer": prev_answer})

@app.post('/question-explanation', response_class=HTMLResponse)
async def explain_question(request: Request):
    global current_question
    return templates.TemplateResponse("explanation.html",
                                   {"request": request, "question": current_question})

@app.get('/stream-explanation')
async def stream_explanation():
    global current_question
    async def generate():
        for chunk in md.question_explanation_streaming(embeddings,current_question):
            yield f"data: {chunk}\n\n"
            await asyncio.sleep(0.1)  # Small delay to prevent overwhelming the client
    
    return StreamingResponse(generate(), media_type="text/event-stream")

# Commenting out the old chatbot endpoint as we are creating a new flow
# @app.post('/chatbot')
# async def chatbot_api(input:OverallState): # Renamed to avoid conflict if we uncomment later
#     # This was for direct API interaction, the new flow is form-based
#     response = await graph.ainvoke(OverallState(messages=[],cv="",score=5, num_questions=0))
#     return response["messages"][-1].content

@app.get("/chatbot-cv", response_class=HTMLResponse)
async def chatbot_cv_upload_page(request: Request):
    return templates.TemplateResponse("chatbot_cv_upload.html", {"request": request})

@app.post("/chatbot-start")
async def chatbot_start(request: Request, cv_file: UploadFile = File(...)):
    global chatbot_state
    try:
        cv_content_bytes = await cv_file.read()
        cv_text = extract_text(io.BytesIO(cv_content_bytes))

        # Initialize state
        initial_messages = [SystemMessage(content="Chat started. CV has been uploaded.")]
        chatbot_state = OverallState(
            messages=initial_messages,
            cv=cv_text,
            score=0, # Initial score
            num_questions=0,
            should_end=False,
            current_human_input=None
        )

        # Run the graph until the first AI message (after cv_reader and first chatbot call)
        # The initial state for ainvoke should be what cv_reader expects or what the graph start node expects.
        # Our cv_reader now expects cv to be in the state.

        # Initial state for the graph invocation
        initial_graph_input = {
            "messages": chatbot_state.messages, # System message
            "cv": chatbot_state.cv,
            "score": chatbot_state.score,
            "num_questions": chatbot_state.num_questions,
            "should_end": chatbot_state.should_end,
            "current_human_input": None # No human input yet
        }

        # This will run cv_reader, then chatbot node.
        # The graph should pause before human_response.
        # The result 'current_graph_output_state_dict' will be the state after the 'chatbot' node.
        current_graph_output_state_dict = await graph.ainvoke(initial_graph_input)

        # Update our global chatbot_state with the new state from the graph
        # Ensure all fields are updated, including those not explicitly returned if graph modifies them implicitly.
        chatbot_state = OverallState(**current_graph_output_state_dict)

        ai_first_message = ""
        if chatbot_state.messages and isinstance(chatbot_state.messages[-1], AIMessage):
            ai_first_message = chatbot_state.messages[-1].content
        else:
            # This indicates something unexpected in the graph's output or structure
            print("Warning: Expected last message to be AIMessage after initial graph invocation.")
            # Provide a fallback message and add it to the state for consistency
            ai_first_message = "I've processed your CV. Please ask your first question or tell me what you'd like to discuss."
            if chatbot_state is not None: # chatbot_state should be defined here
                 chatbot_state.messages.append(AIMessage(content=ai_first_message))
            else: # Should not happen if logic is correct
                 print("ERROR: chatbot_state is None when trying to append fallback AIMessage")


        return templates.TemplateResponse("chatbot_interface.html", {
            "request": request,
            "chat_history": chatbot_state.messages if chatbot_state else [],
            "ai_message": ai_first_message
        })

    except Exception as e:
        print(f"Error during CV processing or initial chatbot call: {e}")
        # Redirect to CV upload with an error message, or render an error page
        return templates.TemplateResponse("chatbot_cv_upload.html", {"request": request, "error": str(e)})

@app.post("/chatbot-respond")
async def chatbot_respond(request: Request, user_input: str = Form(...)):
    global chatbot_state

    if chatbot_state is None:
        # This shouldn't happen if the user followed the flow
        return RedirectResponse(url="/chatbot-cv", status_code=303)

    # Update state with human input
    chatbot_state.current_human_input = user_input
    # The human_response node in chatbot.py will add this to messages and clear current_human_input

    try:
        # Invoke the graph. It will run human_response, then questions_condition,
        # then either chatbot (for another question) or chatbot_ender.
        current_graph_input = chatbot_state.dict()

        # The graph's human_response node will take current_human_input, add it as HumanMessage.
        # Then it proceeds to chatbot or chatbot_ender.
        output_state_dict = await graph.ainvoke(current_graph_input)
        chatbot_state = OverallState(**output_state_dict)

        ai_response_content = ""
        if chatbot_state.messages and isinstance(chatbot_state.messages[-1], AIMessage):
            ai_response_content = chatbot_state.messages[-1].content
        else:
            print("Warning: No new AIMessage found after graph invocation in chatbot_respond.")
            # This might mean the graph ended or an issue occurred.
            # If should_end is true, the last message might be the ender message.
            if chatbot_state.should_end:
                ai_response_content = "The chat session has ended." # Or pull from last message if available
            else:
                ai_response_content = "An unexpected error occurred, or no AI response was generated."


        if chatbot_state.should_end:
            # If the conversation should end, we can display the final message
            # and perhaps redirect to a summary page or clear the state.
            # For now, just render the interface, it might show the final AI message.
             return templates.TemplateResponse("chatbot_interface.html", {
                "request": request,
                "chat_history": chatbot_state.messages,
                "ai_message": ai_response_content,
                "conversation_ended": True
            })

        return templates.TemplateResponse("chatbot_interface.html", {
            "request": request,
            "chat_history": chatbot_state.messages,
            "ai_message": ai_response_content
        })

    except Exception as e:
        print(f"Error during chatbot response generation: {e}")
        return templates.TemplateResponse("chatbot_interface.html", {
            "request": request,
            "chat_history": chatbot_state.messages if chatbot_state else [],
            "ai_message": "Sorry, an error occurred while processing your response.",
            "error": str(e)
        })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
