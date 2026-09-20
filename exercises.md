# Ngày 7 — Bài tập
## Nền tảng Dữ liệu: Embedding & Vector Store | Bài tập thực hành

---

## Phần 1 — Khởi động (Cá nhân)

### Bài tập 1.1 — Cosine Similarity (Độ tương tự Cosine) bằng ngôn ngữ đời thường

Không yêu cầu toán học — hãy giải thích về mặt khái niệm:

- Điều gì xảy ra khi hai đoạn văn bản có độ tương tự cosine cao?
- Đưa ra một ví dụ cụ thể về hai câu sẽ có độ tương tự CAO và hai câu sẽ có độ tương tự THẤP.
- Tại sao độ tương tự cosine lại được ưu tiên hơn khoảng cách Euclid (Euclidean distance) đối với text embeddings?

> **Ghi kết quả vào:** Báo cáo — Phần 1 (Khởi động)
+  Khi hai đoạn văn bản có độ tương tự cosine cao, điều đó có nghĩa là các vector biểu diễn của chúng hướng về cùng một phía trong không gian nhiều chiều . Nói cách khác, dù nội dung có thể dùng từ ngữ khác nhau, chúng vẫn mang ý nghĩa tương đồng hoặc cùng một chủ đề 
+ Độ tương tự CAO: "Chính sách hoàn tiền" và "Quy định đổi trả" (dù dùng từ khác nhau nhưng máy tính hiểu chúng cùng nằm trong cụm chủ đề hỗ trợ khách hàng)
Độ tương tự THẤP: "Chính sách hoàn tiền" và "Thời tiết hôm nay" (hai khái niệm không liên quan nên hướng của vector sẽ khác xa nhau)
+ Khoảng cách Euclid (Euclidean distance) đo khoảng cách đường chim bay, nó bị ảnh hưởng bởi độ lớn (độ dài) của vector . Trong văn bản, một đoạn văn dài có thể có số lượng từ nhiều hơn làm vector "dài hơn" một đoạn ngắn, dù cả hai nói về cùng một chủ đề.
Cosine similarity chỉ tập trung vào hướng (góc giữa hai vector) và triệt tiêu yếu tố độ dài . Điều này giúp hệ thống so sánh nghĩa của văn bản chính xác hơn mà không bị "nhiễu" bởi độ dài ngắn của đoạn văn . Ngoài ra, hầu hết các embedding model hiện đại đều trả về vector đã được chuẩn hóa về độ dài bằng 1, khi đó cosine thường là lựa chọn mặc định .
---

### Bài tập 1.2 — Bài toán tính toán Chunking

- Một tài liệu có độ dài 10,000 ký tự. Bạn tiến hành chia nhỏ (chunk) với `chunk_size=500` (kích thước chunk), `overlap=50` (độ chồng chéo). Bạn dự kiến sẽ có bao nhiêu chunks?
- Công thức: `số lượng chunk = làm_tròn_lên((độ_dài_tài_liệu - độ_chồng_chéo) / (kích_thước_chunk - độ_chồng_chéo))`
- Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk sẽ thay đổi như thế nào? Tại sao bạn lại muốn tăng độ chồng chéo?

> **Ghi kết quả vào:** Báo cáo — Phần 1 (Khởi động)
Công thức (overlap=50): 23 chunks
Thực tế (overlap=50): 23 chunks
Công thức (overlap=100): 25 chunks
---

## Phần 2 — Lập trình cốt lõi (Cá nhân)

Hoàn thành tất cả các TODOs trong `src/chunking.py`, `src/store.py`, và `src/agent.py`. `Document` dataclass và `FixedSizeChunker` đã được triển khai sẵn làm ví dụ — hãy đọc kỹ để hiểu cấu trúc trước khi lập trình phần còn lại.

Chạy `pytest tests/` để kiểm tra tiến độ.

### Danh sách cần làm (Checklist)
- [x] `Document` dataclass — ĐÃ TRIỂN KHAI SẴN
- [x] `FixedSizeChunker` — ĐÃ TRIỂN KHAI SẴN
- [x] `SentenceChunker` — tách dựa trên ranh giới câu, nhóm lại thành các chunks ✅
- [x] `RecursiveChunker` — thử nghiệm các dấu phân cách (separators) theo thứ tự, thực hiện đệ quy trên các đoạn có kích thước quá lớn ✅
- [x] `compute_similarity` — công thức tính độ tương tự cosine kèm cơ chế bảo vệ chia cho 0 ✅
- [x] `ChunkingStrategyComparator` — gọi cả ba chiến lược, tính toán các chỉ số thống kê ✅
- [x] `EmbeddingStore.__init__` — khởi tạo store (lưu trữ trong bộ nhớ) ✅
- [x] `EmbeddingStore.add_documents` — nhúng (embed) và lưu trữ từng tài liệu ✅
- [x] `EmbeddingStore.search` — nhúng truy vấn, xếp hạng theo tích vô hướng (dot product) ✅
- [x] `EmbeddingStore.get_collection_size` — trả về số lượng ✅
- [x] `EmbeddingStore.search_with_filter` — lọc theo siêu dữ liệu (metadata), sau đó tìm kiếm ✅
- [x] `EmbeddingStore.delete_document` — xóa tất cả các chunks của một doc_id ✅
- [x] `KnowledgeBaseAgent.answer` — truy xuất (retrieve) + tạo prompt + gọi LLM ✅
- [x] **BONUS:** `HierarchicalChunker` — split theo Markdown headings ✅
- [x] **BONUS:** `MixedHierarchicalRecursiveChunker` — hybrid approach ✅
- [x] **BONUS:** `SmartMockEmbedder` — keyword-based embedding (improved from hash) ✅

> **Nộp code:** thư mục `src/`
> **Ghi lại hướng tiếp cận vào:** Báo cáo — Phần 4 (Hướng tiếp cận của tôi)

---

## Phần 3 — So Sánh Chiến Lược Truy Xuất (Nhóm)

### Bài tập 3.0 — Chuẩn Bị Tài Liệu (Giờ đầu tiên)

Mỗi nhóm chọn một chủ đề (domain) và chuẩn bị bộ tài liệu:

**Bước 1 — Chọn chủ đề:** FAQ (Câu hỏi thường gặp), SOP (Quy trình chuẩn), chính sách, tài liệu kỹ thuật, công thức nấu ăn, luật, y tế, v.v.

**Bước 2 — Thu thập 5-10 tài liệu.** Chỉ dùng nguồn công khai hoặc nguồn nhóm có quyền sử dụng; lưu dưới dạng `.txt` hoặc `.md` vào thư mục `data/`.

**Quy tắc dữ liệu bắt buộc:**
- Không đưa dữ liệu cá nhân, thông tin đăng nhập, hồ sơ nội bộ hoặc nội dung có quyền sử dụng không rõ ràng vào repo.
- Với mỗi tài liệu, ghi `source_url`, `retrieved_at` (ngày lấy) và `document_version` hoặc ngày hiệu lực nếu nguồn có nêu.
- Đưa ba trường trên vào siêu dữ liệu (metadata) khi nạp (ingest); chúng giúp kiểm tra độ mới và truy vết câu trả lời.

> **Mẹo chuyển PDF sang Markdown:**
> - `pip install marker-pdf` → `marker_single input.pdf output/` (chất lượng cao, giữ cấu trúc)
> - `pip install pymupdf4llm` → `pymupdf4llm.to_markdown("input.pdf")` (nhanh, đơn giản)
> - Hoặc sao chép-dán (copy-paste) nội dung từ PDF/web vào file `.txt`

Ghi vào bảng:

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bước 3 — Thiết kế cấu trúc metadata (metadata schema):** Mỗi tài liệu cần `source_url`, `retrieved_at`, `document_version` và ít nhất 2 trường hữu ích cho việc truy xuất (ví dụ: `audience`, `department`, `category`, `language`, `difficulty`).

> **Ghi kết quả vào:** Báo cáo — Phần 2 (Lựa chọn tài liệu)

---

### Bài tập 3.1 — Thiết Kế Chiến Lược Truy Xuất (Mỗi người thử riêng)

Mỗi thành viên **tự chọn chiến lược riêng** để thử nghiệm trên cùng bộ tài liệu của nhóm.

**Bước 1 — Đường cơ sở (Baseline):** Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu. Ghi lại kết quả.

**Bước 2 — Chọn hoặc thiết kế chiến lược của bạn:**
- Dùng 1 trong 3 chiến lược có sẵn (built-in strategies) với tham số tối ưu, HOẶC
- Thiết kế chiến lược tùy chỉnh cho chủ đề của bạn (ví dụ: chia nhỏ theo cặp Câu hỏi-Đáp án, theo các phần (sections), theo tiêu đề (headers))
- Mỗi thành viên nên thử một chiến lược **khác nhau** để có cơ sở so sánh

```python
class CustomChunker:
    """Chiến lược chia nhỏ tùy chỉnh cho [chủ đề của bạn].

    Lý do thiết kế: [giải thích tại sao chiến lược này phù hợp với dữ liệu của bạn]
    """

    def chunk(self, text: str) -> list[str]:
        # Viết mã nguồn của bạn ở đây
        ...
```

**Bước 3 — So sánh:** So sánh chiến lược tùy chỉnh/được tinh chỉnh (custom/tuned strategy) với đường cơ sở (baseline) trên cùng tài liệu.

> **Ghi kết quả vào:** Báo cáo — Phần 3 (Chiến lược chia nhỏ - Chunking Strategy)

---

### Bài tập 3.2 — Chuẩn Bị Câu Hỏi Đánh Giá (Benchmark Queries)

Mỗi nhóm viết **đúng 5 câu hỏi đánh giá** kèm theo **câu trả lời chuẩn (gold answers)**.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

**Yêu cầu:**
- Câu hỏi phải đa dạng (không hỏi 5 câu có nội dung/cấu trúc giống hệt nhau)
- Câu trả lời chuẩn phải cụ thể và có thể kiểm chứng (verify) từ tài liệu
- Ít nhất 1 câu hỏi yêu cầu lọc bằng metadata (metadata filtering) để trả lời tốt

> **Ghi kết quả vào:** Báo cáo — Phần 6 (Kết quả — Câu hỏi đánh giá & Câu trả lời chuẩn)

---

### Bài tập 3.3 — Dự Đoán Độ Tương Tự Cosine (Cá nhân)

Gọi hàm `compute_similarity()` trên 5 cặp câu. **Trước khi chạy**, hãy dự đoán xem cặp câu nào sẽ có độ tương tự cao nhất/thấp nhất. Ghi lại các dự đoán của bạn và kết quả thực tế. Suy ngẫm xem điều gì khiến bạn ngạc nhiên nhất.

> **Ghi kết quả vào:** Báo cáo — Phần 5 (Dự đoán độ tương tự)

---

### Bài tập 3.4 — Chạy Đánh Giá & So Sánh Trong Nhóm

**Bước 1:** Mỗi thành viên chạy 5 câu hỏi đánh giá với chiến lược riêng. Ghi lại kết quả top-3 cho mỗi câu hỏi.

**Bước 2:** So sánh kết quả trong nhóm:
- Chiến lược nào cho việc truy xuất tốt nhất? Tại sao?
- Có câu hỏi nào mà chiến lược A tốt hơn B nhưng lại ngược lại ở câu hỏi khác không?
- Lọc bằng metadata (Metadata filtering) có giúp ích không?

**Bước 3:** Thảo luận và rút ra bài học — chuẩn bị cho phần demo (thuyết trình) với các nhóm khác.

> **Ghi kết quả vào:** Báo cáo — Phần 6 (Kết quả)
> **Gợi ý đánh giá:** xem danh sách kiểm tra ngắn trong `README.md` mục **Cách Tự Đánh Giá Kết Quả Retrieval** hoặc chi tiết hơn trong file `docs/EVALUATION.md`.

---

### Bài tập 3.5 — Phân Tích Lỗi (Failure Analysis)

Tìm ít nhất **1 trường hợp lỗi (failure case)** trong quá trình so sánh. Mô tả:
- Câu hỏi nào mà quá trình truy xuất gặp thất bại?
- Tại sao? (do chunk quá nhỏ/quá lớn, thiếu metadata, câu hỏi mơ hồ, v.v.)
- Đề xuất cải thiện?

> **Ghi kết quả vào:** Báo cáo — Phần 7 (Những gì tôi học được)
> **Gợi ý:** phân tích lỗi nên tham chiếu từ các góc nhìn như độ chính xác (precision), tính mạch lạc của chunk (chunk coherence), tính hữu dụng của metadata, và chất lượng thông tin nền (grounding quality).

---

## Danh Sách Kiểm Tra Nộp Bài (Submission Checklist)

- [x] Vượt qua tất cả các bài kiểm thử (tests): `pytest tests/ -v` → **42/42 PASSED** ✅
- [x] Cập nhật thư mục `src/` (cá nhân) → **Hoàn thiện chunking.py, store.py, agent.py, embeddings.py** ✅
- [x] Hoàn thành báo cáo nhóm (`report/REPORT_NHOM.md` — 1 file/nhóm) → **4/4 sections complete** ✅
- [x] Hoàn thành báo cáo cá nhân (`report/REPORT_CANHAN.md` — 1 file/sinh viên) → **5/5 sections complete** ✅
- [x] **BONUS:** Data corpus (data/shopee/) với 9 documents + sources.csv ✅
- [x] **BONUS:** Benchmark infrastructure (bench.py + ket_qua_benchmark.txt) ✅
- [x] **BONUS:** Improved embedding (SmartMockEmbedder) với 40% marker found ✅
- [x] **BONUS:** 3 chunking strategies so sánh (Recursive, Hierarchical, Mixed) ✅

---

## 📊 Kết Quả Cuối Cùng

### Tests: **42/42 PASSED** ✅
```bash
pytest tests/ -v
# TestProjectStructure: 2/2
# TestClassBasedInterfaces: 2/2
# TestFixedSizeChunker: 7/7
# TestSentenceChunker: 4/4
# TestRecursiveChunker: 4/4
# TestEmbeddingStore: 8/8
# TestKnowledgeBaseAgent: 2/2
# TestComputeSimilarity: 4/4
# TestCompareChunkingStrategies: 3/3
# TestEmbeddingStoreSearchWithFilter: 3/3
# TestEmbeddingStoreDeleteDocument: 3/3
```

### Benchmark: **4/10 (40%) Score** ✅
- Query #1: **2/2 PERFECT** (đúng doc + marker found)
- Query #2: 1/2 (marker in top-3)
- Query #3: 0/2
- Query #4: 0/2
- Query #5: 1/2 (top-1 correct, filter worked)

### Key Achievement
**Embedding improvement**: 0% → 40% marker found với SmartMockEmbedder (keyword-based)

---

## ✅ SẴN SÀNG NỘP BÀI

**Repository name**: K4-DAY07-PhungDucDang-2A202602956  
**Git status**: Clean (no .venv, no .env)  
**Ready to push**: `git push -u origin main`
