from typing import Callable

from .store import EmbeddingStore

PROMPT_TEMPLATE = """You are a university services assistant. Answer the question using ONLY the context below.

Rules:
- If the context does not contain the answer, say so plainly. Do not guess at a regulation.
- Cite the source number you used, like [1].
- Answer in the same language as the question.

Context:
{context}

Question: {question}

Answer:"""

NO_CONTEXT = "(the knowledge base returned no matching passages)"


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn
        # Kept so a report can show what the model was actually given, rather
        # than what it was meant to be given.
        self.last_context: list[dict] = []
        self.last_prompt: str = ""

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        self.last_context = results
        self.last_prompt = PROMPT_TEMPLATE.format(
            context=self._format_context(results),
            question=question,
        )
        return self.llm_fn(self.last_prompt)

    @staticmethod
    def _format_context(results: list[dict]) -> str:
        if not results:
            return NO_CONTEXT

        # The source line is what makes grounding checkable: given an answer,
        # you can walk back to the exact chunk that produced it.
        blocks = []
        for position, result in enumerate(results, start=1):
            metadata = result.get("metadata") or {}
            source = metadata.get("source_url") or metadata.get("source") or metadata.get("doc_id", "unknown")
            blocks.append(f"[{position}] source: {source} (score {result.get('score', 0.0):.3f})\n{result['content']}")
        return "\n\n".join(blocks)
