
def ask_question(self, doc_id: str, question: str) -> str:
    if not self.model:
        return "AI Service not configured."

    relevant_chunks = vector_service.search(doc_id, question)

    if not relevant_chunks:
        return "No relevant information found in the document."

    #  SAFE context building
    context = "\n\n".join(
        chunk if isinstance(chunk, str) else str(chunk)
        for chunk in relevant_chunks
    )

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

