# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Hà Xuân Sơn]
**Nhóm:** [3AM]
**Ngày:** [03/08/2026]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector chỉ về cùng hướng (close angle), mặc dù có thể khác độ dài. Độ tương tự cao (gần 1) có nghĩa là embeddings biểu diễn ý nghĩa ngữ nghĩa tương tự nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Python là ngôn ngữ lập trình"
- Câu B: "Lập trình với Python"
- Tại sao tương đồng: Cùng chủ đề (Python & lập trình), khác từ ngữ nhưng ý nghĩa gần nhau

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Mèo chạy trên cỏ xanh"
- Câu B: "Đầu bếp nấu canh chiều nay"
- Tại sao khác: Chủ đề hoàn toàn khác (động vật vs nấu ăn), từ vựng không giao thoa

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ so sánh hướng vector, bỏ qua độ dài — phù hợp vì embedding dài ngắn (điều chỉnh từ preprocessing) không liên quan đến ý nghĩa. Euclid bị ảnh hưởng bởi độ dài, làm bias chọn chunk dài hơn mặc dù có thể ít liên quan.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Công thức: số_chunk = ⌈(độ_dài - overlap) / (chunk_size - overlap)⌉ = ⌈(10000 - 50) / (500 - 50)⌉ = ⌈9950 / 450⌉ = ⌈22.11⌉ = 23 chunks
> Đáp án: 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk tăng: ⌈(10000 - 100) / (500 - 100)⌉ = ⌈9900 / 400⌉ = 25 chunks. Tăng overlap giúp giữ ngữ cảnh tốt hơn ở ranh giới chunk — thông tin liên quan nằm ở cuối chunk cũ sẽ xuất hiện lại ở chunk tiếp theo, tránh mất mát khi chia cắt.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex `(?<=[.!?])\s+` phát hiện ranh giới câu (sau dấu câu theo sau khoảng trắng). Nhóm lại các câu theo `max_sentences_per_chunk`. Xử lý edge case: text rỗng trả về [], câu không có dấu câu được coi là 1 câu, các khoảng trắng thừa bị strip.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thử separators theo thứ tự ưu tiên ["\n\n", "\n", ". ", " ", ""]. Nếu chunk quá lớn (> chunk_size), đệ quy với separator tiếp theo. Base case: nếu text <= chunk_size thì trả về [text]; nếu hết separator thì chia cố định theo chunk_size. Cách này giữ ngữ cảnh tốt bằng cách ưu tiên chia theo paragraph/sentence trước khi chia từng ký tự.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ hai cách: ChromaDB nếu có, fallback sang in-memory list. Mỗi document được nhúng (embed) và lưu record chứa doc_id, content, embedding, metadata. Search: nhúng query, tính dot product với tất cả embeddings (nhanh vì embedding đã chuẩn hóa), sắp xếp giảm dần theo score, trả về top_k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc trước: filter records by metadata trước, sau đó tìm kiếm trong subset (tránh tính toán không cần thiết). Delete: loại bỏ tất cả records có doc_id khớp; trả về True nếu có xóa ít nhất 1 record, False nếu doc_id không tồn tại.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> RAG pattern: truy xuất top_k chunks từ store dựa trên query, nối content lại thành context block. Xây dựng prompt: "Context:\n{chunks}\n\nQuestion: {question}\n\nAnswer:" để LLM có ngữ cảnh rõ ràng. Gọi llm_fn() và trả về câu trả lời. Cách này giản đơn nhưng hiệu quả: LLM chỉ cần tập trung vào việc synthesize từ context sẵn.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker (7 tests) PASSED
tests/test_solution.py::TestSentenceChunker (4 tests) PASSED
tests/test_solution.py::TestRecursiveChunker (4 tests) PASSED
tests/test_solution.py::TestEmbeddingStore (8 tests) PASSED
tests/test_solution.py::TestKnowledgeBaseAgent (2 tests) PASSED
tests/test_solution.py::TestComputeSimilarity (4 tests) PASSED
tests/test_solution.py::TestCompareChunkingStrategies (3 tests) PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter (3 tests) PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument (3 tests) PASSED
============================= 42 passed in 0.14s ================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Khách hàng có thể đổi sản phẩm trong vòng 30 ngày. | Chính sách đổi sản phẩm tối đa là 1 tháng. | Cao | 0.89 | ✓ |
| 2 | Phí vận chuyển do shipper quyết định. | Giá sản phẩm phụ thuộc vào chất lượng hàng. | Thấp | 0.15 | ✓ |
| 3 | Người bán cần xác thực tài khoản để bán trên nền tảng. | Seller phải có account đã verify để tham gia. | Cao | 0.85 | ✓ |
| 4 | GHN là công ty chuyên về logistics giao hàng. | Lazada là sàn TMĐT bán hàng trực tuyến. | Thấp | 0.22 | ✓ |
| 5 | Nếu hàng bị hư, báo cáo ngay cho shipper và seller. | Khi hàng có vấn đề, liên hệ với bên bán để xử lý. | Cao | 0.81 | ✓ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 5 có similarity cao (0.81) dù từ vựng khác nhau (báo cáo/liên hệ, shipper/bên bán). Điều này chứng tỏ embedding model thể hiện ý nghĩa ngữ nghĩa (hành động xử lý hàng lỗi) thay vì chỉ khớp từ khóa. Embedding học được các synonym tương tự nhau trong training data và sắp xếp chúng gần nhau trong không gian vector.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Chính sách đổi trả hàng trên Tiki là gì? Thời hạn bao lâu? | Tiki return policy - "Hàng có thể đổi trong 30 ngày từ ngày nhận" | 0.92 | ✓ Yes | Tiki chấp nhận đổi trả trong 30 ngày, hàng phải nguyên vẹn và chưa sử dụng |
| 2 | Tôi mua hàng trên Shopee, thanh toán nhưng chưa nhận được. Bao lâu tôi được hoàn tiền? | Shopee return policy - "Hoàn tiền trong 1-3 ngày làm việc sau khi seller hủy" | 0.88 | ✓ Yes | Shopee hoàn tiền trong 1-3 ngày làm việc, có thể lâu hơn tùy phương thức thanh toán |
| 3 | Người bán phải đáp ứng những điều kiện nào khi bán trên Shopee? | Shopee seller conditions - "Tài khoản xác thực, không bán hàng cấm, pricing policy" | 0.89 | ✓ Yes | Seller cần account xác thực, không bán hàng cấm, tuân thủ pricing, tỷ lệ hoàn dưới 10% |
| 4 | So sánh GHN vs Lazada: nền tảng nào hoàn tiền nhanh hơn? | GHN shipping policy + Lazada refund policy (mix 2 docs) | 0.71 | ⚠️ Partial | GHN tập trung giao hàng (không xử lý refund); Lazada hoàn tiền 3-7 ngày — cần metadata filter |
| 5 | Nếu hàng bị hư hỏng trong quá trình giao, tôi cần làm gì? | Tiki/Shopee/Lazada return policy - "Báo cáo trong 24 giờ, chụp ảnh, hoàn/thay thế 3-5 ngày" | 0.86 | ✓ Yes | Kiểm tra + báo cáo trong 24 giờ, chụp ảnh, seller xác nhận và hoàn/thay thế trong 3-5 ngày |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4.5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Vũ Quốc Anh chọn Recursive chunking (điểm 9/10) thực sự tốt hơn Sentence chunking (8/10) của tôi ở câu hỏi so sánh cross-platform (Q4). Recursive giữ paragraph structure tốt, còn Sentence tạo quá nhiều micro-chunks dẫn đến noise. Bài học: kích thước chunk phải match với cấu trúc tài liệu, không phải cứ nhỏ/chi tiết là tốt.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 9 / 10 |
| **Tổng phần cá nhân** | **58 / 60** |

**Giải thích:**
- Khởi động: 5/5 — tất cả lý thuyết cosine similarity, chunk calculation đúng, ví dụ cụ thể.
- Hướng tiếp cận: 9/10 — Sentence chunking strategy rõ ràng, xử lý edge cases tốt; trừ 1 vì chưa xem xét độ dài câu có thể quá dài (overlap hay sub-chunking).
- Code: 30/30 — 42/42 tests passed.
- Dự đoán: 5/5 — 5 cặp đều dự đoán đúng cao/thấp so với điểm thực tế.
- Truy xuất: 9/10 — 4.5/5 câu hỏi top-3 liên quan; câu 4 (so sánh cross-platform) phải thêm metadata filter; trừ 1 vì dependency vào metadata filter chưa triển khai.
