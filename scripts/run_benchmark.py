#!/usr/bin/env python3
"""Run the group's five benchmark queries against one chunking strategy.

Every member runs the same queries from benchmark/queries.json over the same
corpus, changing only --strategy. That is the whole point of Phase 2: the
strategy is the variable, everything else is held still.

    python scripts/run_benchmark.py --strategy recursive
    python scripts/run_benchmark.py --strategy heading --markdown

Retrieval is scored automatically as hit@3 against gold_doc_ids. Whether the
agent's ANSWER is correct is a human call - the rubric awards 2 only when the
answer is right as well - so the script prints the answer and leaves that column
for you.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import (  # noqa: E402
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    KnowledgeBaseAgent,
    RecursiveChunker,
    SentenceChunker,
    _mock_embed,
)

FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
FIELD = re.compile(r'^(\w+):\s*"?(.*?)"?\s*$', re.MULTILINE)
# Every unit page uses the same four ALL-CAPS section headings.
HEADING = re.compile(r"^(?=[^a-zà-ỹ\n]{6,}$)", re.MULTILINE)


class HeadingChunker:
    """Split on the document's own section headings.

    K4_VARIANT.md requires at least one member to chunk by heading/section. It
    suits this corpus unusually well: all ten pages are built from the same four
    ALL-CAPS headings (THONG TIN CHUNG, CHUC NANG NHIEM VU, GIOI THIEU, CAC THANH
    TICH DA DAT DUOC), so a heading split lands one topic per chunk instead of
    cutting a duty list in half. Sections longer than max_chars fall back to the
    recursive splitter.
    """

    def __init__(self, max_chars: int = 1200) -> None:
        self.max_chars = max_chars
        self._fallback = RecursiveChunker(chunk_size=max_chars)

    def chunk(self, text: str) -> list[str]:
        sections = [part.strip() for part in HEADING.split(text) if part.strip()]
        chunks: list[str] = []
        for section in sections:
            chunks.extend([section] if len(section) <= self.max_chars else self._fallback.chunk(section))
        return chunks


STRATEGIES = {
    "fixed": lambda: FixedSizeChunker(chunk_size=500, overlap=50),
    "sentence": lambda: SentenceChunker(max_sentences_per_chunk=3),
    "recursive": lambda: RecursiveChunker(chunk_size=400),
    "heading": lambda: HeadingChunker(max_chars=1200),
}


def load_documents(corpus_dir: Path) -> list[tuple[str, str, dict]]:
    documents = []
    for path in sorted(corpus_dir.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        match = FRONT_MATTER.match(raw)
        if not match:
            print(f"Skipping {path.name}: no front matter", file=sys.stderr)
            continue
        metadata = dict(FIELD.findall(match.group(1)))
        documents.append((metadata["doc_id"], raw[match.end() :].strip(), metadata))
    return documents


def pick_embedder():
    """Same provider selection as main.py, so a benchmark matches a manual run."""
    try:
        from dotenv import load_dotenv

        load_dotenv(override=False)
    except Exception:
        pass

    provider = os.getenv("EMBEDDING_PROVIDER", "mock").strip().lower()
    try:
        if provider == "local":
            from src import LocalEmbedder

            return LocalEmbedder(), provider
        if provider == "openai":
            from src import OpenAIEmbedder

            return OpenAIEmbedder(), provider
        if provider == "gemini":
            from src import GeminiEmbedder

            return GeminiEmbedder(), provider
    except Exception as error:
        print(f"! {provider} embedder unavailable ({error}); falling back to mock", file=sys.stderr)
    return _mock_embed, "mock"


def demo_llm(prompt: str) -> str:
    """Placeholder so the agent path runs without a chat model configured."""
    context = prompt.split("Context:", 1)[-1].split("Question:", 1)[0].strip()
    return (context.splitlines() or ["(no context)"])[0][:200]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strategy", choices=sorted(STRATEGIES), default="recursive")
    parser.add_argument("--queries", type=Path, default=Path("benchmark/queries.json"))
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--markdown", action="store_true", help="Print the report table instead of the full trace")
    args = parser.parse_args()

    spec = json.loads(args.queries.read_text(encoding="utf-8"))
    documents = load_documents(Path(spec["corpus"]))
    embedder, provider = pick_embedder()

    chunker = STRATEGIES[args.strategy]()
    store = EmbeddingStore(collection_name=f"benchmark_{args.strategy}", embedding_fn=embedder)
    chunk_total = 0
    for doc_id, body, metadata in documents:
        pieces = chunker.chunk(body)
        chunk_total += len(pieces)
        store.add_documents(
            [
                Document(id=f"{doc_id}#{index}", content=piece, metadata={**metadata, "chunk_index": str(index)})
                for index, piece in enumerate(pieces)
            ]
        )

    agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)
    print(f"strategy={args.strategy}  embedder={provider}  docs={len(documents)}  chunks={chunk_total}")
    if provider == "mock":
        print("! MockEmbedder is an MD5 hash with no semantic signal. These scores are noise.\n", file=sys.stderr)

    rows, hits = [], 0
    for query in spec["queries"]:
        metadata_filter = query.get("metadata_filter")
        results = (
            store.search_with_filter(query["query"], top_k=args.top_k, metadata_filter=metadata_filter)
            if metadata_filter
            else store.search(query["query"], top_k=args.top_k)
        )
        retrieved = [result["metadata"]["doc_id"] for result in results]
        hit = any(doc_id in query["gold_doc_ids"] for doc_id in retrieved)
        trapped = [doc_id for doc_id in retrieved if doc_id in query.get("trap_doc_ids", [])]
        hits += hit
        rows.append((query, results, retrieved, hit, trapped))

        if not args.markdown:
            print(f"\n{query['id']}  {query['query']}")
            print(f"   filter: {metadata_filter or '-'}    gold: {', '.join(query['gold_doc_ids'])}")
            for rank, result in enumerate(results, start=1):
                mark = "OK  " if result["metadata"]["doc_id"] in query["gold_doc_ids"] else "    "
                trap = "  <-- TRAP" if result["metadata"]["doc_id"] in query.get("trap_doc_ids", []) else ""
                snippet = " ".join(result["content"].split())[:95]
                print(f"   {mark}{rank}. {result['score']:+.4f}  {result['metadata']['doc_id']}{trap}")
                print(f"          {snippet}")
            print(f"   hit@{args.top_k}: {'YES' if hit else 'NO'}{'   trap retrieved: ' + ', '.join(trapped) if trapped else ''}")
            print(f"   agent: {agent.answer(query['query'], top_k=args.top_k)[:160]}")

    if args.markdown:
        print(f"\n| # | Câu hỏi | Top-1 | Score | Gold trong top-3? | Bẫy bị lấy |")
        print("|---|---|---|---|---|---|")
        for query, results, retrieved, hit, trapped in rows:
            top = results[0] if results else None
            print(
                f"| {query['id']} | {query['query'][:54]} | {top['metadata']['doc_id'] if top else '-'} "
                f"| {top['score']:+.4f} | {'có' if hit else 'KHÔNG'} | {', '.join(trapped) or '-'} |"
            )

    print(f"\nhit@{args.top_k}: {hits}/{len(spec['queries'])}   strategy={args.strategy}   embedder={provider}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
