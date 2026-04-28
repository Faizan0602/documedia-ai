import re
from difflib import SequenceMatcher
from typing import Optional


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

QUERY_ALIASES = {
    "project": {
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
    "skill": {
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
    },
    "education": {
        "education",
        "degree",
        "college",
        "university",
        "school",
        "academic",
        "cgpa",
        "gpa",
    },
    "experience": {
        "experience",
        "work",
        "intern",
        "internship",
        "job",
        "role",
        "company",
        "professional",
    },
}


class DocumentChunk:
    def __init__(self, id: str, text: str, tokens: list[str]):
        self.id = id
        self.text = text
        self.tokens = tokens


class VectorService:
    def __init__(self):
        self.chunks: dict[str, list[DocumentChunk]] = {}

    def _normalize_text(self, text: str) -> str:
        text = str(text or "")
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
        text = re.sub(r"[ ]{2,}", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _tokenize(self, text: str) -> list[str]:
        tokens = re.findall(r"[a-z0-9+#.]+", text.lower())
        return [
            token
            for token in tokens
            if token not in STOPWORDS and (len(token) > 1 or token in {"c", "r"})
        ]

    def _expand_query_tokens(self, query: str) -> list[str]:
        tokens = self._tokenize(query)
        expanded = set(tokens)

        for token in tokens:
            singular = token[:-1] if token.endswith("s") else token
            plural = f"{token}s"

            for key in {token, singular, plural}:
                expanded.update(QUERY_ALIASES.get(key, set()))

        return list(expanded)

    def _chunk_text(self, text: str, size: int = 120, overlap: int = 12) -> list[str]:
        lines = [
            re.sub(r"\s+", " ", line).strip()
            for line in self._normalize_text(text).splitlines()
            if line.strip()
        ]

        if not lines:
            words = self._normalize_text(text).split()
            return [
                " ".join(words[index:index + size])
                for index in range(0, len(words), max(size - overlap, 1))
                if words[index:index + size]
            ]

        chunks = []
        current_lines = []
        current_words = []

        for line in lines:
            words = line.split()

            if current_lines and len(current_words) + len(words) > size:
                chunks.append("\n".join(current_lines))
                overlap_words = current_words[-overlap:] if overlap else []
                current_lines = [" ".join(overlap_words)] if overlap_words else []
                current_words = overlap_words[:]

            current_lines.append(line)
            current_words.extend(words)

        if current_lines:
            chunks.append("\n".join(current_lines))

        return [chunk for chunk in chunks if chunk.strip()]

    def _fingerprint(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9+#.]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _is_duplicate_chunk(self, text: str, existing: list[str]) -> bool:
        text_fp = self._fingerprint(text)

        for item in existing:
            item_fp = self._fingerprint(item)
            shorter = min(len(text_fp), len(item_fp))

            if shorter >= 40 and (text_fp in item_fp or item_fp in text_fp):
                return True

            if shorter >= 90 and SequenceMatcher(None, text_fp, item_fp).ratio() >= 0.9:
                return True

        return False

    def _score_chunk(self, chunk: DocumentChunk, query_tokens: list[str]) -> float:
        if not query_tokens:
            return 0.0

        chunk_text = chunk.text.lower()
        chunk_tokens = set(chunk.tokens)
        query_set = set(query_tokens)
        exact_matches = chunk_tokens.intersection(query_set)

        score = len(exact_matches) * 4.0

        for token in query_set:
            if len(token) >= 4 and re.search(rf"\b{re.escape(token)}\b", chunk_text):
                score += 2.0

        important_tokens = [token for token in query_set if len(token) >= 5]
        for query_token in important_tokens:
            if query_token in chunk_tokens:
                continue

            best_match = 0.0
            for chunk_token in chunk_tokens:
                if abs(len(query_token) - len(chunk_token)) > 3:
                    continue

                similarity = SequenceMatcher(None, query_token, chunk_token).ratio()
                if similarity > best_match:
                    best_match = similarity

            if best_match >= 0.86:
                score += best_match

        density = score / max(len(chunk.tokens), 1)
        return score + density

    def add_document(self, doc_id: str, text: str):
        raw_chunks = self._chunk_text(text)

        document_chunks = [
            DocumentChunk(
                id=f"{doc_id}_chunk_{index}",
                text=chunk_text,
                tokens=self._tokenize(chunk_text),
            )
            for index, chunk_text in enumerate(raw_chunks)
        ]

        self.chunks[doc_id] = document_chunks
        print(f"Indexed document {doc_id} with {len(document_chunks)} chunks.")

    def get_chunks(self, doc_id: str) -> Optional[list[DocumentChunk]]:
        return self.chunks.get(doc_id)

    def search(self, doc_id: str, query: str, top_k: int = 3) -> list[str]:
        doc_chunks = self.chunks.get(doc_id)
        if not doc_chunks:
            return []

        query_tokens = self._expand_query_tokens(query)
        if not query_tokens:
            return []

        scored_chunks = [
            (chunk, self._score_chunk(chunk, query_tokens))
            for chunk in doc_chunks
        ]
        scored_chunks = [
            (chunk, score)
            for chunk, score in scored_chunks
            if score >= 2.0
        ]

        scored_chunks.sort(key=lambda item: item[1], reverse=True)

        results = []
        for chunk, _ in scored_chunks:
            text = self._normalize_text(chunk.text)
            if not text:
                continue

            if self._is_duplicate_chunk(text, results):
                continue

            results.append(text)

            if len(results) >= top_k:
                break

        return results


vector_service = VectorService()
