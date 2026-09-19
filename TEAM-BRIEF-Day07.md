# Day 07 — Brief cho nhóm: nguồn dữ liệu & việc cần chốt

**Người viết:** Hoàng Quốc Việt (02563) · **Ngày:** 2026-09-19
**Repo cá nhân:** https://github.com/Catnip-harvest/K4A-Day07-02563-HoangQuocViet

File này chỉ để nhóm phối hợp, **không phải bài nộp**. Bài nộp là `src/`,
`report/REPORT_NHOM.md` (1 bản/nhóm) và `report/REPORT_CANHAN.md` (1 bản/người).

---

## 1. TL;DR

1. **Trang `tuyensinh.utc.edu.vn` KHÔNG dùng được** — thông tin ngành nằm trong ảnh JPEG, không có chữ để máy đọc. Đo cụ thể ở mục 3.
2. **Đã thay bằng `utc.edu.vn/gioi-thieu/<đơn-vị>`** — văn bản thật, đúng chủ đề L3A. Đã crawl xong **10 tài liệu / 31.212 ký tự**, nằm ở `data/dich-vu-sinh-vien-utc/`.
3. **Cảnh báo lớn:** chạy benchmark trên `MockEmbedder` mặc định sẽ cho kết quả ngẫu nhiên → mất gần hết 10 điểm Chất lượng truy xuất. Phải cài embedder thật. Chi tiết mục 5.
4. Nhóm cần chốt 3 thứ: **bộ tài liệu**, **5 câu hỏi + gold answer**, **ai dùng chiến lược chunking nào**. Mục 6.

---

## 2. Phần cá nhân — ai cũng phải tự làm

Không chia việc được, mỗi người tự code trong repo của mình (60/100 điểm).

| Việc | Điểm | Ghi chú |
|---|---|---|
| 13 TODO trong `src/chunking.py`, `src/store.py`, `src/agent.py` | 30 | Đạt khi `pytest tests/ -v` xanh **42/42** |
| `REPORT_CANHAN.md` mục "Hướng tiếp cận" | 10 | Giải thích code mình viết |
| Khởi động: cosine + bài toán chunking | 5 | Đáp án: 10.000 ký tự, size 500, overlap 50 → **23 chunk**; overlap 100 → **25 chunk** |
| Dự đoán độ tương tự 5 cặp câu | 5 | **Phải ghi dự đoán TRƯỚC khi chạy code** |
| Chạy 5 câu hỏi của nhóm trên code của mình | 10 | Dùng chung bộ câu hỏi với cả nhóm |

Mình đã xong phần code (42/42) và mục Khởi động + Hướng tiếp cận. Ai cần tham khảo
cách làm thì xem `report/REPORT_CANHAN.md` trong repo của mình — **nhưng đừng copy
nguyên**, vì mục "Hướng tiếp cận" chấm theo code của từng người.

---

## 3. Vì sao bỏ `tuyensinh.utc.edu.vn`

Đã thử crawl `https://tuyensinh.utc.edu.vn/?q=thong-tin-nganh-tuyen-sinh` và 5 trang ngành con.

| Trang | Text trích được | Kết luận |
|---|---|---|
| `nganh-tuyen-sinh/khoa-hoc-may-tinh` | 1.861 ký tự | = đúng bằng phần menu/footer của site |
| `nganh-tuyen-sinh/tri-tue-nhan-tao` | 1.866 | +5 ký tự so với trang rỗng |
| `nganh-tuyen-sinh/ky-thuat-may-tinh` | 1.868 | +7 |
| `nganh-tuyen-sinh/ky-thuat-o-to` | 1.860 | −1 |
| `nganh-tuyen-sinh/kinh-te-van-tai` | 1.870 | +9 |

Nội dung thật nằm trong ảnh: `KHMT 2026.jpg`, `KT MT(1).jpg`, `KTOT 1.jpg`…
Muốn dùng thì phải OCR — ngoài phạm vi lab, và `docs/DATA_COLLECTION.md` nói rõ
không dùng trang render bằng JS hay PDF/ảnh cho crawler mẫu.

Hai trang khác trên site có chữ thật nhưng vẫn không dùng được:
- `?q=hoi-dap` — chỉ có **câu hỏi của thí sinh, không có câu trả lời** → không rút được gold answer.
- `?q=tin-tuyen-sinh` — danh sách tin, không phải quy định.

`?q=de-an-tuyen-sinh` trả về **404**.

> Lưu ý nếu ai vẫn muốn crawl site này: `robots.txt` đặt `Crawl-delay: 10`, phải chờ 10 giây giữa các request.

---

## 4. Nguồn đã dùng thay thế

`https://www.utc.edu.vn/gioi-thieu/<đơn-vị>` — trang giới thiệu từng phòng/ban/trung tâm.
`robots.txt` chỉ chặn `/admin/` và `/tmp/`. Sitemap có 5.833 URL.

Đã crawl 10 trang bằng chính `scripts/fetch_public_pages.py` của lab (giãn cách 2 giây),
rồi làm sạch bằng `scripts/clean_utc_pages.py` (mình viết thêm).

| doc_id | audience | category | ký tự |
|---|---|---|---|
| `dao-tao-dai-hoc-hoc-vu` | student | hoc-vu | 3.759 |
| `cong-tac-sinh-vien` | student | cong-tac-sinh-vien | 2.733 |
| `ky-tuc-xa-quan-ly` | student | ky-tuc-xa | 2.231 |
| `tram-y-te` | student | y-te | 2.510 |
| `dao-tao-truc-tuyen` | student | hoc-truc-tuyen | 3.352 |
| `thu-vien-dich-vu` | all | thu-vien | 3.490 |
| `ke-hoach-tai-chinh-hoc-phi` | all | hoc-phi | 4.525 |
| `bao-ve-an-ninh` | all | an-ninh | 2.913 |
| `quan-ly-chat-luong` | staff | dam-bao-chat-luong | 2.973 |
| `phap-che-kiem-soat` | staff | phap-che | 2.726 |
| | | **Tổng** | **31.212** |

**`audience` có 3 giá trị** (student 5 / all 3 / staff 2) → `search_with_filter()` có việc
thật để làm, đúng yêu cầu của `K4_VARIANT.md` là ít nhất 1 câu hỏi cần
`metadata_filter={"audience": "student"}`.

Phần làm sạch đã bỏ: menu ~200 dòng, khối tin tức cuối trang, và **bảng danh sách cán bộ
kèm số điện thoại di động cá nhân** (lab cấm đưa dữ liệu cá nhân vào repo). Giữ lại địa chỉ,
số tổng đài và email đơn vị vì đó là thông tin của tổ chức và câu hỏi benchmark có thể hỏi tới.

### Hạn chế phải biết trước khi viết câu hỏi

Đây là trang **giới thiệu chức năng nhiệm vụ**, không phải văn bản quy định. Kiểm tra cả
10 file: **không có mốc thời hạn nào, gần như không có con số** — không có mức học phí,
không có hạn đăng ký, không có định mức mượn sách.

→ Gold answer phải dạng *"phòng nào phụ trách việc X, ở đâu, làm những gì"*,
**không** phải *"bao nhiêu tiền / hạn chót ngày nào"*.

Muốn có con số thì phải lấy từ `utc.edu.vn/van-ban-phap-qui` và
`utc.edu.vn/thong-tin-cong-khai` — nhưng hai trang đó chỉ là danh sách link tới **PDF**,
phải dùng `marker-pdf` hoặc `pymupdf4llm` chứ crawler không lấy được.

---

## 5. Cảnh báo kỹ thuật: MockEmbedder cho kết quả ngẫu nhiên

`MockEmbedder` mặc định là hàm băm **MD5**. Nó **không mang thông tin ngữ nghĩa nào**.
Đo trên chính repo:

| Cặp | Cosine |
|---|---|
| `"How do I register for courses?"` vs `"Course registration opens on the first Monday of August."` | **−0,1332** |
| `"How do I register for courses?"` vs `"Bananas are a good source of potassium."` | **−0,2260** |
| `"cat"` vs `"cats"` | **−0,0638** |
| `"cat"` vs `"dog"` | **+0,1607** |
| `"identical"` vs `"identical"` | **+1,0000** |

`"cat"` gần `"dog"` hơn cả `"cats"`. Chỉ trùng khớp chuỗi tuyệt đối mới cho 1.0.

**42 bài test thì vẫn xanh** — chúng chỉ kiểm tra hợp đồng của hàm, không kiểm tra chất lượng
ngữ nghĩa. Nhưng **10 điểm Chất lượng truy xuất sẽ gần như bằng 0** nếu benchmark chạy trên mock,
vì thứ tự top-3 chỉ là nhiễu.

Hai cách sửa, chọn một và **cả nhóm dùng chung** để so sánh giữa các thành viên còn ý nghĩa:

```bash
# A. Chạy cục bộ, miễn phí, không cần API key, tiếng Việt tốt.
#    Lần đầu tải vài GB (PyTorch). Chọn cái này nếu máy đủ dung lượng.
pip install -r requirements-local.txt

# B. Gemini free tier — nhẹ hơn nhiều, lấy key ở aistudio.google.com
pip install google-genai
export GEMINI_API_KEY=...
```

Rồi đặt trong `.env`: `EMBEDDING_PROVIDER=local` (hoặc `gemini`).

> **Không commit API key.** File `.env` đã nằm trong `.gitignore`, chỉ sửa `.env`, đừng sửa `.env.example`.

---

## 6. Ba thứ nhóm phải chốt

### 6.1 Bộ tài liệu
Dùng luôn 10 file ở `data/dich-vu-sinh-vien-utc/` hay bổ sung/đổi? Nếu đồng ý thì
copy nguyên thư mục đó sang repo của mỗi người — **phải giống hệt nhau**, nếu không
thì việc so sánh giữa các thành viên không còn cơ sở.

### 6.2 Năm câu hỏi + gold answer
Yêu cầu bắt buộc: đa dạng, kiểm chứng được từ corpus, và **ít nhất 1 câu phải cần
`metadata_filter={"audience": "student"}`** mới trả lời đúng.

Gợi ý dựa trên corpus hiện có (nhóm sửa lại cho hợp):

| # | Câu hỏi | Lấy từ | Cần filter? |
|---|---|---|---|
| 1 | Thư viện phục vụ những đối tượng bạn đọc nào? | `thu-vien-dich-vu` | không |
| 2 | Sinh viên nội trú liên hệ đơn vị nào? | `ky-tuc-xa-quan-ly` | có — `audience=student` |
| 3 | Phòng nào phụ trách học phí và các khoản thu? | `ke-hoach-tai-chinh-hoc-phi` | không |
| 4 | Trạm Y tế có mấy cơ sở và ở đâu? | `tram-y-te` | không |
| 5 | Tra cứu tài liệu thư viện trực tuyến ở địa chỉ nào? | `thu-vien-dich-vu` | không |

> Câu 2 là câu ăn điểm filter: cả 10 tài liệu đều có mục "CHỨC NĂNG NHIỆM VỤ" gần giống nhau,
> nên nếu không lọc `audience` thì top-3 rất dễ trả về nhầm phòng ban khác.

### 6.3 Chia chiến lược chunking — mỗi người một kiểu

`K4_VARIANT.md` bắt buộc **ít nhất một người chunk theo tiêu đề/mục**. Cả 10 tài liệu
đều có đúng 4 heading (`THÔNG TIN CHUNG`, `CHỨC NĂNG NHIỆM VỤ`, `GIỚI THIỆU`,
`CÁC THÀNH TÍCH ĐÃ ĐẠT ĐƯỢC`) nên chiến lược này rất hợp corpus này.

| Thành viên | Chiến lược đề xuất | Tham số |
|---|---|---|
| TV1 | `FixedSizeChunker` (đường cơ sở) | `chunk_size=500, overlap=50` |
| TV2 | `SentenceChunker` | `max_sentences_per_chunk=3` |
| TV3 | `RecursiveChunker` | `chunk_size=400` |
| TV4 (Việt) | `HeadingChunker` tự viết — cắt theo 4 heading | — |

Ai nhận ô nào thì nhắn lại trong nhóm để khỏi trùng.

---

## 7. Checklist trước khi nộp

- [ ] `pytest tests/ -v` → 42/42 (từng người)
- [ ] Cả nhóm dùng **cùng** bộ tài liệu, **cùng** 5 câu hỏi, **cùng** embedder
- [ ] Mỗi người một chiến lược chunking khác nhau, có 1 người chunk theo heading
- [ ] `REPORT_NHOM.md` — 1 bản, có bảng kiểm kê tài liệu + so sánh giữa các thành viên
- [ ] `REPORT_CANHAN.md` — mỗi người 1 bản
- [ ] Ít nhất 1 failure case được phân tích (Bài tập 3.5)
- [ ] Không có API key, không có dữ liệu cá nhân trong repo
