from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from langchain_cohere import CohereEmbeddings
from dotenv import load_dotenv
import uvicorn
import os
import model as md
import asyncio

app = FastAPI()

# Mount the static files directory
app.mount("/assets", StaticFiles(directory="./templates/assets"), name="assets")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="./templates/html")

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
