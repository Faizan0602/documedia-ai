from fastapi import APIRouter
from pydantic import BaseModel

from app.services.ai_service import ai_service


router = APIRouter()


class SummaryRequest(BaseModel):
    doc_id: str


@router.post("/")
async def get_summary(request: SummaryRequest):
    try:
        summary = ai_service.generate_summary(request.doc_id)

        return {
            "status": "success",
            "summary": summary,
        }
    except Exception as e:
        print("Summary error:", str(e))
        return {
            "status": "error",
            "summary": "Error generating summary",
        }
