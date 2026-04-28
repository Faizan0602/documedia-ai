import os
import re
from difflib import SequenceMatcher
from typing import Iterable

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from app.services.vector_service import vector_service


SUMMARY_QUERY = (
    "skills technical skills programming languages frameworks tools education "
    "degree college university experience internship work projects achievements"
)
MAX_SUMMARY_CONTEXT_CHARS = 7000
MAX_CHAT_CONTEXT_CHARS = 5000
MAX_CONTEXT_LINES = 90


class AIService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if api_key and genai:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None

    def generate_summary(self, doc_id: str) -> str:
        context = self._build_context(
            doc_id=doc_id,
            query=SUMMARY_QUERY,
            top_k=10,
            max_chars=MAX_SUMMARY_CONTEXT_CHARS,
        )

        if not context:
            return "No relevant information found in this document."

        prompt = self._summary_prompt(context)
        return self._generate(prompt, self._fallback_summary(context))

    def ask_question(self, doc_id: str, question: str) -> str:
        clean_question = self._clean_line(question)
        if not clean_question:
            return "Please enter a question."

        context = self._build_context(
            doc_id=doc_id,
            query=clean_question,
            top_k=8,
            max_chars=MAX_CHAT_CONTEXT_CHARS,
        )

        if not context:
            return "No relevant information found in this document."

        if self._is_summary_question(clean_question):
            prompt = self._summary_prompt(context)
            fallback = self._fallback_summary(context)
        else:
            prompt = self._chat_prompt(clean_question, context)
            fallback = self._fallback_answer(context)

        return self._generate(prompt, fallback)

    def _generate(self, prompt: str, fallback_context: str) -> str:
        if not self.model:
            return fallback_context

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.8,
                    "max_output_tokens": 900,
                },
            )
            text = getattr(response, "text", "") or ""
            text = text.strip()
            return text if text else fallback_context
        except Exception as e:
            print("Gemini error:", str(e))
            return fallback_context

    def _build_context(
        self,
        doc_id: str,
        query: str,
        top_k: int,
        max_chars: int,
    ) -> str:
        chunks = vector_service.search(doc_id, query, top_k=top_k)

        if not chunks and query != SUMMARY_QUERY:
            chunks = vector_service.search(doc_id, SUMMARY_QUERY, top_k=top_k)

        unique_chunks = self._unique_chunks(chunks)
        meaningful_lines = self._meaningful_unique_lines(unique_chunks)

        selected_lines: list[str] = []
        total_chars = 0

        for line in meaningful_lines:
            next_size = len(line) + 1
            if selected_lines and total_chars + next_size > max_chars:
                break

            selected_lines.append(line)
            total_chars += next_size

            if len(selected_lines) >= MAX_CONTEXT_LINES:
                break

        return "\n".join(selected_lines).strip()

    def _unique_chunks(self, chunks: Iterable[str]) -> list[str]:
        selected: list[str] = []
        fingerprints: set[str] = set()

        for chunk in chunks:
            text = self._normalize_text(chunk)
            if not text:
                continue

            fingerprint = self._fingerprint(text)
            if not fingerprint or fingerprint in fingerprints:
                continue

            if any(self._is_near_duplicate(text, existing) for existing in selected):
                continue

            fingerprints.add(fingerprint)
            selected.append(text)

        return selected

    def _meaningful_unique_lines(self, chunks: Iterable[str]) -> list[str]:
        lines: list[str] = []
        fingerprints: set[str] = set()

        for chunk in chunks:
            for raw_line in self._split_lines(chunk):
                line = self._clean_line(raw_line)
                if not self._is_meaningful_line(line):
                    continue

                fingerprint = self._fingerprint(line)
                if not fingerprint or fingerprint in fingerprints:
                    continue

                if self._overlaps_existing_line(line, lines):
                    continue

                fingerprints.add(fingerprint)
                lines.append(line)

        return lines

    def _split_lines(self, text: str) -> list[str]:
        text = self._normalize_text(text)
        text = re.sub(
            r"\b(Skills|Technical Skills|Education|Experience|Work Experience|"
            r"Professional Experience|Internship|Internships|Projects|"
            r"Certifications|Achievements|Responsibilities)\b\s*:?",
            r"\n\1:\n",
            text,
            flags=re.IGNORECASE,
        )

        candidates: list[str] = []
        for part in re.split(r"\n+", text):
            part = part.strip()
            if not part:
                continue

            if len(part) > 280:
                candidates.extend(
                    item.strip()
                    for item in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", part)
                    if item.strip()
                )
            else:
                candidates.append(part)

        return candidates

    def _normalize_text(self, text: str) -> str:
        text = str(text or "")
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
        text = re.sub(r"[\f\v]+", " ", text)
        text = re.sub(r"[ ]{2,}", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _clean_line(self, line: str) -> str:
        line = self._normalize_text(line)
        line = re.sub(r"^[\-\*\u2022\u2023\u25e6\u2043\u2219]+\s*", "", line)
        line = re.sub(r"\s+", " ", line)
        return line.strip(" -|")

    def _is_meaningful_line(self, line: str) -> bool:
        if not line:
            return False

        lowered = line.lower().strip()
        signal_count = len(re.findall(r"[a-zA-Z0-9+#.]", line))

        if lowered in {"resume", "curriculum vitae", "cv"}:
            return False

        if re.fullmatch(r"(page\s*)?\d+(\s*(of|/)\s*\d+)?", lowered):
            return False

        if re.fullmatch(r"[\W_]+", lowered):
            return False

        if re.search(r"\b(gmail|yahoo|outlook|hotmail)\.com\b", lowered):
            return False

        if re.search(r"\b(linkedin|github)\.com\b", lowered):
            return False

        if re.search(r"https?://|www\.", lowered):
            return False

        if re.fullmatch(r"[\d\s()+-]{8,}", lowered):
            return False

        if signal_count < 2:
            return False

        return True

    def _fingerprint(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9+#.]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _is_near_duplicate(self, text: str, existing: str) -> bool:
        text_fp = self._fingerprint(text)
        existing_fp = self._fingerprint(existing)

        if not text_fp or not existing_fp:
            return False

        if text_fp in existing_fp or existing_fp in text_fp:
            return True

        shorter = min(len(text_fp), len(existing_fp))
        if shorter < 120:
            return False

        return SequenceMatcher(None, text_fp, existing_fp).ratio() >= 0.88

    def _overlaps_existing_line(self, line: str, existing_lines: list[str]) -> bool:
        line_fp = self._fingerprint(line)

        for existing in existing_lines:
            existing_fp = self._fingerprint(existing)

            shorter = min(len(line_fp), len(existing_fp))

            if shorter >= 30 and (line_fp in existing_fp or existing_fp in line_fp):
                return True

            if shorter >= 60 and SequenceMatcher(None, line_fp, existing_fp).ratio() >= 0.9:
                return True

        return False

    def _is_summary_question(self, question: str) -> bool:
        lowered = question.lower()
        summary_terms = {
            "summary",
            "summarize",
            "profile",
            "overview",
            "resume",
            "skills",
            "education",
            "experience",
        }
        return any(term in lowered for term in summary_terms)

    def _summary_prompt(self, context: str) -> str:
        return f"""
You are a resume summarization assistant.

Use only the Context.

Rules:
- Do not copy long phrases or full sentences from the Context.
- Merge duplicate facts.
- Ignore repeated fragments, page numbers, contact details, headers, and footers.
- Keep every bullet short and specific.
- Use "*" bullets only.
- If a section has no facts, write "* Not found in the document."
- Return only the exact format below.

Skills:
* ...

Education:
* ...

Experience:
* ...

Context:
{context}
""".strip()

    def _chat_prompt(self, question: str, context: str) -> str:
        return f"""
You are a document Q&A assistant.

Use only the Context to answer the Question.

Rules:
- Do not copy long phrases or full sentences from the Context.
- Do not repeat facts.
- Do not include raw context.
- Use concise "*" bullet points.
- If the answer is not in the Context, say "* Not found in the document."
- Return only the answer.

Question:
{question}

Context:
{context}

Answer:
""".strip()

    def _fallback_summary(self, context: str) -> str:
        sections = {
            "Skills": [],
            "Education": [],
            "Experience": [],
        }
        seen = set()
        current_section = ""

        for raw_line in context.splitlines():
            line = self._clean_line(raw_line)
            lowered = line.lower().rstrip(":")

            if "skill" in lowered:
                current_section = "Skills"
                continue
            if "education" in lowered:
                current_section = "Education"
                continue
            if "experience" in lowered or "internship" in lowered:
                current_section = "Experience"
                continue

            section = current_section or self._classify_line(line)
            if not section:
                continue

            fingerprint = f"{section}:{self._fingerprint(line)}"
            if fingerprint in seen:
                continue

            seen.add(fingerprint)
            sections[section].append(self._trim_bullet(line))

        return "\n\n".join(
            f"{section}:\n"
            + "\n".join(f"* {item}" for item in (items[:6] or ["Not found in the document."]))
            for section, items in sections.items()
        )

    def _fallback_answer(self, context: str) -> str:
        bullets = []
        seen = set()

        for raw_line in context.splitlines():
            line = self._trim_bullet(self._clean_line(raw_line))
            fingerprint = self._fingerprint(line)

            if not fingerprint or fingerprint in seen:
                continue

            seen.add(fingerprint)
            bullets.append(line)

            if len(bullets) >= 8:
                break

        if not bullets:
            bullets = ["Not found in the document."]

        return "\n".join(f"* {bullet}" for bullet in bullets)

    def _classify_line(self, line: str) -> str:
        lowered = line.lower()

        skill_terms = {
            "python",
            "java",
            "javascript",
            "typescript",
            "react",
            "node",
            "fastapi",
            "sql",
            "mongodb",
            "api",
            "html",
            "css",
            "git",
            "docker",
            "testing",
        }
        education_terms = {
            "b.tech",
            "bachelor",
            "master",
            "degree",
            "university",
            "college",
            "school",
            "cgpa",
            "gpa",
        }
        experience_terms = {
            "intern",
            "developer",
            "engineer",
            "experience",
            "worked",
            "built",
            "developed",
            "project",
            "implemented",
        }

        if any(term in lowered for term in education_terms):
            return "Education"
        if any(term in lowered for term in experience_terms):
            return "Experience"
        if any(term in lowered for term in skill_terms):
            return "Skills"

        return ""

    def _trim_bullet(self, text: str, max_chars: int = 170) -> str:
        text = self._clean_line(text).rstrip(".")
        if len(text) <= max_chars:
            return text

        trimmed = text[:max_chars].rsplit(" ", 1)[0].strip()
        return f"{trimmed}..."


ai_service = AIService()
