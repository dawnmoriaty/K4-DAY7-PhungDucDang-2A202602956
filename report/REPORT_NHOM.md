# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nhóm 3
**Thành viên:** Phùng Đức Đăng, Phùng Gia Bảo, Trần Ngọc Khánh, Nguyễn Hữu Thành
**Ngày:** 20/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách Trả hàng & Hoàn tiền của Shopee (E-commerce Customer Support)

**Tại sao nhóm chọn chủ đề này?**

> Shopee là sàn thương mại điện tử lớn nhất Việt Nam với chính sách trả hàng/hoàn tiền phức tạp, đa đối tượng (buyer vs seller), và có nhiều điều kiện, quy trình khác nhau. Đây là use case thực tế điển hình cho RAG: tài liệu có cấu trúc rõ ràng (## Mục, danh sách, bảng), nội dung dài (5-20KB/file), cần truy xuất chính xác (không được sai số liệu), và cần phân biệt đối tượng (audience filter). Ngoài ra, corpus này hoàn toàn công khai trên help.shopee.vn nên đảm bảo data governance.

### Danh sách tài liệu (Data Inventory)

| #   | Tên tài liệu                         | Nguồn (Source URL)                             | Ngày lấy / Phiên bản    | Số ký tự | Metadata đã gán                                              |
| --- | ------------------------------------ | ---------------------------------------------- | ----------------------- | -------- | ------------------------------------------------------------ |
| 1   | Cách đóng gói đơn hàng hoàn trả      | https://help.shopee.vn/portal/4/article/79508  | 2026-09-20 / not-stated | 3,204    | doc_id, title, audience=buyer, category=return-shipping      |
| 2   | Kiểm tra tiền hoàn vào SPayLater     | https://help.shopee.vn/portal/4/article/164831 | 2026-09-20 / not-stated | 5,569    | doc_id, title, audience=buyer, category=refund               |
| 3   | Phương thức gửi hàng và phí hoàn trả | https://help.shopee.vn/portal/4/article/189477 | 2026-09-20 / not-stated | 5,551    | doc_id, title, audience=buyer, category=return-shipping      |
| 4   | Quy định chung về Trả hàng/Hoàn tiền | https://help.shopee.vn/portal/4/article/188931 | 2026-09-20 / not-stated | 6,801    | doc_id, title, audience=buyer, category=returns-policy       |
| 5   | Sản phẩm hạn chế trả hàng            | https://help.shopee.vn/portal/4/article/79465  | 2026-09-20 / not-stated | 1,198    | doc_id, title, audience=buyer, category=returns-policy       |
| 6   | Theo dõi vận chuyển hàng hoàn trả    | https://help.shopee.vn/portal/4/article/189476 | 2026-09-20 / not-stated | 602      | doc_id, title, audience=buyer, category=return-shipping      |
| 7   | Thời gian nhận tiền hoàn             | https://help.shopee.vn/portal/4/article/189473 | 2026-09-20 / not-stated | 3,829    | doc_id, title, audience=buyer, category=refund               |
| 8   | Trả hàng do "Đổi ý"                  | https://help.shopee.vn/portal/4/article/204305 | 2026-09-20 / not-stated | 7,159    | doc_id, title, audience=buyer, category=returns-policy       |
| 9   | FAQ Trả hàng/Hoàn tiền cho Người bán | https://banhang.shopee.vn/edu/article/10626    | 2026-09-20 / not-stated | 14,149   | doc_id, title, **audience=seller**, category=return-response |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**

- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu   | Ví dụ giá trị                                   | Tại sao hữu ích cho truy xuất (retrieval)?                                                   |
| --------------- | ------ | ----------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `doc_id`        | string | `shopee-tra-hang-doi-y`                         | Định danh file gốc, dùng cho delete_document() và đối chiếu với gold answer                  |
| `audience`      | string | `buyer` / `seller`                              | **Quan trọng nhất** - Lọc câu hỏi theo đối tượng (buyer vs seller), tránh trả lời sai policy |
| `category`      | string | `returns-policy` / `refund` / `return-shipping` | Lọc theo chủ đề con, giúp narrow down search scope                                           |
| `title`         | string | "Những điều cần biết về Trả hàng..."            | Human-readable reference, hiển thị trong citations                                           |
| `source_url`    | string | `https://help.shopee.vn/...`                    | Traceability - user có thể verify nguồn gốc thông tin                                        |
| `retrieved_at`  | date   | `2026-09-20`                                    | Đánh dấu thời điểm crawl, quan trọng cho freshness check                                     |
| `language`      | string | `vi`                                            | Multilingual support - có thể filter theo ngôn ngữ nếu mở rộng                               |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên toàn bộ 9 tài liệu; bảng dưới đây ghi một tài liệu đại diện và tổng hợp toàn corpus:

| Tài liệu        | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không?                          |
| --------------- | --------------------- | -------------- | ----------------- | ------------------------------------------------- |
| Tổng 9 tài liệu | FixedSizeChunker      | 72 chunks      | 667.53 ký tự      | Ít chunk nhưng có thể cắt giữa mục hoặc quy trình |
| Tổng 9 tài liệu | SentenceChunker       | 140 chunks     | 341.02 ký tự      | Giữ câu nhưng tạo nhiều chunk nhỏ                 |
| Tổng 9 tài liệu | RecursiveChunker      | 85 chunks      | 563.68 ký tự      | Cân bằng kích thước và ranh giới tự nhiên         |

### Chiến lược của từng thành viên

**Thành viên 1 — Phùng Đức Đăng**

- **Loại chiến lược:** HierarchicalChunker (Hierarchy / chunk theo cấu trúc Markdown `##`, `###`)
- **Mô tả & lý do chọn cho chủ đề này:** Thực hiện theo yêu cầu riêng của biến thể K4-L3B (thử nghiệm chia nhỏ theo tiêu đề/mục của chính sách gốc). Tôi chia tài liệu theo tiêu đề và mục con (`##`, `###`) nhằm giữ nguyên cấu trúc logic của từng phần trong chính sách Shopee. Mục tiêu là mỗi chunk tập trung vào một chủ đề rõ ràng (như “Thời gian hoàn tiền”, “Điều kiện đổi ý”, hoặc “Phương thức gửi hàng”), đồng thời gắn kèm tiêu đề mục vào từng chunk giúp neo đậu ngữ cảnh.
- **Kết quả đạt được (trên toàn bộ 9 tài liệu):**
  - Total Chunks: 178 chunks (trung bình ~290 ký tự/chunk).
  - Tổng điểm Retrieval: **5/10 (50%)**.
  - Top-1 Correct: **3/5 (60%)** (Query 1, Query 2, Query 5).
  - Marker Found: **2/5 (40%)** (Query 1, Query 2).
  - Mức độ phù hợp: Giữ cấu trúc phân cấp xuất sắc cho các câu hỏi chính sách/FAQ có tiêu đề rõ ràng (Query 1 & 2 đạt điểm tuyệt đối 2/2).
- **Phân tích nguyên nhân sai 2 câu (Failure Analysis cho Query 3 & Query 4):**
  - **Query 3 (Sai do Lexical Overlap - Trùng lặp từ khóa):** Câu hỏi về *"hình thức Tự sắp xếp gửi trả hàng"* bị nhầm sang bài *"Cách đóng gói đơn hàng hoàn trả"* (`shopee-dong-goi-hang-hoan-tra.md`). Lý do: file đóng gói có mật độ từ khóa chung (`gửi hàng`, `bưu cục`, `mã vận đơn`, `bước`) xuất hiện quá dày đặc, lấn át từ khóa ngách *"Tự sắp xếp"*. Cần mô hình real embedding hiểu sâu ngữ nghĩa hoặc BM25 với trọng số IDF cao để không bị nhiễu.
  - **Query 4 (Sai do Over-segmentation - Phân mảnh danh mục):** Câu hỏi yêu cầu *"liệt kê các nhóm sản phẩm hạn chế trả hàng"*. File gốc `shopee-san-pham-han-che-tra-hang.md` có 5 mục `##` tương ứng 5 nhóm hàng, HierarchicalChunker đã chia mỗi `##` thành một chunk con riêng biệt (150-200 ký tự). Hậu quả là **không có chunk đơn lẻ nào chứa đầy đủ danh sách toàn bộ các nhóm**, khiến điểm tương đồng ngữ nghĩa bị phân tán và để mất Top-1 vào tay các tài liệu dài khác.
> **Kết luận cá nhân:** Chiến lược phân cấp theo header (hierarchical) là lựa chọn lý tưởng cho các câu hỏi tra cứu điều khoản cụ thể hoặc câu hỏi FAQ trực tiếp (nhờ giữ nguyên heading làm neo ngữ cảnh). Tuy nhiên, điểm yếu cố hữu là dễ bị phân mảnh khi gặp các câu hỏi mang tính chất "tổng hợp / liệt kê toàn cảnh" (list/aggregation queries) và nhạy cảm với các tài liệu có từ vựng tương đồng.

**Thành viên 2 — Phùng Gia Bảo**

- **Loại chiến lược:** HeadingChunker / chunk theo header (theo cấu trúc Markdown `##`, `###`)
- **Mô tả & lý do chọn:** Tôi chia tài liệu theo tiêu đề và mục con để giữ nguyên logic của từng phần trong chính sách Shopee. Mục tiêu là mỗi chunk tập trung vào một chủ đề rõ ràng, như “Thời gian hoàn tiền”, “Điều kiện đổi ý”, hoặc “Phương thức gửi hàng”, thay vì cắt ngang giữa các section. Với tài liệu hướng dẫn dài, cách này giúp giữ ngữ cảnh của từng mục khi người dùng hỏi về một chính sách cụ thể.
- **Kết quả đạt được:**
  - Total Chunks: 178
  - Top-1 Correct: 1/5 (20%)
  - Marker Found: 1/5 (20%)
  - Avg Top-1 Score: 0.3104
  - Mức độ phù hợp: giữ cấu trúc tốt, nhưng tăng số chunk và làm top-k dễ nhầm giữa các section cùng chủ đề.

> Kết luận cá nhân: chiến lược theo header giữ được cấu trúc tài liệu tốt, nhưng vì các section trong cùng một tài liệu nói rất nhiều về cùng chủ đề, các chunk tương đồng dẫn đến ví trí top-3 dễ bị trôi ngẫu nhiên. Tức là “giữ header” giúp đọc dễ hơn, nhưng không phải lúc nào cũng cải thiện retrieval vì sự giống nhau giữa các section nhiều hơn là sự khác biệt.

**Thành viên 3 — Trần Ngọc Khánh**

- **Loại chiến lược:** Semantic Chunking.
- **Cấu hình:** OpenAI `text-embedding-3-small`, percentile 90, `min_chunk_size=350`, `max_chunk_size=1200`.
- **Lý do:** Chính sách có các section dài ngắn khác nhau; ngắt theo độ thay đổi ngữ nghĩa giúp gom các điều kiện liên quan thay vì cắt theo số ký tự cố định. Heading được gắn vào nội dung theo sau; tài liệu ngắn hơn 1.200 ký tự được giữ nguyên để trả lời câu hỏi liệt kê.

```python
chunker = SemanticChunker(
    embedding_fn=embedder,
    breakpoint_percentile=90,
    min_chunk_size=350,
    max_chunk_size=1200,
)
```

- **Kết quả đạt được:** Chiến lược tạo 55 chunks từ toàn bộ 9 tài liệu. Cả 5 query đều truy xuất chunk chứa đáp án ở top-1, với score lần lượt là `0.549363`, `0.700006`, `0.630563`, `0.583413` và `0.629940`; KnowledgeBaseAgent trả lời đúng cả 5 gold answers, đạt **10/10 điểm retrieval**. Ở query dành cho người bán, metadata filter giữ cả top-3 thuộc `audience=seller`; khi không filter, một chunk `buyer` xuất hiện ở top-3. So với cấu hình đầu tiên đạt 6/10, việc gắn heading với nội dung theo sau và điều chỉnh kích thước chunk đã cải thiện kết quả lên 10/10.

**Thành viên 4 — Nguyễn Hữu Thành**

- **Loại chiến lược:**
  Recursive Chunking (Recursive Character Text Splitting).

- **Mô tả & lý do chọn:**
  Văn bản chính sách Shopee được chia thành các đoạn nhỏ bằng chiến lược Recursive Chunking với kích thước khoảng **500 ký tự/token tùy cấu hình của hệ thống**. Phương pháp này thực hiện chia văn bản theo thứ tự các dấu phân cách từ lớn đến nhỏ, nhằm ưu tiên giữ nguyên cấu trúc và ngữ nghĩa của các đoạn văn trước khi tiếp tục chia nhỏ khi đoạn vượt quá kích thước quy định. Chiến lược được lựa chọn vì tài liệu chính sách có nhiều tiêu đề, đoạn văn và danh sách, nên Recursive Chunking giúp tạo các chunks có kích thước tương đối đồng đều trong khi vẫn giữ được ngữ cảnh cần thiết cho semantic retrieval.
- **Kết quả đạt được:**
  - Tổng điểm Retrieval: 6/10 (60%)
  - Top-1 Correct: 3/5 (60%)
  - Chunk chứa đáp án trong Top-k: 3/5 (60%)
  - Metadata filter: Câu 5 không làm thay đổi kết quả retrieval trong phép thử A/B.

- **Code snippet (nếu custom):**

```python
CHUNKER = RecursiveChunker(chunk_size=500)

for path in sorted(corpus_dir.glob("*.md")):
    metadata, content = parse_frontmatter(path)

    for index, chunk in enumerate(CHUNKER.chunk(content)):
        documents.append(
            Document(
                id=f"{path.stem}#{index}",
                content=chunk,
                metadata=dict(metadata),
            )
        )
```

### So Sánh Giữa Các Thành Viên

| Thành viên       | Chiến lược (Strategy)               | Điểm truy xuất (/10)      | Điểm mạnh                                                                                  | Điểm yếu                                                                                                                          |
| ---------------- | ----------------------------------- | ------------------------- | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| Phùng Đức Đăng   | HierarchicalChunker (Hierarchy)     | 5/10 (3/5 top-1, 2/5 marker) | Giữ cấu trúc phân cấp Markdown (`##`, `###`) rõ ràng; xuất sắc cho câu hỏi điều khoản/FAQ cụ thể (Q1, Q2 đạt 2/2 điểm). | Phân mảnh các câu hỏi mang tính liệt kê/tổng hợp (Q4); nhạy cảm với trùng lặp từ khóa (Q3).                                     |
| Phùng Gia Bảo    | HeadingChunker                      | 2/10 (1/5 marker ở top-1) | Chia theo heading nên giữ được chủ đề và ngữ cảnh của mỗi mục.                             | Theo kết quả đã báo cáo, cũng tạo 178 chunks và chỉ có 1/5 marker; cần tinh chỉnh để tránh các chunk cùng chủ đề cạnh tranh nhau. |
| Trần Ngọc Khánh  | SemanticChunker                     | 10/10 (5/5 top-1)         | Gom các điều kiện liên quan về ngữ nghĩa; 5/5 chunk đáp án ở top-1.                        | Phụ thuộc OpenAI embedding API, chi phí và thời gian xử lý cao hơn.                                                               |
| Nguyễn Hữu Thành | RecursiveChunker (`chunk_size=500`) | 6/10 (3/5 top-3)          | Cân bằng kích thước chunk và ranh giới tự nhiên; 3/5 câu có chunk chứa đáp án trong top-3. | Câu hỏi quy trình/bằng chứng bị tách mất chi tiết; metadata filter ở câu 5 chưa cải thiện kết quả.                                |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

> **SemanticChunker đạt kết quả quan sát cao nhất (10/10).** RecursiveChunker đạt 6/10, cao hơn hai chiến lược dựa trên heading/hierarchy đang được báo cáo là 1/5 marker ở top-1. Tuy nhiên, SemanticChunker dùng OpenAI embedding còn RecursiveChunker dùng cấu hình embedding khác, nên không thể quy toàn bộ chênh lệch cho cách chunking; để kết luận chiến lược tốt nhất một cách chặt chẽ, cần A/B các chunker với cùng embedding backend và cùng cấu hình retrieval.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| #   | Câu hỏi (Query)                                                                                                         | Câu trả lời chuẩn (Gold Answer)                                                                                                              | Chunk nào chứa thông tin?                                                       |
| --- | ----------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| 1   | "Nếu thanh toán bằng thẻ tín dụng/ghi nợ thì tôi sẽ nhận tiền hoàn trong bao lâu?"                                      | "Tiền được hoàn về thẻ tín dụng/ghi nợ trong 7–14 ngày làm việc, tùy theo ngân hàng."                                                        | shopee-thoi-gian-va-kiem-tra-tien-hoan.md                                       |
| 2   | "Tôi đã mở hộp niêm phong để kiểm tra sản phẩm thì có được trả hàng với lý do đổi ý không?"                             | "Không. Việc mở bao bì, hộp, túi hoặc gói niêm phong làm mất tính nguyên vẹn; sản phẩm phải còn nguyên niêm phong, chưa mở và chưa sử dụng." | shopee-tra-hang-doi-y.md                                                        |
| 3   | "Nếu chọn hình thức Tự sắp xếp, tôi phải gửi trả hàng theo các bước nào?"                                               | "Đóng gói hàng; mang hàng đến bưu cục bất kỳ để gửi theo địa chỉ Shopee cung cấp; đăng bằng chứng trả hàng."                                 | shopee-phuong-thuc-va-phi-hoan-tra.md                                           |
| 4   | "Hãy liệt kê các nhóm sản phẩm hạn chế trả hàng và cho một vài ví dụ trong mỗi nhóm."                                   | "Các nhóm gồm: Sức khỏe/Vệ sinh, Thực phẩm/Hàng mau hỏng, Hàng đặc thù trong vận chuyển, Sản phẩm số, Khác."                                 | shopee-san-pham-han-che-tra-hang.md                                             |
| 5   | "Khi đơn hàng hoàn trả bị hư hỏng, thiếu hàng hoặc không đúng hàng, cần chuẩn bị bằng chứng gì?" (Query cho **seller**) | "Chuẩn bị video mở hàng có tài xế, thể hiện 6 mặt kiện nguyên vẹn."                                                                          | shopee-seller-phan-hoi-tra-hang-hoan-tien.md ← **Cần filter `audience=seller`** |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| #   | Câu hỏi                                | HierarchicalChunker (Đăng) | RecursiveChunker (Bảo) | RecursiveChunker (Thành)         | SemanticChunker (Khánh) | Ghi chú                                                                                             |
| --- | -------------------------------------- | -------------------------- | ---------------------- | -------------------------------- | ----------------------- | --------------------------------------------------------------------------------------------------- |
| 1   | Thanh toán thẻ - bao lâu nhận tiền?    | ✅ (top-1 & marker)        | ❌ (sai doc)           | ✅ (top-1)                       | ✅ (top-1)              | OpenAI embedding và Recursive của Thành đều truy xuất đúng chunk.                                   |
| 2   | Mở hộp niêm phong được trả hàng không? | ✅ (top-1 & marker)        | ✅ (đúng doc)          | ✅ (top-1)                       | ✅ (top-1)              | Recursive của Bảo, Thành và Semantic đều tìm đúng tài liệu.                                         |
| 3   | Tự sắp xếp gửi trả hàng theo bước nào? | ❌ (sai doc)               | ❌ (sai doc)           | ❌ (không có marker trong top-3) | ✅ (top-1)              | Semantic giữ heading cùng phần quy trình.                                                           |
| 4   | Liệt kê các nhóm sản phẩm hạn chế?     | ❌ (sai doc)               | ❌ (sai doc)           | ✅ (top-1)                       | ✅ (top-1)              | Semantic và Recursive của Thành lấy đúng chunk chứa danh sách.                                      |
| 5   | Seller - bằng chứng hư hỏng hàng?      | ✅ (đúng doc)              | ✅ (đúng doc)          | ❌ (không có marker trong top-3) | ✅ (top-1)              | Filter `audience=seller` tăng precision của context; Recursive của Thành thiếu chi tiết bằng chứng. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

> Có, rõ nhất ở Query 5 với SemanticChunker: top-1 vẫn đúng ở cả hai lượt, nhưng filter `audience=seller` giữ cả top-3 thuộc tài liệu người bán; khi bỏ filter, một chunk `buyer` xuất hiện trong top-3. Với RecursiveChunker của Thành, phép thử A/B chưa làm thay đổi kết quả. Vì vậy filter tăng precision của context, nhưng hiệu quả còn phụ thuộc vào chất lượng chunking và embedding.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

> 1. **Embedding quality ảnh hưởng mạnh đến kết quả**: SemanticChunker với OpenAI embedding đạt 5/5 top-1, trong khi các cấu hình khác thấp hơn. Vì embedding và chunking cùng thay đổi, nhóm xem đây là tín hiệu mạnh chứ không quy toàn bộ cải thiện cho riêng embedding.
> 2. **RecursiveChunker cân bằng hơn hai cấu hình theo heading được báo cáo**: Recursive đạt 3/5 chunk đáp án trong top-3, còn HierarchicalChunker và HeadingChunker đều ghi nhận 1/5 marker ở top-1. Bài học là giữ cấu trúc Markdown chưa đủ; chunk cũng cần đủ nhỏ và tập trung để tránh nhiễu.
> 3. **Metadata filter tăng độ chính xác ngữ cảnh**: Ở Query 5 của SemanticChunker, filter `audience=seller` loại chunk buyer khỏi top-3. Multi-audience/multi-domain data nên có filter tường minh để giảm nguy cơ trộn chính sách sai đối tượng.

**Bài học rút ra khi so sánh trong nhóm:**

> **Embedding là một nút thắt quan trọng**: kết quả SemanticChunker dùng OpenAI embedding vượt rõ rệt các cấu hình còn lại. Tuy nhiên, vì mỗi thành viên dùng cấu hình khác nhau, nhóm chưa thể tách hoàn toàn ảnh hưởng của embedding khỏi ảnh hưởng của chunking. Điều này dạy chúng ta:
>
> - Đừng optimize premature - identify bottleneck trước (embedding vs chunking)
> - A/B test với cùng embedding để isolate chunking effect
> - Real embedding (SentenceTransformer, OpenAI) là must-have cho production
>
> **Cần chuẩn hóa phép so sánh chunking**: Recursive đang có kết quả cao hơn hai cấu hình theo heading trong báo cáo, nhưng nhóm cần chạy lại toàn bộ chunker trên cùng embedding backend để kết luận chắc chắn về tác động riêng của chunking.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**

> 1. **Dùng real embedding từ đầu** - Setup SentenceTransformer/Ollama trong buổi warm-up để có baseline chính xác. SmartMock tốt cho demo nhưng real embeddings cần cho production assessment.
> 2. **Thêm metadata phong phú hơn** - Không chỉ `audience` mà còn `topic` (refund, shipping, condition), `urgency` (critical, normal), `doc_type` (policy, faq, guide) để multi-dimensional filtering.
> 3. **Implement embedding cache** - Hash content → save embedding để không re-compute mỗi lần chạy benchmark. Tiết kiệm cost với OpenAI API hoặc time với local models.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí                                 | Điểm tự đánh giá |
| ---------------------------------------- | ---------------- |
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10           |
| Thiết kế chiến lược (Strategy Design)    | 14 / 15          |
| Chất lượng truy xuất (Retrieval Quality) | 7 / 10           |
| Thuyết trình (Demo)                      | 4 / 5            |
| **Tổng phần nhóm**                       | **34 / 40**      |
