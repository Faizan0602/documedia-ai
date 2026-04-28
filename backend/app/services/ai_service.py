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
MAX_SUMMARY_LINES = 90
MAX_CHAT_CONTEXT_CHARS = 2600
MAX_CHAT_LINES = 24

CHAT_INTENTS = {
    "projects": {
        "project",
        "projects",
        "application",
        "applications",
        "app",
        "apps",
        "system",
        "systems",
        "simulator",
        "visualizer",
        "portfolio",
        "developed",
        "built",
        "implemented",
    },
    "skills": {
        "skill",
        "skills",
        "technical",
        "technology",
        "technologies",
        "tool",
        "tools",
        "language",
        "languages",
        "framework",
        "frameworks",
        "python",
        "java",
        "javascript",
        "react",
        "node",
        "sql",
        "mongodb",
    },
    "education": {
        "education",
        "academic",
        "degree",
        "college",
        "university",
        "school",
        "cgpa",
        "gpa",
        "b.tech",
        "bachelor",
        "master",
    },
    "experience": {
        "experience",
        "work",
        "professional",
        "intern",
        "internship",
        "job",
        "role",
        "company",
        "employment",
    },
    "certifications": {
        "certification",
        "certifications",
        "certificate",
        "certificates",
        "course",
        "courses",
    },
    "achievements": {
        "achievement",
        "achievements",
        "award",
        "awards",
        "honor",
        "honors",
    },
}

STRICT_CHAT_TERMS = {
    "projects": {
        "project",
        "projects",
        "application",
        "applications",
        "app",
        "apps",
        "system",
        "systems",
        "simulator",
        "visualizer",
        "portfolio",
        "platform",
        "website",
        "tracker",
        "management",
    },
}

SECTION_TO_INTENT = {
    "technical skills": "skills",
    "skills": "skills",
    "tools": "skills",
    "technologies": "skills",
    "education": "education",
    "academic": "education",
    "academics": "education",
    "academic details": "education",
    "experience": "experience",
    "work experience": "experience",
    "professional experience": "experience",
    "internship": "experience",
    "internships": "experience",
    "employment": "experience",
    "projects": "projects",
    "project": "projects",
    "personal projects": "projects",
    "academic projects": "projects",
    "certifications": "certifications",
    "certification": "certifications",
    "certificates": "certifications",
    "achievements": "achievements",
    "awards": "achievements",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "give",
    "in",
    "include",
    "including",
    "is",
    "it",
    "list",
    "me",
    "mentioned",
    "of",
    "on",
    "or",
    "show",
    "tell",
    "that",
    "the",
    "this",
    "to",
    "was",
    "were",
    "what",
    "which",
    "with",
}


class AIService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if api_key and genai:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None

    def generate_summary(self, doc_id: str) -> str:
        context = self._build_summary_context(doc_id)

        if not context:
            return "No relevant information found in this document."

        prompt = self._summary_prompt(context)
        return self._generate(prompt, self._fallback_summary(context))

    def ask_question(self, doc_id: str, question: str) -> str:
        clean_question = self._clean_line(question)
        if not clean_question:
            return "Please enter a question."

        intent = self._detect_chat_intent(clean_question)

        if self._is_summary_question(clean_question) and not intent:
            context = self._build_summary_context(doc_id)
            if not context:
                return "No relevant information found in this document."

            prompt = self._summary_prompt(context)
            fallback = self._fallback_summary(context)
            return self._generate(prompt, fallback)

        context = self._build_chat_context(doc_id, clean_question, intent)
        if not context:
            return "* Not found in the document."

        prompt = self._chat_prompt(clean_question, context, intent)
        fallback = self._fallback_answer(context)
        return self._generate(prompt, fallback)

    def _generate(self, prompt: str, fallback_text: str) -> str:
        if not self.model:
            return fallback_text

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.8,
                    "max_output_tokens": 700,
                },
            )
            text = getattr(response, "text", "") or ""
            text = text.strip()
            return text if text else fallback_text
        except Exception as e:
            print("Gemini error:", str(e))
            return fallback_text

    def _build_summary_context(self, doc_id: str) -> str:
        return self._build_context(
            doc_id=doc_id,
            query=SUMMARY_QUERY,
            top_k=10,
            max_chars=MAX_SUMMARY_CONTEXT_CHARS,
            max_lines=MAX_SUMMARY_LINES,
        )

    def _build_context(
        self,
        doc_id: str,
        query: str,
        top_k: int,
        max_chars: int,
        max_lines: int,
    ) -> str:
        chunks = vector_service.search(doc_id, query, top_k=top_k)
        unique_chunks = self._unique_chunks(chunks)
        meaningful_lines = self._meaningful_unique_lines(unique_chunks)
        return self._join_limited_lines(meaningful_lines, max_chars, max_lines)

    def _build_chat_context(self, doc_id: str, question: str, intent: str) -> str:
        search_query = question
        if intent:
            search_query = f"{question} {' '.join(sorted(CHAT_INTENTS[intent]))}"

        chunks = vector_service.search(doc_id, search_query, top_k=4)
        unique_chunks = self._unique_chunks(chunks)
        lines = self._relevant_chat_lines(unique_chunks, question, intent)

        if not lines and intent:
            fallback_query = " ".join(sorted(CHAT_INTENTS[intent]))
            chunks = vector_service.search(doc_id, fallback_query, top_k=4)
            unique_chunks = self._unique_chunks(chunks)
            lines = self._relevant_chat_lines(unique_chunks, question, intent)

        return self._join_limited_lines(lines, MAX_CHAT_CONTEXT_CHARS, MAX_CHAT_LINES)

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
        seen: set[str] = set()

        for chunk in chunks:
            for raw_line in self._split_lines(chunk):
                self._append_unique_line(lines, seen, raw_line)

        return lines

    def _relevant_chat_lines(
        self,
        chunks: Iterable[str],
        question: str,
        intent: str,
    ) -> list[str]:
        lines: list[str] = []
        seen: set[str] = set()
        query_tokens = self._query_tokens(question)

        for chunk in chunks:
            sections = self._split_sections(chunk)

            if intent:
                matched_section = False
                for section_intent, section_text in sections:
                    if section_intent != intent:
                        continue

                    matched_section = True
                    for raw_line in self._split_lines(section_text):
                        self._append_unique_line(lines, seen, raw_line)

                if matched_section:
                    continue

            for section_intent, section_text in sections:
                if intent and section_intent and section_intent != intent:
                    continue

                for raw_line in self._split_lines(section_text):
                    line = self._clean_line(raw_line)
                    if not self._is_relevant_chat_line(line, query_tokens, intent):
                        continue

                    self._append_unique_line(lines, seen, line)

        return lines

    def _split_sections(self, text: str) -> list[tuple[str, str]]:
        text = self._normalize_text(text)
        heading_names = sorted(SECTION_TO_INTENT.keys(), key=len, reverse=True)
        heading_pattern = "|".join(re.escape(name) for name in heading_names)
        marked = re.sub(
            rf"\b({heading_pattern})\b\s*:?",
            r"\n[[SECTION:\1]]\n",
            text,
            flags=re.IGNORECASE,
        )

        sections: list[tuple[str, str]] = []
        current_intent = ""
        current_lines: list[str] = []

        for part in re.split(r"\n+", marked):
            part = part.strip()
            if not part:
                continue

            marker = re.fullmatch(r"\[\[SECTION:(.+?)\]\]", part, flags=re.IGNORECASE)
            if marker:
                if current_lines:
                    sections.append((current_intent, "\n".join(current_lines)))
                    current_lines = []

                heading = marker.group(1).lower().strip()
                current_intent = SECTION_TO_INTENT.get(heading, "")
                continue

            current_lines.append(part)

        if current_lines:
            sections.append((current_intent, "\n".join(current_lines)))

        return sections or [("", text)]

    def _split_lines(self, text: str) -> list[str]:
        text = self._normalize_text(text)
        text = re.sub(
            r"\b(Skills|Technical Skills|Education|Academic Details|Experience|"
            r"Work Experience|Professional Experience|Internship|Internships|"
            r"Projects|Project|Personal Projects|Academic Projects|"
            r"Certifications|Achievements|Responsibilities)\b\s*:?",
            r"\n\1:\n",
            text,
            flags=re.IGNORECASE,
        )

        candidates: list[str] = []
        for part in re.split(r"\n+|[;|]", text):
            part = part.strip()
            if not part:
                continue

            if len(part) > 260:
                candidates.extend(
                    item.strip()
                    for item in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", part)
                    if item.strip()
                )
            else:
                candidates.append(part)

        return candidates

    def _append_unique_line(self, lines: list[str], seen: set[str], raw_line: str) -> None:
        line = self._clean_line(raw_line)
        if not self._is_meaningful_line(line):
            return

        fingerprint = self._fingerprint(line)
        if not fingerprint or fingerprint in seen:
            return

        if self._overlaps_existing_line(line, lines):
            return

        seen.add(fingerprint)
        lines.append(line)

    def _is_relevant_chat_line(
        self,
        line: str,
        query_tokens: set[str],
        intent: str,
    ) -> bool:
        if not self._is_meaningful_line(line):
            return False

        lowered = line.lower().rstrip(":")
        if lowered in SECTION_TO_INTENT:
            return False

        line_tokens = self._query_tokens(line)

        if intent:
            intent_tokens = STRICT_CHAT_TERMS.get(intent, CHAT_INTENTS[intent])
            if line_tokens.intersection(intent_tokens):
                return True

            if query_tokens and line_tokens.intersection(query_tokens):
                return True

            return False

        return bool(query_tokens and line_tokens.intersection(query_tokens))

    def _detect_chat_intent(self, question: str) -> str:
        tokens = self._query_tokens(question)

        for intent in (
            "projects",
            "skills",
            "education",
            "experience",
            "certifications",
            "achievements",
        ):
            if tokens.intersection(CHAT_INTENTS[intent]):
                return intent

        return ""

    def _query_tokens(self, text: str) -> set[str]:
        tokens = set(re.findall(r"[a-z0-9+#.]+", text.lower()))
        tokens = {
            token
            for token in tokens
            if token not in STOPWORDS and (len(token) > 1 or token in {"c", "r"})
        }

        expanded = set(tokens)
        for token in tokens:
            singular = token[:-1] if token.endswith("s") else token
            plural = f"{token}s"

            for key in {token, singular, plural}:
                expanded.update(CHAT_INTENTS.get(key, set()))

        return expanded

    def _join_limited_lines(
        self,
        lines: Iterable[str],
        max_chars: int,
        max_lines: int,
    ) -> str:
        selected_lines: list[str] = []
        total_chars = 0

        for line in lines:
            next_size = len(line) + 1
            if selected_lines and total_chars + next_size > max_chars:
                break

            selected_lines.append(line)
            total_chars += next_size

            if len(selected_lines) >= max_lines:
                break

        return "\n".join(selected_lines).strip()

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

        return signal_count >= 2

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
        summary_terms = {"summary", "summarize", "overview"}
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

    def _chat_prompt(self, question: str, context: str, intent: str) -> str:
        topic = intent.title() if intent else "Question"

        return f"""
You are a document Q&A assistant.

Answer only the Question using only the Relevant Context.

Requested topic: {topic}

Rules:
- Include only facts directly related to the Requested topic.
- Exclude skills, education, experience, certifications, achievements, and other sections unless the Question asks for them.
- Do not copy long phrases or full sentences from the Context.
- Do not repeat facts.
- Do not include raw context.
- Use concise "*" bullet points only.
- If the answer is not in the Relevant Context, return exactly "* Not found in the document."
- Return only the answer.

Question:
{question}

Relevant Context:
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
            if lowered in SECTION_TO_INTENT:
                current_section = ""
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
        tokens = self._query_tokens(line)

        if tokens.intersection(CHAT_INTENTS["education"]):
            return "Education"
        if tokens.intersection(CHAT_INTENTS["experience"]):
            return "Experience"
        if tokens.intersection(CHAT_INTENTS["skills"]):
            return "Skills"

        return ""

    def _trim_bullet(self, text: str, max_chars: int = 170) -> str:
        text = self._clean_line(text).rstrip(".")
        if len(text) <= max_chars:
            return text

        trimmed = text[:max_chars].rsplit(" ", 1)[0].strip()
        return f"{trimmed}..."


ai_service = AIService()
