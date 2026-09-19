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

**Cấu hình:** `LocalEmbedder` — `paraphrase-multilingual-MiniLM-L12-v2`, 384 chiều ·
chiến lược **`FixedSizeChunker(chunk_size=400, overlap=50)`** · 10 tài liệu → **90 chunk**,
độ dài trung bình 381 ký tự. Chạy bằng `python bench.py` (harness chung của nhóm);
kết quả đầy đủ lưu ở `ket_qua_benchmark.txt`.

### Hai cách chấm cho cùng một lần chạy

Nhóm chấm ở **hai mức**, và đây là phát hiện đáng giá nhất của phần cá nhân:

| # | Câu hỏi | Top-1 | Score | Tài liệu gold trong top-3? | Chuỗi đáp án có trong ngữ cảnh? | Điểm |
|---|---|---|---|---|---|---|
| 1 | Ký túc xá có bao nhiêu phòng, sức chứa bao nhiêu SV? | `ky-tuc-xa-quan-ly` | +0,789 | ✅ | `214 phòng` ✅ · `1500 sinh viên` ✅ | **2/2** |
| 2 | Học bổng và vay vốn tín dụng thì liên hệ đâu? | `cong-tac-sinh-vien` | +0,694 | ✅ | `vay vốn tín dụng đào tạo` ❌ · `học bổng khuyến khích học tập` ✅ | **0/2** |
| 3 | Đơn vị nào tổ chức thi và đánh giá kết quả học tập? | `dao-tao-dai-hoc-hoc-vu` | +0,720 | ✅ | `đánh giá kết quả học tập của sinh viên` ✅ | **2/2** |
| 4 | Ai quản lý ký túc xá? | `ky-tuc-xa-quan-ly` | +0,759 | ✅ | `sáp nhập lại Phòng CTCT&SV` ❌ | **0/2** |
| 5 | Tra cứu thư viện online ở đâu, phục vụ ai? | `thu-vien-dich-vu` | +0,702 | ✅ | `opac.utc.edu.vn` ✅ · `trong và ngoài Trường` ❌ | **0/2** |

- **Chấm theo `doc_id` (ngây thơ): 5/5** — câu nào cũng lôi được đúng tài liệu vào top-3.
- **Chấm theo nội dung: 4/10** — nhưng chỉ 2 câu thực sự chứa đủ câu chữ để trả lời.

**Chênh lệch 5/5 so với 4/10 chính là bài học.** Chấm theo `doc_id` khen quá tay: nó chỉ
hỏi *"có lấy đúng tài liệu không"*, trong khi cái mà người dùng cần là *"đoạn văn bản lấy về
có chứa câu trả lời không"*. Ba câu 2, 4, 5 đều lấy **đúng tài liệu nhưng sai chunk**.

### Câu 3 — bằng chứng đo được cho việc lọc metadata

Đây là câu bắt buộc phải lọc, và nó cho một cặp A/B sạch trên cùng một lần chạy:

| | Top-1 | Điểm |
|---|---|---|
| **A — không lọc** | `quan-ly-chat-luong` (+0,744) — Phòng Quản lý chất lượng, `audience: staff` | **1/2** |
| **B — lọc `audience=student`** | `dao-tao-dai-hoc-hoc-vu` (+0,720) | **2/2** |

Không lọc thì embedding chọn Phòng Quản lý chất lượng, vì trang đó ghi đúng cụm *"Chủ trì tổ
chức các kỳ thi nội bộ và công tác đánh giá kết quả học tập"* — về mặt ngữ nghĩa nó **không sai**.
Nhưng câu hỏi là của sinh viên, nên tài liệu `audience: student` mới là cái cần. Một trường
metadata làm được việc mà không tham số chunking nào làm được.

> Lưu ý: hiệu ứng này **phụ thuộc kích thước chunk**. Đo lại ở `chunk_size=500` thì A đã đạt
> 2/2 sẵn, tức là cặp A/B biến mất — chunk to hơn vô tình nuốt luôn câu trả lời. Đây là lý do
> tôi chốt **400** thay vì 500.

### Phân tích lỗi (Bài tập 3.5)

**Lỗi 1 — câu 4: tài liệu cũ đè tài liệu mới.**
Kho chứa **hai câu trả lời chính thức mâu thuẫn nhau**, cùng crawl một ngày từ website đang chạy:

- `cong-tac-sinh-vien.md` — *"Phòng Chăm sóc người học được thành lập theo Quyết định số
  2109/QĐ-ĐHGTVT trên cơ sở sắp xếp, **sáp nhập lại Phòng CTCT&SV, Ban Quản lý KTX, Trạm Y tế**"*
- `ky-tuc-xa-quan-ly.md` — vẫn tự mô tả là đơn vị đang hoạt động (QĐ 390/QĐ-TC, 1981)

Trang cũ thắng hạng 1 với **+0,759**. Tệ hơn: tài liệu đúng *có* vào top-3, nhưng **chunk lấy
về lại là đoạn nói về "quản lý sinh viên nội trú", không phải câu nói về sáp nhập** — nên chấm
theo `doc_id` thì "đạt", chấm theo nội dung thì 0.

Đã kiểm chứng trên cả bốn chiến lược: **không cách chia nhỏ nào sửa được.** `by_sentences` còn
tệ hơn — tài liệu đúng rơi hẳn khỏi top-3.

**Lỗi 2 — câu 2 và 5: câu trả lời bị chia đôi qua hai chunk.**
Câu 2 cần hai thông tin nằm ở **hai tài liệu khác nhau**; câu 5 cần hai thông tin nằm ở **hai
chunk khác nhau của cùng một tài liệu** (địa chỉ OPAC và danh sách đối tượng bạn đọc). Với
`top_k=3` và chunk 400 ký tự, kho không gom đủ. Đo thử với `SentenceChunker` (chunk trung bình
471 ký tự) thì câu 5 **đạt 2/2** — chunk to hơn giữ được cả hai vế.

**Lỗi 3 — 116 ký tự vô hình làm hỏng phép so khớp.**
Lần chạy đầu, câu 5 trượt cả `trong và ngoài Trường` dù tài liệu ghi đúng hệt như vậy. Nguyên
nhân là **`U+00A0` NO-BREAK SPACE** (từ `&nbsp;` trong HTML gốc) nằm giữa "ngoài" và "Trường" —
mắt thường không thấy, nhưng với máy thì đó không phải dấu cách. Toàn corpus có **116 ký tự
như vậy trên 8/10 tài liệu**. Chúng còn âm thầm phá `RecursiveChunker`, vì danh sách separator
của nó chứa dấu cách thường nên không cắt được chỗ bị NBSP dính liền.
Đã sửa trong `scripts/clean_utc_pages.py` và chuẩn hoá lại corpus.

**Đề xuất cải thiện, theo thứ tự ưu tiên:**

1. **Thêm trường hiệu lực vào metadata** và dùng khi xếp hạng, không chỉ để lọc — sửa được lỗi 1:
   ```yaml
   document_version: "1981-10-24"
   superseded_by: cong-tac-sinh-vien    # QĐ 2109/QĐ-ĐHGTVT
   status: superseded                   # active | superseded
   ```
2. **Tăng `top_k` từ 3 lên 5**, hoặc gom các chunk cùng `doc_id` trước khi dựng ngữ cảnh — sửa lỗi 2.
3. **Chuẩn hoá Unicode ngay khi nạp dữ liệu**, không đợi đến lúc phát hiện — lỗi 3 mất gần một
   lượt chạy mới tìm ra, và nó hoàn toàn vô hình khi đọc file.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Điền sau buổi demo.*

---

## 6. Những khó khăn đã gặp và cách xử lý (Phản ngẫm)

> `exercises.md` (Bài tập 3.5) yêu cầu ghi phân tích lỗi vào *"Báo cáo — Phần 7 (Những gì
> tôi học được)"*, nhưng mẫu `REPORT_CANHAN.md` chỉ đánh số đến Phần 5. Phần 6 này chính là
> phần đó; phân tích lỗi chi tiết của 5 câu benchmark nằm ở cuối Phần 5.

Phần này ghi lại các vấn đề **thực sự** đã cản đường, vì phần lớn thời gian của lab không nằm ở
việc viết 13 hàm TODO mà nằm ở những chỗ dưới đây.

**1. Nguồn dữ liệu đầu tiên chọn sai — mất công crawl rồi phải bỏ.**
Nhóm định dùng `tuyensinh.utc.edu.vn/?q=thong-tin-nganh-tuyen-sinh`. Trang mở ra nhìn đầy đủ
thông tin ngành. Nhưng crawl xong thì mỗi trang chỉ cho ~1.860 ký tự, và con số đó **đúng bằng
phần menu + footer của một trang rỗng** — toàn bộ nội dung thật nằm trong ảnh JPEG
(`KHMT 2026.jpg`, `KT MT(1).jpg`…). Trang `?q=hoi-dap` có chữ thật nhưng chỉ là câu hỏi của thí
sinh, không có câu trả lời nào.
*Bài học:* phải **đo số ký tự trích được** trước khi chốt nguồn, không tin vào việc "mở ra thấy
có chữ". Cách kiểm tra rẻ nhất: crawl 1 trang, so độ dài text với một trang chắc chắn rỗng của
cùng site — bằng nhau thì trang đó là ảnh.

**2. Chạy benchmark trên `MockEmbedder` suốt một thời gian dài mà kết quả vô nghĩa.**
42 test vẫn xanh nên rất dễ tưởng mọi thứ ổn. Nhưng `MockEmbedder` băm MD5, không mang ngữ nghĩa:
đo thử thì `"cat"` gần `"dog"` (+0,1607) hơn cả `"cats"` (−0,0638), và câu hỏi về đăng ký học phần
gần câu về **chuối** hơn gần chính câu trả lời của nó.
*Bài học:* bộ test chỉ kiểm tra **hợp đồng của hàm**, không kiểm tra chất lượng ngữ nghĩa. Xanh
42/42 không có nghĩa là hệ thống truy xuất đúng. Sau khi chuyển sang embedder thật, cùng cặp câu
đó cho +0,9337 và +0,3033 — đúng thứ tự.

**3. Windows Application Control chặn một file `.dll` của `scikit-learn`.**
Cài xong `sentence-transformers` thì import lỗi:
`DLL load failed while importing _expected_mutual_info_fast: An Application Control policy has
blocked this file`. Thoạt nhìn tưởng thiếu thư viện hoặc hỏng cài đặt.
*Cách xử lý:* thử import từng gói một mới thấy `torch`, `scipy`, `transformers` và cả `sklearn`
đều bình thường — **chỉ đúng một module bị chặn**, và `sentence-transformers` chỉ gọi nó gián
tiếp. Hạ `scikit-learn` xuống bản 1.7.2 là chạy được. **Không tắt Application Control** — đó là
thiết lập bảo mật của máy, tắt đi để chữa một lỗi thư viện là đánh đổi sai.

**4. Dung lượng ổ đĩa — chỉ còn 8 GB.**
Cài `sentence-transformers` theo mặc định sẽ kéo theo bản `torch` có CUDA (~2,5 GB) mà lab không
dùng tới, vì corpus chỉ có 10 tài liệu và chạy CPU là đủ.
*Cách xử lý:* cài `torch` bản CPU riêng trước bằng
`pip install torch --index-url https://download.pytorch.org/whl/cpu` (~600 MB), rồi mới cài
`sentence-transformers`. Tổng chi phí còn ~1,4 GB kể cả model.

**5. 116 ký tự vô hình phá phép so khớp chuỗi — mất lâu nhất để tìm ra.**
Benchmark báo trượt chuỗi `trong và ngoài Trường` trong khi mở file ra đọc thì thấy đúng y hệt.
Grep cũng không ra. Phải in mã Unicode từng ký tự mới thấy giữa "ngoài" và "Trường" là
**`U+00A0` NO-BREAK SPACE**, sinh ra từ `&nbsp;` trong HTML gốc. Toàn corpus có 116 ký tự như vậy
trên 8/10 tài liệu, và chúng còn âm thầm phá `RecursiveChunker` (separator của nó là dấu cách
thường nên không cắt được chỗ bị NBSP dính liền).
*Bài học:* dữ liệu crawl từ HTML **phải chuẩn hoá Unicode ngay khi nạp**, không đợi đến lúc có
lỗi lạ. Khi một phép so khớp thất bại mà mắt nhìn thấy đúng, nghi ngờ ký tự vô hình trước tiên —
cách kiểm tra là in `repr()` hoặc mã codepoint chứ không phải nhìn lại lần nữa.

**6. Hai cách chấm cho cùng một kết quả, chênh nhau rất xa.**
Chấm theo `doc_id` cho **5/5**; chấm theo nội dung cho **4/10**. Ban đầu tôi chỉ chấm theo `doc_id`
và tưởng kết quả gần như hoàn hảo.
*Bài học:* "lấy đúng tài liệu" và "lấy được đoạn chứa câu trả lời" là hai việc khác nhau. Ba trong
năm câu lấy **đúng tài liệu nhưng sai chunk**. Chỉ số nào dễ đạt thì thường là chỉ số đo sai thứ
mình quan tâm.

**7. Dữ liệu cá nhân suýt lọt vào repo.**
Các trang giới thiệu đơn vị có bảng danh sách cán bộ kèm **số điện thoại di động cá nhân**. Bước
làm sạch đầu tiên bỏ sót trang Phòng Bảo vệ vì heading của trang đó bị gõ sai thành
`ĐỘI NGŨ CÁN B=Ộ CHUYÊN VIÊN` (có dấu `=` thừa), nên khớp chuỗi chính xác không bắt được.
*Cách xử lý:* neo vào tiêu đề cột `Họ tên` — thứ xuất hiện ở mọi bảng và không xuất hiện trong
văn xuôi — thay vì neo vào dòng tiêu đề mục. Giữ lại địa chỉ, số tổng đài và email đơn vị vì đó
là thông tin của tổ chức, không phải của cá nhân.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 4 / 10 (chấm nội dung) · 5/5 (chấm doc_id) |
| **Tổng phần cá nhân** | **/ 60** |
