# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Hoàng Quốc Việt (02563)
**Nhóm:** Logitech
**Ngày:** 2026-09-19

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine (High cosine similarity) nghĩa là gì?**

> Mỗi chunk trong cơ sở dữ liệu được mô hình embedding biểu diễn thành một **vector** trong không gian vector. Về bản chất nó giống hệt vector 3 chiều học ở hình học phổ thông, chỉ khác là số chiều lớn hơn nhiều (64 chiều với `MockEmbedder`, 384 chiều với mô hình multilingual của lab). Hai đoạn văn bản có nội dung gần nhau thì hai vector sẽ nằm trong cùng một vùng và **chỉ về cùng một hướng**. Cosine similarity đo **góc** giữa hai vector đó rồi quy ra một điểm số trong khoảng `[-1, 1]`: `+1` là trùng hướng hoàn toàn, `0` là vuông góc (không liên quan), `-1` là ngược hướng.

**Ví dụ có độ tương tự CAO:**
- Câu A: *"Sinh viên đăng ký học phần trong tuần đầu tiên của tháng 8."*
- Câu B: *"Thời gian đăng ký môn học bắt đầu từ đầu tháng 8."*
- Tại sao tương đồng: cùng một chủ thể (sinh viên), cùng một hành động (đăng ký học phần), cùng một mốc thời gian. Chữ dùng khác nhau ("học phần" / "môn học") nhưng ý nghĩa trùng nhau, nên embedding đặt hai câu về cùng một hướng.

**Ví dụ có độ tương tự THẤP:**
- Câu A: *"Thư viện mở cửa đến 22 giờ các ngày trong tuần."*
- Câu B: *"Học phí kỳ mùa thu phải nộp trước ngày 15 tháng 9."*
- Tại sao khác: khác chủ đề hoàn toàn (giờ mở cửa thư viện / hạn nộp học phí), không chia sẻ thực thể hay hành động nào. Hai vector gần như vuông góc, điểm số tiến về 0.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Vì cosine **chỉ đo hướng, bỏ qua độ dài** của vector. Một văn bản quy định dài 5 trang và một câu hỏi ngắn một dòng về đúng chủ đề đó sẽ có độ dài vector rất khác nhau, nên khoảng cách Euclid giữa chúng lớn — dù nội dung trùng nhau. Cosine vẫn cho điểm cao vì hai vector chỉ về cùng một hướng. Ngoài ra cosine luôn nằm trong khoảng `[-1, 1]` nên dễ đặt ngưỡng lọc, còn khoảng cách Euclid không có chặn trên và phải chuẩn hoá lại theo từng bộ dữ liệu.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> Phép tính:
> `số chunk = ⌈(độ_dài − overlap) / (chunk_size − overlap)⌉`
> `= ⌈(10000 − 50) / (500 − 50)⌉ = ⌈9950 / 450⌉ = ⌈22.11⌉`
>
> **Đáp án: 23 chunks.**
>
> Kiểm chứng bằng chính code trong `src/chunking.py`: `FixedSizeChunker` nhảy theo bước `step = 500 − 50 = 450`, dừng khi `start + 500 ≥ 10000`, tức `start ≥ 9500`. Vì `start = 450k`, ta có `k ≥ 21.1` → `k = 22` là vòng cuối, nên tổng số vòng là `k = 0…22` = **23 chunks**. Công thức và cài đặt khớp nhau.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> `⌈(10000 − 100) / (500 − 100)⌉ = ⌈9900 / 400⌉ = ⌈24.75⌉ = **25 chunks**` — tăng thêm 2 chunk (khoảng +8.7%).
>
> Overlap lớn hơn nghĩa là tốn thêm chi phí lưu trữ và số lần gọi embedding, đổi lại nó **bảo vệ các câu nằm vắt qua ranh giới chunk**. Chia cứng theo ký tự rất dễ cắt một câu quy định làm đôi; khi đó không chunk nào chứa trọn ý, và cả hai đều truy xuất kém. Với overlap, phần bị cắt đó xuất hiện nguyên vẹn trong ít nhất một chunk.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Dùng regex `r"(?<=[.!?])\s+"`. Điểm quan trọng là **lookbehind** `(?<=...)`: nó cắt ở khoảng trắng *sau* dấu câu, nên dấu `.` `!` `?` vẫn dính vào câu mà nó kết thúc — chunk đọc ra vẫn là văn xuôi bình thường chứ không phải các mẩu cụt đầu cụt đuôi. `\s+` gộp luôn cả `". "` lẫn `".\n"` nên không cần liệt kê riêng từng dấu phân cách.
> Các trường hợp ngoại lệ đã xử lý: chuỗi rỗng hoặc chỉ có khoảng trắng → trả về `[]`; mẩu rỗng sinh ra từ dấu chấm cuối văn bản bị loại bỏ; `max_sentences_per_chunk` bị ép tối thiểu bằng 1 (đã có sẵn trong `__init__`) để không chia cho 0.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Thuật toán đi **lần lượt theo thứ tự ưu tiên** của danh sách separator (`"\n\n"` → `"\n"` → `". "` → `" "` → `""`), tức là ưu tiên cắt ở ranh giới ngữ nghĩa lớn nhất trước, chỉ hạ xuống ranh giới nhỏ hơn khi bắt buộc.
> Có **ba base case**: (1) đoạn đã ngắn hơn `chunk_size` → trả về nguyên vẹn, đây là điều kiện dừng chính; (2) hết separator, hoặc separator hiện tại là `""` → cắt cứng theo số ký tự và chấp nhận vỡ từ; (3) separator hiện tại không xuất hiện trong đoạn → bỏ qua, đệ quy xuống separator kế tiếp.
> Sau khi `split`, các mẩu láng giềng được **gộp ngược lại** một cách tham lam chừng nào tổng độ dài còn vừa `chunk_size`. Mẩu nào tự nó đã quá to thì mới bị đem đi đệ quy với separator kế tiếp. Nếu không gộp lại thì `"\n"` sẽ sinh ra hàng trăm chunk một dòng, mất hết ngữ cảnh.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Mỗi `Document` được chuyển thành một **record chuẩn hoá** (`_make_record`) gồm `chunk_id`, `id`, `content`, `metadata`, `embedding`. Trong đó `metadata["doc_id"]` được **đóng dấu tự động từ `doc.id`** — đây là khoá mà `delete_document` và bộ lọc metadata dựa vào, nên gán một chỗ thay vì tin tưởng mọi nơi gọi đều nhớ gán.
> `search` nhúng câu truy vấn rồi tính **tích vô hướng (dot product)** với từng embedding đã lưu, sắp xếp giảm dần, cắt `top_k`. Vì tất cả embedder trong lab đều trả về **vector đơn vị** (đã chuẩn hoá), tích vô hướng *chính là* cosine similarity — phép chia cho hai độ dài là chia cho 1. `compute_similarity()` là dạng tổng quát của cùng một công thức.
> Về ChromaDB: danh sách in-memory **luôn là nguồn sự thật** cho việc đếm, xếp hạng và lọc; Chroma chỉ được ghi thêm vào để bộ sưu tập có thể lưu lại. Lý do không để Chroma xếp hạng: index mặc định của nó đo khoảng cách L2 chứ không phải cosine, nên điểm số sẽ đổi tuỳ theo máy có cài gói tuỳ chọn đó hay không. Giữ một bộ chấm điểm duy nhất thì kết quả benchmark mới lặp lại được trên mọi máy trong lớp.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> **Lọc trước, chấm điểm sau.** Nếu chấm điểm trước rồi mới lọc, `top_k` sẽ bị tiêu vào những chunk sau đó bị vứt đi — một truy vấn `metadata_filter={"audience": "student"}` sẽ trả về thiếu kết quả dù trong kho vẫn còn chunk hợp lệ. Bộ lọc dùng phép so khớp bằng trên mọi cặp khoá-giá trị (`all(...)`); `metadata_filter` rỗng hoặc `None` thì bỏ qua bước lọc, nên kết quả trùng khớp với `search()` thường.
> `delete_document` quét theo `metadata["doc_id"]`, trả về `False` ngay nếu không có chunk nào khớp (không đụng vào store), ngược lại giữ lại phần còn lại và trả `True`. Khi Chroma đang bật thì các `chunk_id` tương ứng cũng bị xoá theo, bọc trong `try/except` — mất khả năng lưu trữ lâu dài thì chấp nhận được, mất dữ liệu thì không.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Ba bước đúng theo mô hình RAG: truy xuất `top_k` chunk → dựng prompt → gọi `llm_fn`.
> Ngữ cảnh được đưa vào dưới dạng các khối **đánh số kèm nguồn**: `[1] source: <source_url|source|doc_id> (score 0.412)` rồi mới đến nội dung chunk. Prompt yêu cầu mô hình chỉ trả lời dựa trên ngữ cảnh, nói thẳng khi không có thông tin (không được đoán quy định của trường), trích số nguồn đã dùng, và trả lời bằng đúng ngôn ngữ của câu hỏi.
> Đánh số kèm nguồn chính là thứ làm cho **grounding kiểm chứng được**: có câu trả lời là truy ngược được về đúng chunk đã sinh ra nó — tiêu chí số 4 trong `docs/EVALUATION.md`. Ngoài ra `last_context` và `last_prompt` được giữ lại sau mỗi lần gọi, để báo cáo trình bày được thứ mô hình *thực sự* nhận, chứ không phải thứ đáng lẽ nó phải nhận.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ pytest tests/ -v

============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
rootdir: K4A-Day07-02563-HoangQuocViet
collecting ... collected 42 items

TestProjectStructure::test_root_main_entrypoint_exists PASSED
TestProjectStructure::test_src_package_exists PASSED
TestClassBasedInterfaces::test_chunker_classes_exist PASSED
TestClassBasedInterfaces::test_mock_embedder_exists PASSED
TestFixedSizeChunker::test_chunks_respect_size PASSED
TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
TestFixedSizeChunker::test_returns_list PASSED
TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
TestSentenceChunker::test_chunks_are_strings PASSED
TestSentenceChunker::test_respects_max_sentences PASSED
TestSentenceChunker::test_returns_list PASSED
TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
TestRecursiveChunker::test_handles_double_newline_separator PASSED
TestRecursiveChunker::test_returns_list PASSED
TestEmbeddingStore::test_add_documents_increases_size PASSED
TestEmbeddingStore::test_add_more_increases_further PASSED
TestEmbeddingStore::test_initial_size_is_zero PASSED
TestEmbeddingStore::test_search_results_have_content_key PASSED
TestEmbeddingStore::test_search_results_have_score_key PASSED
TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
TestEmbeddingStore::test_search_returns_list PASSED
TestKnowledgeBaseAgent::test_answer_non_empty PASSED
TestKnowledgeBaseAgent::test_answer_returns_string PASSED
TestComputeSimilarity::test_identical_vectors_return_1 PASSED
TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
TestComputeSimilarity::test_zero_vector_returns_0 PASSED
TestCompareChunkingStrategies::test_counts_are_positive PASSED
TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
TestCompareChunkingStrategies::test_returns_three_strategies PASSED
TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================= 42 passed in 0.05s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> **CHƯA ĐIỀN — phần này phải tự dự đoán TRƯỚC khi chạy code, nên không thể điền hộ.**
>
> Cách nhanh nhất: mở giao diện (`python ui/api_server.py` + `cd ui && npm run dev`), vào tab
> **Độ tương tự**. Nút hiện điểm bị khoá cho đến khi cả 5 cặp có dự đoán, nên không thể xem
> trộm rồi điền ngược. Điền xong thì chép số vào bảng dưới.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | | | cao / thấp | | |
| 2 | | | cao / thấp | | |
| 3 | | | cao / thấp | | |
| 4 | | | cao / thấp | | |
| 5 | | | cao / thấp | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

**Cấu hình:** `LocalEmbedder` — `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`,
384 chiều · chiến lược **`FixedSizeChunker(chunk_size=500, overlap=50)`** · 10 tài liệu → **70 chunk**.
Chạy bằng `python scripts/run_benchmark.py --strategy fixed`.

| # | Câu hỏi | Top-1 chunk | Score | Liên quan? | Câu trả lời của agent |
|---|---|---|---|---|---|
| 1 | Ký túc xá có bao nhiêu phòng, sức chứa bao nhiêu SV? | `ky-tuc-xa-quan-ly` | +0.7358 | ✅ | Đúng — trích được 214 phòng / 1500 SV |
| 2 | Học bổng và vay vốn tín dụng thì liên hệ đâu? | `dao-tao-dai-hoc-hoc-vu` | +0.6330 | ✅ | Đúng — top-3 có cả hai phòng liên quan |
| 3 | Đơn vị nào tham mưu về chăm sóc sức khỏe SV? | `tram-y-te` | +0.7232 | ✅ | Đúng — có lọc `audience=student` |
| 4 | Ai quản lý ký túc xá? | `ky-tuc-xa-quan-ly` | +0.7891 | ⚠️ **sai** | **Sai** — trích trang đã bị thay thế |
| 5 | Tra cứu thư viện online ở đâu, phục vụ ai? | `thu-vien-dich-vu` | +0.6550 | ✅ | Đúng — cả OPAC lẫn danh sách bạn đọc |

**Bao nhiêu câu trả về chunk liên quan trong top-3?** **5 / 5**

**Nhưng chấm theo rubric thì là 9/10, không phải 10/10.** Câu 4 chỉ được **1 điểm**:
tài liệu đúng có trong top-3, nhưng đứng **hạng 3**, và câu trả lời của agent **sai**.

### Phân tích lỗi câu 4 (cho Bài tập 3.5)

Câu *"Ai quản lý ký túc xá của trường?"* trả về:

| Hạng | Score | Tài liệu | |
|---|---|---|---|
| 1 | **+0.7891** | `ky-tuc-xa-quan-ly` | ❌ trang đã bị thay thế |
| 2 | **+0.7130** | `ky-tuc-xa-quan-ly` | ❌ cũng trang đó |
| 3 | +0.6575 | `cong-tac-sinh-vien` | ✅ trang đúng |

Agent trích nguồn `ban-quan-ly-ky-tuc-xa` với score 0.789 — **rất tự tin và sai**.

**Nguyên nhân:** kho chứa **hai câu trả lời chính thức mâu thuẫn nhau**, cả hai đều crawl
cùng ngày từ website đang chạy của trường:

- `cong-tac-sinh-vien.md` — *"Phòng Chăm sóc người học được thành lập theo Quyết định số
  2109/QĐ-ĐHGTVT trên cơ sở sắp xếp, **sáp nhập lại Phòng CTCT&SV, Ban Quản lý KTX, Trạm Y tế**"*
- `ky-tuc-xa-quan-ly.md` — vẫn tự mô tả là đơn vị đang hoạt động (QĐ 390/QĐ-TC, 1981)

Trang cũ khớp từ khoá tốt hơn hẳn: câu hỏi chứa "ký túc xá", mà trang đó nhắc cụm này
hàng chục lần, còn trang đúng chỉ nhắc gián tiếp qua "quản lý sinh viên nội trú".
Embedding hoàn toàn đúng về mặt ngữ nghĩa — nó chỉ không biết tài liệu nào còn hiệu lực.

**Đây là lỗi KHÔNG sửa được bằng chunking.** Đã kiểm chứng trên cả bốn chiến lược:

| Chiến lược | Score của trang sai (hạng 1) | Trang đúng nằm ở đâu |
|---|---|---|
| Fixed size | +0.7891 | hạng 3 |
| By sentence | +0.7780 | **ngoài top-3** |
| Recursive | +0.7796 | trong top-3 |
| By heading | +0.7635 | trong top-3 |

Cả bốn đều đặt trang sai lên hạng 1. Đổi `chunk_size`, đổi separator, cắt theo tiêu đề —
không cách nào giúp được, vì vấn đề không nằm ở chỗ cắt.

**Đề xuất cải thiện:** thêm metadata về hiệu lực và dùng nó để xếp hạng, không chỉ để lọc:

```yaml
document_version: "1981-10-24"
superseded_by: cong-tac-sinh-vien     # QĐ 2109/QĐ-ĐHGTVT
status: superseded                    # active | superseded
```

Rồi `search_with_filter(metadata_filter={"status": "active"})`, hoặc phạt điểm tài liệu
`superseded` trước khi cắt top-k. Chi phí: một trường metadata. Hiệu quả: câu 4 từ 1 điểm
lên 2 điểm, và quan trọng hơn là agent thôi trả lời sai một cách tự tin.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Điền sau buổi demo.*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 9 / 10 |
| **Tổng phần cá nhân** | **/ 60** |
