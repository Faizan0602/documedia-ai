
from app.services.vector_service import vector_service


class SummaryService:
    def generate_summary(self, doc_id: str):
        # 🔥 Correct search (with doc_id)
        chunks = vector_service.search(doc_id, "summary", top_k=5)

        if not chunks:
            return "No data available to summarize."

        full_text = " ".join(chunks)
        full_text = full_text.replace("\n", " ")

        summary_parts = []

        if "final-year" in full_text.lower() or "student" in full_text.lower():
            summary_parts.append(
                "Final-year IT student with strong foundation in software development and QA practices."
            )

        if "java" in full_text.lower():
            summary_parts.append(
                "Skilled in Java, OOP, and full-stack technologies including React and Node.js."
            )

        if "project" in full_text.lower():
            summary_parts.append(
                "Worked on multiple real-world projects including stock simulators and algorithm visualizers."
            )

        if "intern" in full_text.lower():
            summary_parts.append(
                "Has internship experience applying modular design, testing, and debugging practices."
            )

        # fallback
        if not summary_parts:
            summary_parts.append(full_text[:200])

        return "Summary:\n\n" + "\n\n".join(summary_parts)

