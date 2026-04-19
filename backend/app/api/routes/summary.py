from fastapi import APIRouter
from pydantic import BaseModel
from app.services.vector_service import vector_service

router = APIRouter()

class SummaryRequest(BaseModel):
    doc_id: str

@router.post("/")
async def get_summary(request: SummaryRequest):
    # ✅ FIX: Only get chunks for the specific document
    doc_chunks = vector_service.get_chunks(request.doc_id)

    if not doc_chunks:
        return {
            "status": "error",
            "summary": "Document not found or no text available."
        }

    text = " ".join([chunk.text for chunk in doc_chunks]).lower()
    summary_parts = []

    # Extract key sections
    if "skills" in text:
        for chunk in doc_chunks:
            if "skills" in chunk.text.lower():
                summary_parts.append("Skills:\n" + chunk.text.strip())
                break

    if "education" in text:
        for chunk in doc_chunks:
            if "education" in chunk.text.lower():
                summary_parts.append("Education:\n" + chunk.text.strip())
                break

    if "experience" in text:
        for chunk in doc_chunks:
            if "experience" in chunk.text.lower():
                summary_parts.append("Experience:\n" + chunk.text.strip())
                break

    # fallback
    if not summary_parts:
        summary_parts.append(doc_chunks[0].text)

    return {
        "status": "success",
        "summary": "\n\n".join(summary_parts)
    }