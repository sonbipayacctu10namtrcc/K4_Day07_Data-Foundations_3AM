# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Vũ Quốc Anh]
**Nhóm:** [3AM]
**Ngày:** [Ngày 03/08/2026]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai đoạn văn bản có hướng vector biểu diễn gần nhau trong không gian vector, thể hiện chúng có sự tương đồng lớn về mặt ngữ nghĩa và chủ đề.

**Ví dụ có độ tương tự CAO:**
- Câu A: Hôm nay thời tiết thật đẹp và tràn ngập ánh nắng.
- Câu B: Trời hôm nay nhiều nắng và khí hậu vô cùng dễ chịu.
- Tại sao tương đồng: Cả hai câu đều diễn đạt cùng một nội dung là thời tiết đẹp, ấm áp và có nắng, sử dụng các từ đồng nghĩa/gần nghĩa.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Chú chó con đang đùa nghịch ngoài sân vườn.
- Câu B: Trí tuệ nhân tạo đang làm thay đổi sâu sắc nhiều ngành công nghiệp.
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn khác biệt (động vật/hoạt động ngoài trời so với công nghệ/AI) nên không có sự liên quan về mặt ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Độ tương tự cosine đo góc giữa hai vector nên chỉ tập trung vào hướng ngữ nghĩa mà không phụ thuộc vào độ dài văn bản (độ lớn vector). Khoảng cách Euclid nhạy cảm với độ dài, dẫn đến việc hai văn bản cùng chủ đề nhưng có độ dài khác nhau sẽ bị đánh giá là xa nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* `số lượng chunk = làm_tròn_lên((10000 - 50) / (500 - 50)) = làm_tròn_lên(9950 / 450) = làm_tròn_lên(22.11)`
> *Đáp án:* 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> - Số lượng chunk sẽ tăng lên thành 25 chunks (phép tính: `làm_tròn_lên((10000 - 100) / (500 - 100)) = làm_tròn_lên(9900 / 400) = làm_tròn_lên(24.75) = 25`).
> - Ta muốn tăng độ chồng chéo để đảm bảo ngữ cảnh của thông tin xung quanh các ranh giới cắt không bị đứt đoạn, giúp LLM/bộ truy xuất giữ được sự liền mạch thông tin tốt hơn giữa các chunks liên kề.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy (regex) `(?<=\. )|(?<=! )|(?<=\? )|(?<=\.\n)` để tách văn bản thành danh sách câu dựa trên ranh giới câu mà vẫn giữ lại dấu câu. Xử lý các khoảng trắng thừa bằng `.strip()`, loại bỏ câu rỗng và sau đó nhóm các câu liên tiếp lại thành các chunk với kích thước tối đa là `max_sentences_per_chunk`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Sử dụng thuật toán đệ quy tách nhỏ văn bản theo độ ưu tiên của danh sách các ký tự phân tách `["\n\n", "\n", ". ", " ", ""]`. Base case là khi kích thước đoạn nhỏ hơn `chunk_size` hoặc không còn ký tự phân tách nào để chia (khi đó sẽ fallback sang cắt cứng theo ký tự). Sau khi đệ quy, các phần tử con được gộp lại với nhau tối đa trong giới hạn `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Với cấu trúc in-memory, lưu trữ tài liệu dưới dạng danh sách các dict chứa `id`, `content`, `metadata` và `embedding` được sinh ra từ `_embedding_fn`. Khi thực hiện `search`, truy vấn được nhúng thành vector và tính toán độ tương tự cosine với tất cả các vector đã lưu thông qua hàm `compute_similarity`, sau đó sắp xếp giảm dần để trả về kết quả tốt nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Thực hiện lọc trước (pre-filtering) bằng cách quét qua danh sách `_store` và chỉ giữ lại các tài liệu có `metadata` khớp hoàn toàn với `metadata_filter` trước khi tính toán độ tương tự. Đối với `delete_document`, tiến hành loại bỏ toàn bộ các chunk có `metadata['doc_id'] == doc_id` hoặc có ID trùng khớp trực tiếp.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Thực hiện tìm kiếm các chunk liên quan nhất bằng `store.search`, gộp nội dung các chunk này lại làm ngữ cảnh (context). Ngữ cảnh và câu hỏi sau đó được đưa vào mẫu prompt chuẩn để cung cấp cho mô hình ngôn ngữ thông qua `llm_fn` và trả về câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sản phẩm có thể được đổi trong 30 ngày. | Khách được đổi hàng trong vòng một tháng. | Cao | 0.87 | ✓ |
| 2 | Giá sản phẩm được quyết định bởi chi phí sản xuất. | Thời gian giao hàng phụ thuộc vào khoảng cách. | Thấp | 0.18 | ✓ |
| 3 | Seller phải cung cấp thông tin sản phẩm chính xác. | Người bán cần công khai chi tiết hàng đầy đủ. | Cao | 0.84 | ✓ |
| 4 | GHN quản lý dịch vụ giao hàng toàn quốc. | Tiki là nền tảng thương mại điện tử bán sản phẩm. | Thấp | 0.25 | ✓ |
| 5 | Khi hàng bị hư, báo cáo ngay cho seller. | Nếu sản phẩm có lỗi, liên hệ ngay với người bán. | Cao | 0.83 | ✓ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 3 có similarity cao (0.84) dù diễn đạt khác nhau: "cung cấp" vs "công khai", "thông tin" vs "chi tiết". Embedding model học được các synonym từ training data và sắp xếp chúng gần nhau trong semantic space. Điều này chứng tỏ embedding không chỉ khớp keyword mà thực sự hiểu ý nghĩa cốt lõi — hành động "chia sẻ thông tin sản phẩm".

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Chính sách đổi trả hàng trên Tiki là gì? Thời hạn bao lâu? | Tiki return policy - "Tiki chấp nhận đổi trả trong 30 ngày kể từ ngày nhận hàng" | 0.94 | ✓ Yes | Tiki chấp nhận đổi trả trong 30 ngày, điều kiện: hàng nguyên vẹn, chưa sử dụng |
| 2 | Tôi mua hàng trên Shopee, thanh toán nhưng chưa nhận được. Bao lâu tôi được hoàn tiền? | Shopee return policy - "Hoàn tiền vào tài khoản/ví điện tử 1-3 ngày làm việc" | 0.91 | ✓ Yes | Shopee hoàn tiền 1-3 ngày làm việc, có thể 1-5 ngày cho bank transfer tùy phương thức |
| 3 | Người bán phải đáp ứng những điều kiện nào khi bán trên Shopee? | Shopee seller conditions - "Tài khoản xác thực, không bán hàng cấm, giữ tỷ lệ hoàn dưới 10%" | 0.92 | ✓ Yes | Seller cần account verify, tuân thủ pricing policy, không abuse tools, tỷ lệ hoàn < 10% |
| 4 | So sánh GHN vs Lazada: nền tảng nào hoàn tiền nhanh hơn? | GHN shipping policy + Lazada refund policy (2 docs riêng, cần metadata) | 0.79 | ⚠️ Partial | GHN là shipper (không xử lý refund trực tiếp); Lazada hoàn tiền 3-7 ngày — Lazada nhanh hơn |
| 5 | Nếu hàng bị hư hỏng trong quá trình giao, tôi cần làm gì? | Multi-doc: Tiki/Shopee/Lazada policies - "Báo cáo 24 giờ, chụp ảnh, hoàn/thay 3-5 ngày" | 0.88 | ✓ Yes | Kiểm tra hàng, báo cáo trong 24 giờ, chụp ảnh chứng minh, seller hoàn tiền/thay thế 3-5 ngày |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4.5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Hà Xuân Sơn chọn Sentence chunking (điểm 8/10) có ưu điểm rất rõ khi query hỏi về các rule riêng rẽ: 18 chunks chi tiết, mỗi chunk = một câu hoàn chỉnh, đỡ bị mất context. Tuy nhiên độ chi tiết đó lại trở thành nhược điểm khi retriever phải rank giữa quá nhiều candidates. Bài học: không có chunking strategy hoàn hảo — cần trade-off giữa semantic accuracy (Sentence tốt) vs query efficiency (Recursive cân bằng).

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 9.5 / 10 |
| **Tổng phần cá nhân** | **59.5 / 60** |

**Giải thích:**
- Khởi động: 5/5 — cosine similarity, chunk calculation, tại sao ưu tiên cosine đều chi tiết và đúng.
- Hướng tiếp cận: 10/10 — Recursive chunking strategy giải thích rõ (priority separators, recursive base case, re-merge logic). Xử lý edge case tốt, thuật toán đệ quy được mô tả chính xác.
- Code: 30/30 — 42/42 tests passed, tất cả components hoạt động.
- Dự đoán: 5/5 — 5/5 cặp dự đoán cao/thấp đúng so với điểm thực tế.
- Truy xuất: 9.5/10 — 4.5/5 câu hỏi top-3 liên quan; câu 4 yêu cầu metadata filter nên score hơi thấp (0.79); trừ 0.5 vì metadata filter chưa triển khai.
