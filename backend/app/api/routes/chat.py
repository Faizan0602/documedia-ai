from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.file_service import FileService

router = APIRouter()

class ChatRequest(BaseModel):
    doc_id: str
    question: str

@router.post("/")
async def chat(request: ChatRequest):
    try:
        # ✅ FIX: Pass doc_id to generate_answer
        answer = FileService.generate_answer(request.doc_id, request.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))