
import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException
from pypdf import PdfReader
from docx import Document
from datetime import datetime, timezone
import google.generativeai as genai

from app.services.vector_service import vector_service
from app.core.database import db


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class FileService:
    @staticmethod
    async def save_upload_file(file: UploadFile) -> dict:
        ext = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename).replace("\\", "/")

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            file.file.close()

        content_type = file.content_type or ""

        if ext == ".pdf":
            file_category = "pdf"
        elif ext == ".txt":
            file_category = "text"
        elif ext == ".docx":
            file_category = "docx"
        elif content_type.startswith("audio/") or ext in [".mp3", ".wav", ".m4a"]:
            file_category = "audio"
        elif content_type.startswith("video/") or ext in [".mp4", ".avi", ".mov"]:
            file_category = "video"
        else:
            file_category = "other"

        doc_id = unique_filename

        # -------------------------------
        # MEDIA FILES
        # -------------------------------
        if file_category in ["audio", "video"]:
            file_doc = {
                "doc_id": doc_id,
                "original_filename": file.filename,
                "file_path": file_path,
                "file_type": file_category,
                "preview": "",
                "upload_timestamp": datetime.now(timezone.utc)
            }

            try:
                await db.db["files"].insert_one(file_doc)
            except Exception as e:
                print("DB INSERT ERROR:", str(e))

            return {
                "doc_id": doc_id,
                "filename": file.filename,
                "message": "Media uploaded successfully"
            }

        # -------------------------------
        # TEXT EXTRACTION
        # -------------------------------
        try:
            if file_category == "pdf":
                full_text = FileService.extract_pdf_text(file_path)
            elif file_category == "text":
                full_text = FileService.extract_txt_text(file_path)
            elif file_category == "docx":
                full_text = FileService.extract_docx_text(file_path)
            else:
                full_text = ""
        except Exception as e:
            print("TEXT EXTRACTION ERROR:", str(e))
            full_text = ""

        full_text = (full_text or "").strip()

        # Vector indexing (safe)
        try:
            vector_service.add_document(doc_id, full_text)
        except Exception as e:
            print("VECTOR ERROR:", str(e))

        file_doc = {
            "doc_id": doc_id,
            "original_filename": file.filename,
            "file_path": file_path,
            "file_type": file_category,
            "preview": full_text[:500],
            "upload_timestamp": datetime.now(timezone.utc)
        }

        try:
            await db.db["files"].insert_one(file_doc)
        except Exception as e:
            print("DB INSERT ERROR:", str(e))

        return {
            "doc_id": doc_id,
            "filename": file.filename,
            "message": "File uploaded successfully"
        }

    # -------------------------------
    # LLM Chat — Gemini
    # -------------------------------
    @staticmethod
    def generate_answer(doc_id: str, query: str) -> str:
        context_chunks = vector_service.search(doc_id, query, top_k=3)

        if not context_chunks:
            return "No relevant information found in this document."

        context = "\n\n".join(context_chunks)

        prompt = f"""Answer strictly based on the provided context below.

Context:
{context}

Question:
{query}

Answer clearly and concisely."""

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            return response.text or "No answer generated."

        except Exception as e:
            print("Gemini error:", str(e))
            return "Based on document:\n\n" + context

    # -------------------------------
    # Extraction Methods
    # -------------------------------
    @staticmethod
    def extract_pdf_text(file_path: str) -> str:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text

    @staticmethod
    def extract_txt_text(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def extract_docx_text(file_path: str) -> str:
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

