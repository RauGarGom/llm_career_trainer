from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import model as md

app = FastAPI()

# Mount the static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get('/generate-question', response_class=HTMLResponse)
async def generate_question(request: Request):
    question = md.generate_question()
    return templates.TemplateResponse("question.html", {"request": request, "question": question})

@app.post('/evaluate-answer', response_class=HTMLResponse)
async def evaluate_answer(request: Request, answer: str = Form(...)):
    evaluation = md.evaluate_answer(answer)
    return templates.TemplateResponse("evaluation.html", {"request": request, "evaluation": evaluation})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
