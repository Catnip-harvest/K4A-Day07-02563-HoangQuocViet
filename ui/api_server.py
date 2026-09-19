#!/usr/bin/env python3
"""Local API for the Phase 1 UI. Stdlib only - nothing to pip install.

Every endpoint is a thin wrapper over the code in src/, which is the point: the
UI exercises the graded implementation rather than reimplementing any of it. If
a chunker is wrong, this shows it wrong.

    python ui/api_server.py            # serves on 127.0.0.1:8791

Run `npm run dev` in ui/ alongside it; next.config.ts proxies /api/* here.
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from run_benchmark import STRATEGIES, load_documents, pick_embedder  # noqa: E402
from src import (  # noqa: E402
    ChunkingStrategyComparator,
    Document,
    EmbeddingStore,
    KnowledgeBaseAgent,
    compute_similarity,
)

HOST, PORT = "127.0.0.1", 8791
CORPUS = ROOT / "data" / "dich-vu-sinh-vien-utc"
QUERIES = ROOT / "benchmark" / "queries.json"

_embedder, _provider = pick_embedder()
_documents = load_documents(CORPUS)
_stores: dict[str, tuple[EmbeddingStore, int]] = {}


def store_for(strategy: str) -> tuple[EmbeddingStore, int]:
    """Build one store per strategy, once. Embedding the corpus is the slow part."""
    if strategy not in _stores:
        chunker = STRATEGIES[strategy]()
        store = EmbeddingStore(collection_name=f"ui_{strategy}", embedding_fn=_embedder)
        count = 0
        for doc_id, body, metadata in _documents:
            pieces = chunker.chunk(body)
            count += len(pieces)
            store.add_documents(
                [
                    Document(id=f"{doc_id}#{i}", content=piece, metadata={**metadata, "chunk_index": str(i)})
                    for i, piece in enumerate(pieces)
                ]
            )
        _stores[strategy] = (store, count)
    return _stores[strategy]


def answer_with(prompt: str) -> str:
    """No chat model is configured for the lab, so the 'answer' is the grounding.

    Returning the top passage verbatim keeps the agent honest: whatever appears
    here came out of the corpus, and the citation above it says which document.
    """
    context = prompt.split("Context:", 1)[-1].split("Question:", 1)[0].strip()
    body = [line for line in context.splitlines() if line.strip() and not line.startswith("[")]
    return " ".join(body[:4])[:600] or "(không truy xuất được đoạn nào)"


def meta() -> dict:
    return {
        "embedder": _provider,
        "embedder_is_mock": _provider == "mock",
        "documents": [
            {"doc_id": doc_id, "chars": len(body), **{k: v for k, v in metadata.items() if k != "doc_id"}}
            for doc_id, body, metadata in _documents
        ],
        "strategies": sorted(STRATEGIES),
        "queries": json.loads(QUERIES.read_text(encoding="utf-8"))["queries"] if QUERIES.exists() else [],
    }


def compare_chunking(payload: dict) -> dict:
    # Either chunk the text the user pasted, or load one of the corpus documents
    # by id so the UI can demonstrate on real data without shipping a copy of it.
    doc_id = payload.get("doc_id")
    if doc_id:
        text = next((body for identifier, body, _ in _documents if identifier == doc_id), "")
    else:
        text = payload.get("text") or ""
    size = int(payload.get("chunk_size") or 200)
    if not text.strip():
        return {"strategies": {}, "text": ""}
    comparison = ChunkingStrategyComparator().compare(text, chunk_size=size)
    # The heading strategy is Phase 2 work, so it is not part of the graded
    # comparator - but it is the one that suits this corpus, so show it too.
    heading = STRATEGIES["heading"]().chunk(text)
    lengths = [len(chunk) for chunk in heading]
    comparison["heading"] = {
        "count": len(heading),
        "avg_length": round(sum(lengths) / len(lengths), 2) if lengths else 0.0,
        "min_length": min(lengths) if lengths else 0,
        "max_length": max(lengths) if lengths else 0,
        "chunks": heading,
    }
    return {"strategies": comparison, "text": text}


def similarity(payload: dict) -> dict:
    pairs = payload.get("pairs") or []
    scored = []
    for pair in pairs:
        left, right = (pair + ["", ""])[:2]
        score = compute_similarity(_embedder(left), _embedder(right)) if left and right else 0.0
        scored.append({"a": left, "b": right, "score": score})
    return {"pairs": scored, "embedder": _provider}


def search(payload: dict) -> dict:
    strategy = payload.get("strategy") or "recursive"
    store, chunks = store_for(strategy)
    metadata_filter = payload.get("metadata_filter") or None
    query = payload.get("query") or ""
    top_k = int(payload.get("top_k") or 3)
    results = (
        store.search_with_filter(query, top_k=top_k, metadata_filter=metadata_filter)
        if metadata_filter
        else store.search(query, top_k=top_k)
    )
    return {"results": results, "chunks_indexed": chunks, "strategy": strategy, "embedder": _provider}


def answer(payload: dict) -> dict:
    strategy = payload.get("strategy") or "recursive"
    store, chunks = store_for(strategy)
    agent = KnowledgeBaseAgent(store=store, llm_fn=answer_with)
    top_k = int(payload.get("top_k") or 3)
    reply = agent.answer(payload.get("question") or "", top_k=top_k)
    return {
        "reply": reply,
        "context": agent.last_context,
        "prompt": agent.last_prompt,
        "chunks_indexed": chunks,
        "strategy": strategy,
        "embedder": _provider,
    }


def benchmark(payload: dict) -> dict:
    strategy = payload.get("strategy") or "recursive"
    store, chunks = store_for(strategy)
    spec = json.loads(QUERIES.read_text(encoding="utf-8"))
    rows = []
    for query in spec["queries"]:
        metadata_filter = query.get("metadata_filter")
        results = (
            store.search_with_filter(query["query"], top_k=3, metadata_filter=metadata_filter)
            if metadata_filter
            else store.search(query["query"], top_k=3)
        )
        retrieved = [result["metadata"]["doc_id"] for result in results]
        rows.append(
            {
                "id": query["id"],
                "query": query["query"],
                "tests": query["tests"],
                "gold_answer": query["gold_answer"],
                "gold_doc_ids": query["gold_doc_ids"],
                "metadata_filter": metadata_filter,
                "results": results,
                "hit": any(doc_id in query["gold_doc_ids"] for doc_id in retrieved),
                "traps": [d for d in retrieved if d in query.get("trap_doc_ids", [])],
            }
        )
    return {
        "rows": rows,
        "hits": sum(row["hit"] for row in rows),
        "total": len(rows),
        "strategy": strategy,
        "chunks_indexed": chunks,
        "embedder": _provider,
    }


ROUTES = {
    "/api/chunk": compare_chunking,
    "/api/similarity": similarity,
    "/api/search": search,
    "/api/answer": answer,
    "/api/benchmark": benchmark,
}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, status: int, body: dict) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(204, {})

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/api/meta":
            self._send(200, meta())
        else:
            self._send(404, {"error": f"no route {self.path}"})

    def do_POST(self) -> None:  # noqa: N802
        route = ROUTES.get(self.path.rstrip("/"))
        if route is None:
            self._send(404, {"error": f"no route {self.path}"})
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length) or b"{}")
            self._send(200, route(payload))
        except Exception as error:  # surfaced in the UI rather than swallowed
            self._send(500, {"error": f"{type(error).__name__}: {error}"})

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"  {self.address_string()} {fmt % args}\n")


if __name__ == "__main__":
    print(f"corpus: {len(_documents)} documents from {CORPUS.relative_to(ROOT)}")
    print(f"embedder: {_provider}")
    if _provider == "mock":
        print("! MockEmbedder has no semantic signal - retrieval results are noise.")
    print(f"listening on http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
