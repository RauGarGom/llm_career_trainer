from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import model as md

app = FastAPI()

# Mount the static files directory
app.mount("/assets", StaticFiles(directory="./templates/assets"), name="assets")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="./templates/html")

# Startup variables
current_question = None
chroma_db = md.chroma_read()


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

@app.get('/question-explanation', response_class=HTMLResponse)
async def explain_question(request: Request):
    global current_question
    explanation = md.question_explanation(current_question)
    return templates.TemplateResponse("evaluation.html",
                                       {"request": request, "explanation": explanation})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
