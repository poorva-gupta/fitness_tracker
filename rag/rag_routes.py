from fastapi import APIRouter
from pydantic import BaseModel
from rag.rag_pipeline import generate_answer

router=APIRouter(
    prefix="/fitness-ai",
    tags=["fitness AI"]
)

class QuestionRequest(BaseModel):
    question:str

class AnswerResponse(BaseModel):
    question:str
    answer:str

@router.post("/ask",response_model=AnswerResponse)
def ask_fitness_question(request: QuestionRequest):
    answer=generate_answer(request.question)
    return{
        "question":request.question,
        "answer":answer
    }