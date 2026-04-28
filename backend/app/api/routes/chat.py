from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.ai_service import ai_service


router = APIRouter()


class ChatRequest(BaseModel):
    doc_id: str
    question: str


@router.post("/")
async def chat(request: ChatRequest):
    try:
        answer = ai_service.ask_question(request.doc_id, request.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
