# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phùng Đức Đăng
**Nhóm:** Nhóm 3
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code 3(30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

Khi hai đoạn văn bản có độ tương tự cosine cao, điều đó có nghĩa là các vector biểu diễn của chúng hướng về cùng một phía trong không gian nhiều chiều. Nói cách khác, dù nội dung có thể dùng từ ngữ khác nhau, chúng vẫn mang ý nghĩa tương đồng hoặc cùng một chủ đề.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Chính sách hoàn tiền"
- Câu B: "Quy định đổi trả"
- Tại sao tương đồng: Dù dùng từ khác nhau nhưng máy tính hiểu chúng cùng nằm trong cụm chủ đề hỗ trợ khách hàng

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Chính sách hoàn tiền"
- Câu B: "Thời tiết hôm nay"
- Tại sao khác: Hai khái niệm không liên quan nên hướng của vector sẽ khác xa nhau

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

Khoảng cách Euclid (Euclidean distance) đo khoảng cách đường chim bay, nó bị ảnh hưởng bởi độ lớn (độ dài) của vector. Trong văn bản, một đoạn văn dài có thể có số lượng từ nhiều hơn làm vector "dài hơn" một đoạn ngắn, dù cả hai nói về cùng một chủ đề. Cosine similarity chỉ tập trung vào hướng (góc giữa hai vector) và triệt tiêu yếu tố độ dài. Điều này giúp hệ thống so sánh nghĩa của văn bản chính xác hơn mà không bị "nhiễu" bởi độ dài ngắn của đoạn văn. Ngoài ra, hầu hết các embedding model hiện đại đều trả về vector đã được chuẩn hóa về độ dài bằng 1, khi đó cosine thường là lựa chọn mặc định.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

Công thức: ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.111) = **23 chunks**
Thực tế: 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

Khi overlap tăng lên 100: ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = **25 chunks** (tăng từ 23)

Muốn tăng độ chồng chéo vì nó giữ lại thông tin ở ranh giới giữa các chunks. Khi hỏi retrieval, nếu câu hỏi liên quan đến thông tin ở ranh giới, overlap lớn giúp tìm thấy tốt hơn. Nhưng đánh đổi là phải lưu trữ nhiều chunks hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

Tôi dùng regex lookahead `(?<=[.!?])\s+` để tách câu mà giữ lại dấu câu (không nuốt mất). 
Sau đó gom các câu liền kề theo `max_sentences_per_chunk`. Edge case xử lý: text rỗng trả `[]`, 
câu không có dấu được giữ nguyên.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

Thuật toán hai chiều: (1) Đệ quy xuống sâu - thử separators theo thứ tự (ưu tiên ranh giới "to" trước), 
nếu mảnh vẫn quá dài thì hạ xuống separator nhỏ hơn. (2) Gom lên - nối các mảnh nhỏ liền kề cho tới sát 
`chunk_size` để tránh chunks vụn. Base case: text ≤ chunk_size (return), hết separators (cắt cứng), 
empty separator (cắt cứng).

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

Tôi tách logic thành 2 helper methods: (1) `_make_record` - chuẩn hóa Document → internal record 
(embed + copy metadata + bảo đảm doc_id). (2) `_search_records` - tính similarity toàn bộ records 
rồi sort descending. Điều này tránh lặp logic vì cả `search()` và `search_with_filter()` đều cần 
tính similarity giống nhau.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

Filter **trước** khi search (không sau) vì nếu filter sau sẽ mất kết quả - k slots có thể bị 
chiếm bởi records không hợp lệ. `delete_document` dùng list comprehension để lọc ra những record 
có `metadata['doc_id']` khác, trả True/False tuỳ xóa được gì không.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

Theo mô hình RAG chuẩn: (1) Retrieve - gọi store.search() lấy top-k chunks. (2) Augment - xây prompt 
với ngữ cảnh **có đánh số** [1] [2] [3]. (3) Generate - gọi llm_fn(). Đánh số chunks giúp model 
tham chiếu được (ví dụ "như [1] nói...") → câu trả lời **truy vết được** → đạt tiêu chí Source Traceability.


---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
pytest tests/ -v
→ 42/42 PASSED ✅

TestProjectStructure: 2/2
TestClassBasedInterfaces: 2/2
TestFixedSizeChunker: 7/7
TestSentenceChunker: 4/4
TestRecursiveChunker: 4/4
TestEmbeddingStore: 8/8
TestKnowledgeBaseAgent: 2/2
TestComputeSimilarity: 4/4
TestCompareChunkingStrategies: 3/3
TestEmbeddingStoreSearchWithFilter: 3/3
TestEmbeddingStoreDeleteDocument: 3/3
```

**Số lượng bài test vượt qua (pass):** 42 / 42 ✅

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

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

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
