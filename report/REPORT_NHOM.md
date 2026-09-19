# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Logitech
**Thành viên:** Hoàng Quốc Việt (02563) · [Tên TV2] · [Tên TV3] · [Tên TV4]
**Ngày:** 2026-09-19

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

> **Tình trạng bản nháp:** mọi số trong báo cáo này là **kết quả chạy thật**, do Việt chạy trên
> cùng một máy, cùng một embedder, cùng một bộ tài liệu — chỉ đổi chiến lược chia nhỏ. Các thành
> viên khác chạy lại trên máy mình rồi thay số vào bảng "So sánh giữa các thành viên" để xác nhận.

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Dịch vụ và đơn vị hành chính dành cho sinh viên — Trường Đại học Giao thông vận tải (UTC).

**Tại sao nhóm chọn chủ đề này?**

> Đây là chủ đề bắt buộc của lớp L3A (dịch vụ/quy định đại học) và là thứ sinh viên hỏi thật:
> thư viện, ký túc xá, học phí, học vụ, y tế. Quan trọng hơn, nguồn công khai và có cấu trúc
> giống nhau giữa các trang, nên so sánh chiến lược chia nhỏ mới công bằng.
>
> **Nhóm đã phải đổi nguồn một lần.** Nguồn định dùng ban đầu là
> `tuyensinh.utc.edu.vn/?q=thong-tin-nganh-tuyen-sinh`, nhưng **không dùng được**: mọi trang ngành
> đều là ảnh JPEG. Đo trên 5 trang, text trích được là 1.860–1.870 ký tự và **đúng bằng phần
> menu/footer của một trang rỗng** — nội dung thật nằm trong `KHMT 2026.jpg`, `KT MT(1).jpg`…
> Trang `?q=hoi-dap` có chữ nhưng chỉ là câu hỏi của thí sinh, **không có câu trả lời**, nên không
> rút được gold answer. Nhóm chuyển sang `utc.edu.vn/gioi-thieu/<đơn-vị>`.

### Danh sách tài liệu (Data Inventory)

Nguồn: `https://www.utc.edu.vn/gioi-thieu/<đơn-vị>` · lấy ngày **2026-09-19** ·
`document_version: not-stated` (nguồn không nêu phiên bản — **không bịa số hiệu**).

| # | doc_id | Đơn vị | Số ký tự | audience | category |
|---|---|---|---|---|---|
| 1 | `dao-tao-dai-hoc-hoc-vu` | Phòng Đào tạo đại học | 3.759 | student | hoc-vu |
| 2 | `cong-tac-sinh-vien` | Phòng Chăm sóc người học | 2.733 | student | cong-tac-sinh-vien |
| 3 | `ky-tuc-xa-quan-ly` | Ban Quản lý Ký túc xá | 2.231 | student | ky-tuc-xa |
| 4 | `tram-y-te` | Trạm Y tế | 2.510 | student | y-te |
| 5 | `dao-tao-truc-tuyen` | TT Đào tạo trực tuyến UTC | 3.352 | student | hoc-truc-tuyen |
| 6 | `thu-vien-dich-vu` | TT Thông tin – Thư viện | 3.490 | all | thu-vien |
| 7 | `ke-hoach-tai-chinh-hoc-phi` | Phòng Kế hoạch – Tài chính | 4.525 | all | hoc-phi |
| 8 | `bao-ve-an-ninh` | Phòng Bảo vệ | 1.991 | all | an-ninh |
| 9 | `quan-ly-chat-luong` | Phòng Quản lý chất lượng | 2.973 | staff | dam-bao-chat-luong |
| 10 | `phap-che-kiem-soat` | Phòng Thanh tra – Pháp chế | 2.726 | staff | phap-che |
| | | **Tổng** | **30.290** | student 5 / all 3 / staff 2 | |

Bảng kiểm kê đầy đủ kèm `source_url` và `license_or_permission` nằm ở
`data/dich-vu-sinh-vien-utc/sources.csv`, khớp một-một với 10 file.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu chỉ chứa nguồn công khai. `robots.txt` của `utc.edu.vn` chỉ chặn `/admin/` và `/tmp/`; crawl giãn cách 2 giây bằng chính `scripts/fetch_public_pages.py` của lab.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` trong metadata.
- [x] **Đã lược bỏ dữ liệu cá nhân.** Các trang gốc có bảng danh sách cán bộ kèm số di động cá nhân; `scripts/clean_utc_pages.py` cắt toàn bộ bảng đó và redact số điện thoại. Giữ lại địa chỉ, tổng đài và email đơn vị vì đó là thông tin của tổ chức.
- [x] Đã bỏ menu (~200 dòng) và khối tin tức cuối trang.

### Cấu trúc Metadata (Metadata Schema)

| Trường | Kiểu | Ví dụ | Tại sao hữu ích cho truy xuất? |
|---|---|---|---|
| `doc_id` | string | `tram-y-te` | Khoá để gom chunk về tài liệu gốc; `delete_document()` dùng trường này |
| `title` | string | "Trạm Y tế: chăm sóc sức khỏe…" | Hiển thị nguồn khi agent trích dẫn |
| `source_url` | url | `.../gioi-thieu/tram-y-te` | Truy vết câu trả lời về trang gốc |
| `retrieved_at` | date | `2026-09-19` | Biết dữ liệu cũ bao lâu |
| `document_version` | string | `not-stated` | Chỗ để ghi ngày hiệu lực khi nguồn có nêu |
| **`audience`** | enum | `student` / `all` / `staff` | **Trường lọc chính.** 3 giá trị nên `search_with_filter()` có việc thật |
| `department` | slug | `tram-y-te` | Lọc theo đơn vị phụ trách |
| `category` | slug | `y-te`, `hoc-phi` | Lọc theo mảng dịch vụ |
| `language` | iso | `vi` | Dự phòng khi thêm tài liệu tiếng Anh |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

`ChunkingStrategyComparator().compare(text, chunk_size=500)` trên 3 tài liệu:

| Tài liệu | Chiến lược | Số chunk | Độ dài TB | Ngắn nhất | Dài nhất | Giữ được ngữ cảnh? |
|---|---|---|---|---|---|---|
| `ky-tuc-xa-quan-ly` (2.231) | `fixed_size` | 5 | 486,2 | 431 | 500 | Đều nhưng cắt giữa câu |
| | `by_sentences` | 4 | 556,25 | 260 | 999 | Tốt, nhưng chunk dài lệch nhau |
| | `recursive` | 8 | 277,0 | 105 | 500 | Tôn trọng ranh giới, chunk vụn |
| | `heading` | 4 | 556,25 | 79 | 1.117 | Trọn mục, nhưng lệch rất mạnh |
| `thu-vien-dich-vu` (3.490) | `fixed_size` | 8 | 480,0 | 340 | 500 | |
| | `by_sentences` | 7 | 496,14 | 349 | 932 | |
| | `recursive` | 9 | 386,0 | 168 | 485 | |
| | `heading` | 6 | 580,0 | 82 | 1.145 | |
| `dao-tao-dai-hoc-hoc-vu` (3.759) | `fixed_size` | 9 | 462,11 | 159 | 500 | |
| | `by_sentences` | 14 | 266,57 | 97 | 479 | Nhiều mục a) b) c) ngắn |
| | `recursive` | 10 | 374,1 | 140 | 464 | |
| | `heading` | 5 | 750,2 | 109 | 1.181 | |

**Nhận xét:** `fixed_size` cho phân bố đều nhất (min/max sát nhau). `heading` cho chunk trọn ý
nhất nhưng biến động lớn nhất — mục `THÔNG TIN CHUNG` chỉ ~80 ký tự trong khi `CHỨC NĂNG NHIỆM VỤ`
hơn 1.100. `by_sentences` phụ thuộc mạnh vào cách viết: trang học vụ viết thành mục a) b) c) nên
ra 14 chunk ngắn, trang ký túc xá viết văn xuôi dài nên ra 4 chunk rất dài.

### Chiến lược của từng thành viên

**Thành viên 1 — Hoàng Quốc Việt (02563)**
- **Loại chiến lược:** `FixedSizeChunker(chunk_size=500, overlap=50)`
- **Mô tả & lý do:** Chọn làm **đường cơ sở có chủ đích**, không phải vì lười. Corpus này gồm
  10 trang cùng khuôn mẫu, độ dài chênh nhau gấp đôi; chia đều theo ký tự cho phân bố chunk ổn
  định nhất (min 340–431, max 500 trên cả ba tài liệu đo thử), nên mọi chiến lược khác được so
  với một mốc không thiên vị tài liệu nào. Overlap 50 để câu vắt qua ranh giới vẫn xuất hiện
  nguyên vẹn ở ít nhất một chunk.
- **Kết quả:** **hit@3 = 5/5**, 70 chunk.

**Thành viên 2 — [Tên]**
- **Loại chiến lược:** `SentenceChunker(max_sentences_per_chunk=3)` → `--strategy sentence`
- **Mô tả & lý do:** *(điền)*
- **Kết quả (Việt chạy thử):** hit@3 = 4/5, 64 chunk.

**Thành viên 3 — [Tên]**
- **Loại chiến lược:** `RecursiveChunker(chunk_size=400)` → `--strategy recursive`
- **Mô tả & lý do:** *(điền)*
- **Kết quả (Việt chạy thử):** hit@3 = 5/5, 105 chunk.

**Thành viên 4 — [Tên]**
- **Loại chiến lược:** `HeadingChunker(max_chars=1200)` — cắt theo tiêu đề, **thoả yêu cầu bắt buộc của `K4_VARIANT.md`**
- **Mô tả & lý do:** Cả 10 tài liệu đều dùng đúng 4 heading viết hoa (`THÔNG TIN CHUNG`,
  `CHỨC NĂNG NHIỆM VỤ`, `GIỚI THIỆU`, `CÁC THÀNH TÍCH ĐÃ ĐẠT ĐƯỢC`), nên cắt theo heading đặt
  trọn một chủ đề vào một chunk thay vì cắt ngang danh sách nhiệm vụ.
- **Code:** đã có sẵn trong `scripts/run_benchmark.py`, chạy `--strategy heading`.

```python
class HeadingChunker:
    """Cắt theo chính các heading của tài liệu; mục nào quá dài thì đệ quy tiếp."""

    def __init__(self, max_chars: int = 1200) -> None:
        self.max_chars = max_chars
        self._fallback = RecursiveChunker(chunk_size=max_chars)

    def chunk(self, text: str) -> list[str]:
        sections = [p.strip() for p in HEADING.split(text) if p.strip()]
        chunks = []
        for section in sections:
            chunks.extend([section] if len(section) <= self.max_chars
                          else self._fallback.chunk(section))
        return chunks
```

- **Kết quả (Việt chạy thử):** hit@3 = 5/5, 49 chunk.

### So Sánh Giữa Các Thành Viên

Cùng 10 tài liệu, cùng 5 câu hỏi, cùng embedder
(`paraphrase-multilingual-MiniLM-L12-v2`, 384 chiều). Chỉ đổi chiến lược.

| Chiến lược | Số chunk | hit@3 | Điểm rubric | Điểm mạnh | Điểm yếu |
|---|---|---|---|---|---|
| **Fixed size** (Việt) | 70 | **5/5** | 9/10 | Phân bố đều, ổn định trên mọi tài liệu | Cắt giữa câu; Q4 vẫn sai |
| By sentence | 64 | 4/5 | 7/10 | Chunk đọc được như văn xuôi | **Trượt hẳn Q4** — tài liệu đúng rơi khỏi top-3 |
| Recursive | 105 | **5/5** | 9/10 | Tôn trọng ranh giới ngữ nghĩa | Sinh chunk vụn (có chunk 5 ký tự) |
| By heading | 49 | **5/5** | 9/10 | **Ít chunk nhất mà vẫn 5/5** — hiệu quả lưu trữ tốt nhất | Chunk lệch mạnh (79 → 1.181 ký tự) |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

> **`HeadingChunker`, nhưng khoảng cách nhỏ hơn nhiều so với kỳ vọng.** Nó đạt 5/5 với chỉ
> **49 chunk** — ít hơn `recursive` 53% mà kết quả ngang nhau, nghĩa là chi phí embedding và lưu
> trữ thấp hơn một nửa cho cùng chất lượng. Nó hợp corpus này vì corpus **có cấu trúc heading
> nhất quán**; trên tập tài liệu viết tự do thì lợi thế đó biến mất.
>
> Phát hiện đáng giá hơn là: **ba trong bốn chiến lược đạt 5/5, và cả bốn đều sai câu 4.**
> Khi mọi chiến lược đều đúng gần hết, chiến lược chia nhỏ **không còn là biến quyết định** —
> thứ quyết định là chất lượng dữ liệu và metadata (xem mục 3).
>
> `by_sentences` là chiến lược duy nhất tụt hạng, và lý do cụ thể: nó cắt theo dấu câu, mà trang
> ký túc xá viết văn xuôi dài dòng nên sinh chunk tới 999 ký tự — tín hiệu của câu trả lời đúng
> bị pha loãng trong một chunk quá lớn.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

Bản máy đọc được: `benchmark/queries.json`. Mọi thành viên chạy đúng bộ này.

| # | Câu hỏi | Câu trả lời chuẩn | Chunk chứa thông tin |
|---|---|---|---|
| 1 | Ký túc xá của trường có bao nhiêu phòng và sức chứa bao nhiêu sinh viên? | 03 khối nhà 4–5 tầng, **214 phòng** khép kín, sức chứa **1.500 sinh viên** | `ky-tuc-xa-quan-ly` |
| 2 | Sinh viên muốn hỏi về học bổng và vay vốn tín dụng đào tạo thì liên hệ đơn vị nào? | Phòng Chăm sóc người học (vay vốn, học bổng tài trợ / ngoài ngân sách); **học bổng khuyến khích học tập** do Phòng Đào tạo đại học chủ trì xét | `cong-tac-sinh-vien` + `dao-tao-dai-hoc-hoc-vu` |
| 3 | Đơn vị nào tham mưu cho Hiệu trưởng về công tác chăm sóc sức khỏe cho sinh viên? | Trạm Y tế — 2 cơ sở, 04 cán bộ y tế; sau QĐ 2109 thuộc Phòng Chăm sóc người học | `tram-y-te` + `cong-tac-sinh-vien` |
| 4 | Ai quản lý ký túc xá của trường? | Phòng Chăm sóc người học, theo **QĐ 2109/QĐ-ĐHGTVT** sáp nhập Phòng CTCT&SV + Ban QL KTX + Trạm Y tế | `cong-tac-sinh-vien` |
| 5 | Tra cứu tài liệu thư viện trực tuyến ở địa chỉ nào và thư viện phục vụ những đối tượng bạn đọc nào? | OPAC tại `http://opac.utc.edu.vn`; bạn đọc gồm giảng viên, cán bộ nghiên cứu, NCS, học viên cao học và sinh viên trong và ngoài Trường | `thu-vien-dich-vu` |

**Câu 3 là câu bắt buộc phải lọc metadata** (`metadata_filter={"audience": "student"}`).

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (`docs/SCORING.md`): **2 điểm/câu** — top-3 có chunk liên quan + agent trả lời đúng (2);
> có liên quan nhưng thiếu chi tiết hoặc không ở top-1 (1); không có trong top-3 (0).

| # | Fixed | Sentence | Recursive | Heading | Điểm | Ghi chú |
|---|---|---|---|---|---|---|
| 1 | ✅ +0,7358 | ✅ +0,6300 | ✅ +0,7769 | ✅ +0,8003 | **2** | Mọi chiến lược đều top-1 đúng |
| 2 | ✅ +0,6330 | ✅ +0,7709 | ✅ +0,6759 | ✅ +0,5823 | **2** | Top-3 gom được cả hai phòng |
| 3 | ✅ +0,7232 | ✅ +0,7473 | ✅ +0,8055 | ✅ +0,7806 | **2** | Có lọc `audience=student` |
| 4 | ⚠️ hạng 3 | ❌ ngoài top-3 | ⚠️ trong top-3 | ⚠️ trong top-3 | **1** | **Tài liệu cũ thắng ở mọi chiến lược** |
| 5 | ✅ +0,6550 | ✅ +0,6468 | ✅ +0,6728 | ✅ +0,6938 | **2** | Cả 3 chunk top đều đúng tài liệu |
| | | | | | **9 / 10** | (chiến lược fixed của Việt) |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

> **Có, và đo được ở câu 3.** Cụm *"tham mưu cho Hiệu trưởng"* xuất hiện trong **8 / 10** tài liệu
> vì mọi trang đơn vị đều mở đầu y hệt nhau. Không lọc thì top-3 dễ toàn phần mở đầu của các
> phòng không liên quan. Đặt `metadata_filter={"audience": "student"}` loại 5 tài liệu
> `all`/`staff` trước khi chấm điểm, và top-3 trở thành `tram-y-te` (+0,7232), `tram-y-te`
> (+0,6896), `cong-tac-sinh-vien` (+0,6807) — sạch.
>
> Điểm thiết kế đáng nói: `search_with_filter()` **lọc trước rồi mới chấm điểm**. Nếu chấm trước
> rồi lọc sau thì `top_k` bị tiêu vào những chunk sắp bị vứt đi, và câu trả lời sẽ thiếu kết quả
> dù trong kho vẫn còn chunk hợp lệ.
>
> **Nhưng metadata hiện tại không cứu được câu 4** — vì cả hai tài liệu mâu thuẫn đều là
> `audience: student`. Cần thêm trường hiệu lực, xem mục 4.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích hay nhất nhóm sẽ trình bày:**

1. **Nguồn nhìn thì công khai, crawl ra thì rỗng.** Trang tuyển sinh của UTC trông đầy đủ với
   người đọc nhưng cho **0 ký tự** nội dung máy đọc được — thông tin ngành nằm trong ảnh JPEG.
   Bài học: luôn đo lượng text trích được *trước khi* chốt nguồn, đừng tin mắt nhìn.
2. **Câu 4 — hai câu trả lời chính thức mâu thuẫn nhau trong cùng một kho.** Trang Ban Quản lý
   KTX (QĐ 390, 1981) và trang Phòng Chăm sóc người học (QĐ 2109, ghi rõ đã sáp nhập Ban QL KTX)
   đều đang nằm trên website trường, đều crawl cùng một ngày. Agent trả lời **sai với score
   0,789** — rất tự tin. Và **không chiến lược chunking nào sửa được**: cả bốn đều đặt trang cũ
   lên hạng 1.
3. **Khi mọi chiến lược đều tốt, chiến lược hết là biến quyết định.** 3/4 chiến lược đạt 5/5.
   Khác biệt thật nằm ở chi phí (`heading` 49 chunk vs `recursive` 105 chunk cho cùng kết quả)
   và ở chất lượng dữ liệu, không nằm ở cách cắt.

**Bài học rút ra khi so sánh trong nhóm:**

> Cùng tài liệu, cùng câu hỏi, cùng embedder — chênh lệch giữa bốn chiến lược chỉ là **1 câu trên 5**.
> Điều đó nói rằng với corpus sạch và có cấu trúc, việc tinh chỉnh chunking cho lợi ích giảm dần rất
> nhanh. Thời gian bỏ vào làm sạch dữ liệu và thiết kế metadata đem lại nhiều hơn hẳn thời gian bỏ
> vào dò `chunk_size`. Trường hợp `by_sentences` trượt câu 4 cũng cho thấy chiến lược nào **phụ
> thuộc vào văn phong của nguồn** thì rủi ro hơn chiến lược không phụ thuộc.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu?**

> Thêm **trường hiệu lực** vào metadata ngay từ khi nạp, và dùng nó khi xếp hạng chứ không chỉ để lọc:
>
> ```yaml
> document_version: "1981-10-24"
> superseded_by: cong-tac-sinh-vien    # QĐ 2109/QĐ-ĐHGTVT
> status: superseded                   # active | superseded
> ```
>
> Chi phí một trường metadata; đổi lại câu 4 từ 1 lên 2 điểm và agent thôi trích dẫn tài liệu hết
> hiệu lực. Ngoài ra nhóm sẽ bổ sung vài văn bản có **con số và mốc thời gian** (mức học phí, hạn
> đăng ký) — corpus hiện tại là trang mô tả chức năng nhiệm vụ nên không trả lời được câu hỏi dạng
> "bao nhiêu tiền / hạn chót ngày nào".

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 14 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 9 / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
