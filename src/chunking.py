from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


# A sentence ends at . ! or ? and is followed by whitespace. The lookbehind
# keeps the punctuation attached to the sentence it belongs to, so a chunk still
# reads like prose after it has been split.
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sentences = [piece.strip() for piece in _SENTENCE_BOUNDARY.split(text)]
        sentences = [piece for piece in sentences if piece]
        if not sentences:
            return []

        size = self.max_sentences_per_chunk
        return [" ".join(sentences[start : start + size]) for start in range(0, len(sentences), size)]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return self._split(text, list(self.separators))

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        text = current_text.strip()
        if not text:
            return []
        # Small enough already: the whole point of going separator by separator
        # is to stop as soon as a piece fits.
        if len(text) <= self.chunk_size:
            return [text]

        # Out of separators (or told to use the empty one): nothing left to
        # respect, so cut on the character count and accept the broken word.
        if not remaining_separators or remaining_separators[0] == "":
            return self._hard_split(text)

        separator, rest = remaining_separators[0], remaining_separators[1:]
        pieces = text.split(separator)
        if len(pieces) == 1:
            # This separator does not occur here. Try the next one down.
            return self._split(text, rest)

        # Glue neighbouring pieces back together while they still fit. A piece
        # that is too big on its own gets taken apart by the next separator.
        chunks: list[str] = []
        buffer = ""
        for piece in pieces:
            candidate = piece if not buffer else buffer + separator + piece
            if len(candidate) <= self.chunk_size:
                buffer = candidate
                continue

            if buffer:
                chunks.append(buffer)
                buffer = ""
            if len(piece) <= self.chunk_size:
                buffer = piece
            else:
                chunks.extend(self._split(piece, rest))

        if buffer:
            chunks.append(buffer)

        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def _hard_split(self, text: str) -> list[str]:
        return [text[start : start + self.chunk_size] for start in range(0, len(text), self.chunk_size)]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    magnitude_a = math.sqrt(_dot(vec_a, vec_a))
    magnitude_b = math.sqrt(_dot(vec_b, vec_b))
    # A zero vector points nowhere, so the angle between it and anything else is
    # undefined. Returning 0.0 keeps callers from dividing by zero.
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        # SentenceChunker has no character budget, so it is given the sentence
        # count that lands nearest the same chunk size on ordinary prose. The
        # three strategies are then comparable on one axis: how big a chunk is.
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=chunk_size // 10),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison: dict = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            lengths = [len(chunk) for chunk in chunks]
            comparison[name] = {
                "count": len(chunks),
                "avg_length": round(sum(lengths) / len(lengths), 2) if lengths else 0.0,
                "min_length": min(lengths) if lengths else 0,
                "max_length": max(lengths) if lengths else 0,
                "chunks": chunks,
            }
        return comparison
