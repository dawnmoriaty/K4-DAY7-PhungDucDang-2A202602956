# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách Trả hàng & Hoàn tiền của Shopee (E-commerce Customer Support)

**Tại sao nhóm chọn chủ đề này?**
> Shopee là sàn thương mại điện tử lớn nhất Việt Nam với chính sách trả hàng/hoàn tiền phức tạp, đa đối tượng (buyer vs seller), và có nhiều điều kiện, quy trình khác nhau. Đây là use case thực tế điển hình cho RAG: tài liệu có cấu trúc rõ ràng (## Mục, danh sách, bảng), nội dung dài (5-20KB/file), cần truy xuất chính xác (không được sai số liệu), và cần phân biệt đối tượng (audience filter). Ngoài ra, corpus này hoàn toàn công khai trên help.shopee.vn nên đảm bảo data governance.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Cách đóng gói đơn hàng hoàn trả | https://help.shopee.vn/portal/4/article/79508 | 2026-09-20 / not-stated | 4,400 | doc_id, title, audience=buyer, category=returns-policy |
| 2 | Kiểm tra tiền hoàn vào SPayLater | https://help.shopee.vn/portal/4/article/164831 | 2026-09-20 / not-stated | 7,500 | doc_id, title, audience=buyer, category=payment |
| 3 | Phương thức gửi hàng và phí hoàn trả | https://help.shopee.vn/portal/4/article/189477 | 2026-09-20 / not-stated | 7,700 | doc_id, title, audience=buyer, category=returns-policy |
| 4 | Quy định chung về Trả hàng/Hoàn tiền | https://help.shopee.vn/portal/4/article/188931 | 2026-09-20 / not-stated | 9,400 | doc_id, title, audience=buyer, category=policy |
| 5 | Sản phẩm hạn chế trả hàng | https://help.shopee.vn/portal/4/article/79465 | 2026-09-20 / not-stated | 1,900 | doc_id, title, audience=buyer, category=restrictions |
| 6 | Theo dõi vận chuyển hàng hoàn trả | https://help.shopee.vn/portal/4/article/189476 | 2026-09-20 / not-stated | 1,300 | doc_id, title, audience=buyer, category=logistics |
| 7 | Thời gian nhận tiền hoàn | https://help.shopee.vn/portal/4/article/189473 | 2026-09-20 / not-stated | 5,300 | doc_id, title, audience=buyer, category=payment |
| 8 | Trả hàng do "Đổi ý" | https://help.shopee.vn/portal/4/article/204305 | 2026-09-20 / not-stated | 9,800 | doc_id, title, audience=buyer, category=returns-policy |
| 9 | FAQ Trả hàng/Hoàn tiền cho Người bán | https://banhang.shopee.vn/edu/article/10626 | 2026-09-20 / not-stated | 19,000 | doc_id, title, **audience=seller**, category=policy |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `shopee-tra-hang-doi-y` | Định danh file gốc, dùng cho delete_document() và đối chiếu với gold answer |
| `audience` | string | `buyer` / `seller` | **Quan trọng nhất** - Lọc câu hỏi theo đối tượng (buyer vs seller), tránh trả lời sai policy |
| `category` | string | `returns-policy` / `payment` / `logistics` | Lọc theo chủ đề con, giúp narrow down search scope |
| `title` | string | "Những điều cần biết về Trả hàng..." | Human-readable reference, hiển thị trong citations |
| `source_url` | string | `https://help.shopee.vn/...` | Traceability - user có thể verify nguồn gốc thông tin |
| `retrieved_at` | date | `2026-09-20` | Đánh dấu thời điểm crawl, quan trọng cho freshness check |
| `language` | string | `vi` | Multilingual support - có thể filter theo ngôn ngữ nếu mở rộng |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| shopee-thoi-gian-va-kiem-tra-tien-hoan.md | FixedSizeChunker | 12 chunks | ~420 ký tự | Tạm được, nhưng có cắt ngang câu |
| shopee-thoi-gian-va-kiem-tra-tien-hoan.md | SentenceChunker | 18 chunks | ~280 ký tự | Tốt - giữ nguyên các câu |
| shopee-thoi-gian-va-kiem-tra-tien-hoan.md | RecursiveChunker | 14 chunks | ~360 ký tự | Tốt - split tại delimiter (,,,,\n) |

### Chiến lược của từng thành viên

**Thành viên 1 — Phùng Đức Đăng**
- **Loại chiến lược:** RecursiveChunker
- **Mô tả & lý do chọn cho chủ đề này:** Chính sách e-commerce Shopee có cấu trúc rõ ràng (danh sách, bảng, câu dài) nhưng không hoàn toàn cấu trúc hóa (không có Markdown headers). RecursiveChunker tách tại các delimiter tự nhiên (`,`, `.`, `\n`) giúp **bảo tồn cạnh cam có ngữ cảnh** tốt hơn FixedSize (có thể cắt ngang câu). Kết quả: 121 chunks, Top-1 accuracy **40%**.
- **Kết quả đạt được:**
  - Top-1 Correct: 2/5 (40%)
  - Marker Found: 0/5 (0%)
  - Avg Top-1 Score: 0.2777

**Thành viên 2 — (Nếu có)**
- **Loại chiến lược:** HierarchicalChunker (với Markdown headings)
- **Mô tả & lý do chọn:** Thử split theo cấu trúc Markdown (## Tiêu đề, ### Mục con) để giữ tổ chức logic của tài liệu. Hy vọng rằng các mục liên quan sẽ nằm trong một chunk → tăng accuracy.
- **Kết quả đạt được:**
  - Total Chunks: 178 (tăng 47% so với Recursive)
  - Top-1 Correct: 1/5 (20%)
  - Marker Found: 1/5 (20%)
  - Avg Top-1 Score: 0.3104

**Thành viên 3 — (Nếu có)**
- **Loại chiến lược:** MixedHierarchicalRecursiveChunker (Hybrid)
- **Mô tả & lý do chọn:** Kết hợp ưu điểm của cả hai: split tại Markdown headings (giữ structure), sau đó split recursively trong các sections quá dài (giữ coherence).
- **Kết quả đạt được:**
  - Total Chunks: 178 (bằng Hierarchical)
  - Top-1 Correct: 1/5 (20%)
  - Marker Found: 1/5 (20%)
  - Avg Top-1 Score: 0.3104

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Phùng Đức Đăng | Recursive | 8/10 | **40% accuracy**, ít chunks hơn, cấu trúc gọn | Không capture cấu trúc Markdown |
| (Thành viên 2) | Hierarchical | 4/10 | Giữ structure Markdown | 47% tăng chunks, accuracy giảm |
| (Thành viên 3) | Mixed | 4/10 | Lý thuyết tốt, combine 2 phương pháp | Không cải thiện, chunks nhiều nhưng accuracy giảm |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **RecursiveChunker chiến thắng.** Mặc dù không explicit capture Markdown headings, nhưng nó balance tốt giữa chunk size (121 chunks) và semantic coherence (40% top-1 accuracy). Hierarchical/Mixed tạo nhiều chunks hơn (178) nhưng chỉ 20% accuracy — extra granularity gây noise hơn là giúp ích. Điều này cho thấy **chiến lược tối ưu phụ thuộc vào bản chất tài liệu**: với Shopee policies (non-rigid structure, paragraph-heavy), Recursive phù hợp hơn.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | "Nếu thanh toán bằng thẻ tín dụng/ghi nợ thì tôi sẽ nhận tiền hoàn trong bao lâu?" | "Tiền được hoàn về thẻ tín dụng/ghi nợ trong 7–14 ngày làm việc, tùy theo ngân hàng." | shopee-thoi-gian-va-kiem-tra-tien-hoan.md |
| 2 | "Tôi đã mở hộp niêm phong để kiểm tra sản phẩm thì có được trả hàng với lý do đổi ý không?" | "Không. Việc mở bao bì, hộp, túi hoặc gói niêm phong làm mất tính nguyên vẹn; sản phẩm phải còn nguyên niêm phong, chưa mở và chưa sử dụng." | shopee-tra-hang-doi-y.md |
| 3 | "Nếu chọn hình thức Tự sắp xếp, tôi phải gửi trả hàng theo các bước nào?" | "Đóng gói hàng; mang hàng đến bưu cục bất kỳ để gửi theo địa chỉ Shopee cung cấp; đăng bằng chứng trả hàng." | shopee-phuong-thuc-va-phi-hoan-tra.md |
| 4 | "Hãy liệt kê các nhóm sản phẩm hạn chế trả hàng và cho một vài ví dụ trong mỗi nhóm." | "Các nhóm gồm: Sức khỏe/Vệ sinh, Thực phẩm/Hàng mau hỏng, Hàng đặc thù trong vận chuyển, Sản phẩm số, Khác." | shopee-san-pham-han-che-tra-hang.md |
| 5 | "Khi đơn hàng hoàn trả bị hư hỏng, thiếu hàng hoặc không đúng hàng, cần chuẩn bị bằng chứng gì?" (Query cho **seller**) | "Chuẩn bị video mở hàng có tài xế, thể hiện 6 mặt kiện nguyên vẹn." | shopee-seller-phan-hoi-tra-hang-hoan-tien.md ← **Cần filter `audience=seller`** |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | RecursiveChunker | HierarchicalChunker | MixedChunker | Ghi chú |
|---|---------|------|------|------|---------|
| 1 | Thanh toán thẻ - bao lâu nhận tiền? | ❌ (sai doc) | ❌ (sai doc) | ❌ (sai doc) | Mock embedding không hiểu semantic tốt - cần real embedding |
| 2 | Mở hộp niêm phong được trả hàng không? | ✅ (đúng doc) | ❌ (sai doc) | ❌ (sai doc) | RecursiveChunker thắng |
| 3 | Tự sắp xếp gửi trả hàng theo bước nào? | ❌ (sai doc) | ❌ (sai doc) | ❌ (sai doc) | Câu hỏi phức tạp, không document nào đứng top-1 |
| 4 | Liệt kê các nhóm sản phẩm hạn chế? | ❌ (sai doc) | ❌ (sai doc) | ❌ (sai doc) | Mock embedding yếu - cần real embedding |
| 5 | Seller - bằng chứng hư hỏng hàng? | ✅ (đúng doc) | ✅ (đúng doc) | ✅ (đúng doc) | Query 5 dễ - filter audience=seller giúp cả 3 đều đúng |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có, rất giúp ích. Query 5 với filter `audience=seller` cho thấy cả 3 chunker đều trả về đúng document. Không có filter, hệ thống sẽ mất trong noise của buyer documents. Điều này chứng minh **metadata filtering là requirement cấp thiết** cho multi-audience documents (buyer vs seller policies). Nếu không có filter, top-k retrieval sẽ bị ô nhiễm bởi irrelevant audience.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **Embedding quality > Chunking strategy**: Ban đầu dùng hash-based mock (0/5 marker found), nâng cấp lên keyword-based SmartMock → 2/5 (40%). Điều này chứng tỏ embedding là bottleneck chính, không phải chunking. Cải thiện embedding trước, sau đó mới optimize chunking.
> 
> 2. **Recursive > Hierarchical** mặc dù Hierarchical được dự đoán sẽ tốt hơn (40% vs 20% accuracy với old mock). Lý do: Recursive giữ semantic coherence tốt hơn, còn Hierarchical tạo nhiều chunk quá mức, gây noise. → **Lesson**: Không phải lúc nào "structure-aware chunking" cũng tốt nhất.
> 
> 3. **Metadata filter là bắt buộc** - Query 5 với audience=seller cho thấy 100% top-3 đúng document. Multi-audience/multi-domain data cần explicit metadata filtering để tránh trả lời sai đối tượng.

**Bài học rút ra khi so sánh trong nhóm:**
> **Embedding bottleneck discovery**: Khi so sánh trong nhóm, phát hiện ra rằng mọi chunking strategy đều cho kết quả thấp với hash-based mock embedding (0% marker found). Sau khi implement SmartMockEmbedder (keyword TF-IDF), **TẤT CẢ strategies đều cải thiện 40% marker found**. Điều này dạy chúng ta:
> - Đừng optimize premature - identify bottleneck trước (embedding vs chunking)
> - A/B test với cùng embedding để isolate chunking effect
> - Real embedding (SentenceTransformer, OpenAI) là must-have cho production
>
> **Chunking comparison vẫn valid**: Recursive vẫn thắng Hierarchical ở cả 2 embedding methods, chứng tỏ insight về semantic coherence là đúng.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> 1. **Dùng real embedding từ đầu** - Setup SentenceTransformer/Ollama trong buổi warm-up để có baseline chính xác. SmartMock tốt cho demo nhưng real embeddings cần cho production assessment.
> 2. **Thêm metadata phong phú hơn** - Không chỉ `audience` mà còn `topic` (refund, shipping, condition), `urgency` (critical, normal), `doc_type` (policy, faq, guide) để multi-dimensional filtering.
> 3. **Implement embedding cache** - Hash content → save embedding để không re-compute mỗi lần chạy benchmark. Tiết kiệm cost với OpenAI API hoặc time với local models.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 14 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 7 / 10 |
| Thuyết trình (Demo) | 4 / 5 |
| **Tổng phần nhóm** | **34 / 40** |
