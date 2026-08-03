# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Chu Tuấn Việt
**Nhóm:** 3AM
**Ngày:** 03/08/2026

## 1. Khởi động

### 1.1. Cosine similarity

Cosine similarity đo mức độ cùng hướng giữa hai vector embedding. Hai đoạn văn có cosine similarity cao thường có nội dung hoặc ý nghĩa gần nhau; hai đoạn văn có similarity thấp thường nói về các chủ đề khác nhau.

Ví dụ có similarity cao:

- Câu A: `Khách hàng có thể đổi sản phẩm trong vòng 30 ngày.`
- Câu B: `Sản phẩm được phép đổi trong thời hạn 30 ngày kể từ ngày mua.`

Hai câu cùng nói về chính sách đổi sản phẩm và thời hạn 30 ngày.

Ví dụ có similarity thấp:

- Câu A: `Khách hàng có thể đổi sản phẩm trong vòng 30 ngày.`
- Câu B: `Mô hình học máy được huấn luyện bằng dữ liệu lớn.`

Hai câu thuộc hai chủ đề khác nhau: đổi trả và machine learning.

Cosine similarity phù hợp với text embedding vì nó quan tâm đến hướng biểu diễn ngữ nghĩa hơn là độ dài tuyệt đối của vector. Vì vậy, hai văn bản có nội dung tương tự nhưng độ dài khác nhau vẫn có thể có điểm similarity cao.

### 1.2. Tính số lượng chunk

Với tài liệu dài 10.000 ký tự, `chunk_size = 500`, `overlap = 50`:

```text
step = chunk_size - overlap = 500 - 50 = 450
số chunk = ceil((10000 - 50) / 450) = ceil(22.11...) = 23
```

Khi tăng overlap lên 100:

```text
step = 500 - 100 = 400
số chunk = ceil((10000 - 100) / 400) = 25
```

Overlap lớn hơn giúp giữ lại nhiều ngữ cảnh ở ranh giới giữa hai chunk, nhưng làm tăng số chunk, chi phí embedding và dung lượng lưu trữ.

## 2. Hướng tiếp cận cá nhân

### 2.1. FixedSizeChunker

Tôi sử dụng sliding window để chia văn bản theo số ký tự cố định. Bước dịch giữa hai chunk là `chunk_size - overlap`, nên phần cuối của chunk trước được lặp lại ở đầu chunk sau.

Các trường hợp đã xử lý:

- Text rỗng trả về danh sách rỗng.
- Text ngắn hơn hoặc bằng `chunk_size` trả về một chunk.
- Mỗi chunk không vượt quá `chunk_size`.
- `overlap` được giữ giữa các chunk liên tiếp.
- Tham số không hợp lệ bị từ chối bằng `ValueError`.

Ưu điểm của phương pháp này là đơn giản, dễ kiểm soát kích thước và phù hợp làm baseline. Nhược điểm là ranh giới chunk có thể cắt ngang câu hoặc đoạn văn.

### 2.2. SentenceChunker

`SentenceChunker` tách câu bằng dấu `.`, `!`, `?` và khoảng trắng hoặc xuống dòng sau dấu câu. Các câu sau đó được gom thành nhóm theo `max_sentences_per_chunk`, đồng thời loại bỏ khoảng trắng thừa.

### 2.3. RecursiveChunker

`RecursiveChunker` ưu tiên các separator theo thứ tự:

```python
["\n\n", "\n", ". ", " ", ""]
```

Đoạn văn được gom theo separator hiện tại. Nếu đoạn vẫn dài hơn `chunk_size`, thuật toán chuyển sang separator có mức ưu tiên thấp hơn. Khi không còn separator, văn bản được cắt theo kích thước cố định.

### 2.4. Cosine similarity và comparator

`compute_similarity` tính tích vô hướng chia cho tích độ dài hai vector. Nếu một vector có độ dài bằng 0, hàm trả về `0.0` để tránh chia cho 0.

`ChunkingStrategyComparator` chạy ba chiến lược và trả về số lượng chunk, độ dài trung bình và nội dung các chunk để tiện so sánh.

### 2.5. EmbeddingStore

Tôi sử dụng in-memory store cho checkpoint nhẹ của lab. Mỗi record lưu:

```python
{
    "id": document_id,
    "content": content,
    "metadata": metadata,
    "embedding": embedding,
}
```

Khi tìm kiếm, query được embedding và so sánh với các record bằng dot product. Kết quả được sắp xếp giảm dần theo score, có hỗ trợ lọc metadata và xóa theo `doc_id`.

### 2.6. KnowledgeBaseAgent

Agent lấy các chunk liên quan từ `EmbeddingStore`, ghép chúng thành context, tạo prompt chứa context và câu hỏi, rồi gọi hàm LLM được inject vào constructor. Cách này giữ phần retrieval độc lập với phần sinh câu trả lời.

## 3. Kết quả kiểm thử

Đã chạy:

```powershell
python -m pytest tests -v
```

Kết quả:

```text
42 passed in 0.21s
```

Các test của `FixedSizeChunker` đều pass, cùng với test cho sentence chunking, recursive chunking, similarity, vector store, metadata filter, delete document và agent.

Đã chạy thêm pipeline kiểm tra:

```powershell
python ingest.py
```

Kết quả:

```text
ingest self-check OK: parse được 4 khóa metadata, tạo 18 chunk
```

## 4. Dự đoán similarity

| Cặp | Câu A | Câu B | Dự đoán |
|---|---|---|---|
| 1 | Chính sách đổi trả trong 30 ngày. | Sản phẩm được đổi trong vòng 30 ngày. | Cao |
| 2 | Phí giao hàng do khách hàng thanh toán. | Mô hình cần dữ liệu để huấn luyện. | Thấp |
| 3 | Người bán phải cung cấp thông tin sản phẩm chính xác. | Seller cần đăng thông tin sản phẩm đầy đủ. | Cao |
| 4 | Khách hàng yêu cầu hoàn tiền sau khi trả hàng. | Máy tính xử lý hình ảnh bằng mạng neuron. | Thấp |
| 5 | Thời gian giao hàng phụ thuộc vào địa chỉ nhận. | Địa điểm nhận hàng ảnh hưởng đến thời gian giao. | Cao |

Các cặp có ý nghĩa gần nhau được dự đoán có similarity cao dù cách diễn đạt khác nhau. Đây là mục tiêu chính của embedding: biểu diễn mức độ gần nhau về nghĩa thay vì chỉ so khớp từ khóa.

## 5. Đóng góp cá nhân

- Hoàn thiện các chức năng chunking và similarity trong `src/chunking.py`.
- Hoàn thiện lưu trữ, tìm kiếm, lọc metadata và xóa document trong `src/store.py`.
- Hoàn thiện luồng RAG cơ bản trong `src/agent.py`.
- Bổ sung kiểm tra tham số cho `FixedSizeChunker`.
- Chạy và xác nhận toàn bộ 42 test đều pass.
- Kiểm tra pipeline ingest tạo chunk và giữ metadata.

## 6. Kết luận

Fixed-size chunking là baseline đơn giản và dễ kiểm soát, nhưng có thể làm mất ranh giới ngữ nghĩa tự nhiên. Sentence chunking giữ tính dễ đọc tốt hơn, còn recursive chunking linh hoạt hơn với tài liệu có nhiều cấu trúc. Trong phần cá nhân, các interface chính của lab đã được hoàn thiện và xác nhận bằng test tự động.

> Kết quả benchmark retrieval với 5 câu hỏi chính thức của nhóm sẽ được bổ sung sau khi nhóm thống nhất câu hỏi, gold answer và bộ tài liệu chung.
