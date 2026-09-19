"""
Benchmark retrieval cho Lab 07 — nhóm Logitech.

Cả nhóm dùng chung file này; mỗi người CHỈ đổi dòng CHUNKER bên dưới.
Chạy từ thư mục gốc repo:
    python bench.py
Kết quả được in ra màn hình và lưu vào ket_qua_benchmark.txt.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from src import (
    EMBEDDING_PROVIDER_ENV,
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    GeminiEmbedder,
    LocalEmbedder,
    OpenAIEmbedder,
    RecursiveChunker,
    SentenceChunker,
    _mock_embed,
)

# ======================================================================
# DÒNG DUY NHẤT MỖI THÀNH VIÊN ĐƯỢC ĐỔI
# Long  : RecursiveChunker(chunk_size=400)
# Việt  : FixedSizeChunker(chunk_size=400, overlap=50)
# Tài   : chunker theo heading (tự viết)
CHUNKER = FixedSizeChunker(chunk_size=400, overlap=50)
# ======================================================================

DATA_DIR = Path("data/dich-vu-sinh-vien-utc")
OUTPUT_FILE = Path("ket_qua_benchmark.txt")
TOP_K = 3

# 5 câu hỏi chung của nhóm (REPORT_NHOM mục 3).
# gold: doc_id chứa đáp án; checks: chuỗi phải có trong ngữ cảnh top-3 (khớp đúng data).
QUERIES = [
    {
        "id": "Q1",
        "query": "Ký túc xá có bao nhiêu phòng và sức chứa bao nhiêu sinh viên?",
        "gold": ["ky-tuc-xa-quan-ly"],
        "checks": ["214 phòng", "1500 sinh viên"],
        "filter": None,
    },
    {
        "id": "Q2",
        "query": "Hỏi về học bổng và vay vốn tín dụng đào tạo thì liên hệ đơn vị nào?",
        "gold": ["cong-tac-sinh-vien", "dao-tao-dai-hoc-hoc-vu"],
        "checks": ["vay vốn tín dụng đào tạo", "học bổng khuyến khích học tập"],
        "filter": None,
    },
    {
        "id": "Q3",
        "query": "Đơn vị nào tổ chức thi và đánh giá kết quả học tập?",
        "gold": ["dao-tao-dai-hoc-hoc-vu"],
        "checks": ["đánh giá kết quả học tập của sinh viên"],
        "filter": {"audience": "student"},
    },
    {
        "id": "Q4",
        "query": "Ai quản lý ký túc xá của trường?",
        "gold": ["cong-tac-sinh-vien"],
        "checks": ["sáp nhập lại Phòng CTCT&SV"],
        "filter": None,
    },
    {
        "id": "Q5",
        "query": "Tra cứu tài liệu thư viện trực tuyến ở đâu, phục vụ những đối tượng nào?",
        "gold": ["thu-vien-dich-vu"],
        "checks": ["opac.utc.edu.vn", "trong và ngoài Trường"],
        "filter": None,
    },
]

_lines: list[str] = []


def out(line: str = "") -> None:
    print(line)
    _lines.append(line)


def parse_markdown(path: Path) -> tuple[dict, str]:
    """Tách frontmatter YAML đơn giản (key: value) thành metadata, phần còn lại là nội dung."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if not text.startswith("---"):
        return {}, text
    _, frontmatter, body = text.split("---", 2)
    metadata = {}
    for line in frontmatter.strip().split("\n"):
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata, body.strip()


def load_chunks(data_dir: Path) -> list[Document]:
    docs: list[Document] = []
    for path in sorted(data_dir.glob("*.md")):
        frontmatter, body = parse_markdown(path)
        for i, chunk in enumerate(CHUNKER.chunk(body)):
            docs.append(
                Document(
                    id=f"{path.stem}#{i}",
                    content=chunk,
                    # Trải frontmatter vào mọi chunk để search_with_filter có cái để lọc.
                    metadata={**frontmatter, "doc_id": path.stem, "chunk_index": i},
                )
            )
    return docs


def pick_embedder():
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    factories = {"local": LocalEmbedder, "openai": OpenAIEmbedder, "gemini": GeminiEmbedder}
    if provider in factories:
        try:
            return factories[provider]()
        except Exception as exc:  # thiếu thư viện / API key -> quay về mock
            out(f"[!] Không khởi tạo được embedder '{provider}': {exc}. Dùng mock.")
    return _mock_embed


def score(results: list[dict], item: dict) -> dict:
    """Chấm hai mức: theo doc_id (ngây thơ) và theo nội dung (chuỗi đặc trưng)."""
    doc_ids = [r["metadata"]["doc_id"] for r in results]
    context = "\n".join(r["content"] for r in results)
    found = {s: (s in context) for s in item["checks"]}
    content_ok = all(found.values())
    gold_in_top = any(d in item["gold"] for d in doc_ids)
    if content_ok and doc_ids and doc_ids[0] in item["gold"]:
        points = 2
    elif content_ok:
        points = 1
    else:
        points = 0
    return {"gold_in_top": gold_in_top, "found": found, "points": points}


def run_query(store: EmbeddingStore, item: dict, metadata_filter: dict | None, label: str) -> dict:
    results = store.search_with_filter(item["query"], top_k=TOP_K, metadata_filter=metadata_filter)
    s = score(results, item)
    out(f"--- {item['id']} {label} | filter={metadata_filter}")
    for rank, r in enumerate(results, start=1):
        mark = "*" if r["metadata"]["doc_id"] in item["gold"] else " "
        preview = r["content"][:110].replace("\n", " ")
        out(f"  {rank}.{mark} score={r['score']:.3f}  doc_id={r['metadata']['doc_id']}  ({r['id']})")
        out(f"       {preview}...")
    checks = ", ".join(f"'{k}': {'OK' if v else 'THIẾU'}" for k, v in s["found"].items())
    out(f"  gold doc trong top-{TOP_K}: {'CÓ' if s['gold_in_top'] else 'KHÔNG'} | chuỗi đáp án: {checks} | điểm: {s['points']}/2")
    return s


def main() -> None:
    embedder = pick_embedder()
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    docs = load_chunks(DATA_DIR)
    store = EmbeddingStore(collection_name="bench", embedding_fn=embedder)
    store.add_documents(docs)

    lengths = [len(d.content) for d in docs]
    out("=" * 78)
    out(f"Chunker        : {CHUNKER.__class__.__name__} {vars(CHUNKER)}")
    out(f"Embedding      : {backend}")
    if embedder is _mock_embed:
        out("[!] Đang dùng MockEmbedder (băm MD5, không có ngữ nghĩa) -> điểm số chỉ là nhiễu.")
    out(f"Dữ liệu        : {DATA_DIR} ({len(list(DATA_DIR.glob('*.md')))} file)")
    out(f"Số chunk đã nạp: {store.get_collection_size()} | độ dài TB: {sum(lengths) / len(lengths):.0f} ký tự")
    out("(* = chunk thuộc tài liệu gold)")
    out("=" * 78)

    summary = []
    for item in QUERIES:
        if item["filter"]:
            # A/B bắt buộc: chạy cả không lọc và có lọc; điểm chính tính theo bản có lọc.
            a = run_query(store, item, None, "[A: không filter]")
            b = run_query(store, item, item["filter"], "[B: có filter]")
            summary.append((item["id"], b, f"A={a['points']} / B={b['points']}"))
        else:
            s = run_query(store, item, None, "")
            summary.append((item["id"], s, ""))
        out()

    out("=" * 78)
    out("TỔNG KẾT")
    for qid, s, note in summary:
        out(f"  {qid}: gold doc trong top-3={'CÓ' if s['gold_in_top'] else 'KHÔNG'} | điểm nội dung={s['points']}/2 {note}")
    naive = sum(1 for _, s, _ in summary if s["gold_in_top"])
    total = sum(s["points"] for _, s, _ in summary)
    out(f"  Chấm theo doc_id (ngây thơ): {naive}/5 câu có tài liệu gold trong top-3")
    out(f"  Chấm theo nội dung         : {total}/10 điểm")
    out("=" * 78)

    OUTPUT_FILE.write_text("\n".join(_lines) + "\n", encoding="utf-8")
    print(f"\nĐã lưu kết quả vào {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
