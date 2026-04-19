import re
import math
from typing import Optional


class DocumentChunk:
    def __init__(self, id: str, text: str, tokens: list[str]):
        self.id = id
        self.text = text
        self.tokens = tokens


class VectorService:
    def __init__(self):
        self.chunks: dict[str, list[DocumentChunk]] = {}

    def get_all_text_chunks(self) -> list[str]:
        all_text = []
        for doc_chunks in self.chunks.values():
            for chunk in doc_chunks:
                all_text.append(chunk.text)
        return all_text

    # 🔹 Levenshtein distance (for typo handling)
    def _levenshtein_distance(self, a: str, b: str) -> int:
        if len(a) == 0:
            return len(b)
        if len(b) == 0:
            return len(a)

        matrix = [[0] * (len(a) + 1) for _ in range(len(b) + 1)]

        for i in range(len(a) + 1):
            matrix[0][i] = i
        for j in range(len(b) + 1):
            matrix[j][0] = j

        for j in range(1, len(b) + 1):
            for i in range(1, len(a) + 1):
                indicator = 0 if a[i - 1] == b[j - 1] else 1
                matrix[j][i] = min(
                    matrix[j][i - 1] + 1,
                    matrix[j - 1][i] + 1,
                    matrix[j - 1][i - 1] + indicator
                )

        return matrix[len(b)][len(a)]

    def _get_similarity(self, a: str, b: str) -> float:
        dist = self._levenshtein_distance(a, b)
        max_len = max(len(a), len(b))
        return 1.0 if max_len == 0 else 1 - dist / max_len

    def _tokenize(self, text: str) -> list[str]:
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return [word for word in text.split() if len(word) > 2]

    def _chunk_text(self, text: str, size: int = 150, overlap: int = 30) -> list[str]:
        words = text.split()
        chunks = []

        i = 0
        while i < len(words):
            chunk = " ".join(words[i:i + size])
            if chunk.strip():  # ✅ guard against empty chunks
                chunks.append(chunk)
            i += size - overlap

        return chunks

    def add_document(self, doc_id: str, text: str):
        raw_chunks = self._chunk_text(text)

        document_chunks = [
            DocumentChunk(
                id=f"{doc_id}_chunk_{index}",
                text=chunk_text,
                tokens=self._tokenize(chunk_text)
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

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scored_chunks = []

        for chunk in doc_chunks:
            score = 0.0

            # 🔥 Strong phrase match
            if query.lower() in chunk.text.lower():
                score += 5

            # 🔥 Token + fuzzy match
            for q_token in query_tokens:
                best_match = 0.0

                for c_token in chunk.tokens:
                    sim = self._get_similarity(q_token, c_token)
                    if sim > best_match:
                        best_match = sim

                if best_match >= 0.75:
                    score += best_match * 2

            scored_chunks.append((chunk, score))

        # 🔥 Only strong matches
        valid_chunks = [
            (chunk, score)
            for chunk, score in scored_chunks
            if score >= 2
        ]

        valid_chunks.sort(key=lambda x: x[1], reverse=True)
        valid_chunks = valid_chunks[:top_k]

        if not valid_chunks:
            return []

        return [chunk.text for chunk, _ in valid_chunks]


# Singleton instance
vector_service = VectorService()