import os
import google.generativeai as genai
from app.services.vector_service import vector_service


class AIService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash")  # ✅ valid model name
        else:
            self.model = None

    def generate_summary(self, doc_id: str) -> str:
        if not self.model:
            return "AI Service not configured."

        chunks = vector_service.get_chunks(doc_id)
        if not chunks:
            return "No document found."

        text = "\n\n".join(c.text for c in chunks)[:10000]

        try:
            response = self.model.generate_content(
                f"Summarize the following content concisely:\n\n{text}"
            )
            return response.text or "No summary generated."
        except Exception as e:
            print(f"Summary failed: {e}")
            return "Error generating summary."

    def ask_question(self, doc_id: str, question: str) -> str:
        if not self.model:
            return "AI Service not configured."

        # 🔥 GET RELEVANT CHUNKS
        relevant_chunks = vector_service.search(doc_id, question)

        if not relevant_chunks:
            return "No relevant answer found in the document."

        # 🔥 ONLY PASS RELEVANT CONTEXT
        context = "\n\n".join(relevant_chunks)

        prompt = f"""Answer the question based ONLY on the context below.

Context:
{context}

Question:
{question}

Answer clearly and concisely."""

        try:
            response = self.model.generate_content(prompt)
            return response.text or "No answer generated."
        except Exception as e:
            print(f"Chat failed: {e}")
            return "Error generating answer."


# Singleton instance
ai_service = AIService()