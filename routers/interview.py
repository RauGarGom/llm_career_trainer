# routers/interview.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from schemas.interview import OverallState
from services.interview_service import parse_cv, generate_question, score_answer, should_end_interview
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage, AnyMessage



import os
import uuid

router = APIRouter()

@router.post("/upload-cv")
async def upload_cv(file: UploadFile = File()):
    # handle CV upload
    temp_filename = f"temp_{uuid.uuid4()}.pdf"
    temp_filepath = os.path.join("/tmp", temp_filename)
    with open(temp_filepath, "wb") as f:
        f.write(await file.read())

    try:
        cv_data = parse_cv(temp_filepath)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CV: {e}")
    
    os.remove(temp_filepath)

    state = OverallState(
        messages=[],
        cv=cv_data["cv"],
        score=None,
        num_questions=0,
        should_end=False
    )
    return state

@router.post("/next-question")
async def next_question(state: OverallState):
    question = generate_question(state)
    all_msg = state.messages + [AIMessage(content=question)]


    state = OverallState(
        messages=all_msg,
        cv=state.cv,
        score=state.score,
        num_questions=state.num_questions+1,
        should_end=state.should_end
    )
    return state

@router.post("/submit-answer")
async def submit_answer():
    # handle next question
    pass

@router.post("/end-interview")
async def end_interview():
    # handle next question
    pass