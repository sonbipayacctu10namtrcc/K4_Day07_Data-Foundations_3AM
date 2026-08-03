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

Khi chạy trên `data/k4_ecommerce/shopee_return_policy.md` với `chunk_size = 500`, comparator cho kết quả thực tế:

| Chiến lược | Số chunk | Độ dài trung bình |
|---|---:|---:|
| Fixed-size (không overlap trong comparator) | 40 | 493,20 ký tự |
| Sentence (3 câu/chunk) | 47 | 416,85 ký tự |
| Recursive | 61 | 321,26 ký tự |

Riêng chiến lược cá nhân `FixedSizeChunker(chunk_size=500, overlap=50)` tạo **44 chunk**, độ dài trung bình **497,23 ký tự**; 43 chunk dài 500 ký tự và chunk cuối dài 378 ký tự.

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

Môi trường hiện tại có Python 3.11 nhưng chưa cài `pytest`, vì vậy lệnh sau chưa chạy được:

```powershell
py -3.11 -m pytest tests -v
```

Kết quả:

```text
No module named pytest
```

Để kiểm tra cùng bộ 42 test mà không thay đổi code hoặc cài thêm thư viện, tôi chạy bằng `unittest`:

```powershell
$env:LAB_SOLUTION_PACKAGE='src.ChuTuanViet_2A202601082'
py -3.11 -m unittest tests.test_solution -v
```

Kết quả thực tế:

```text
Ran 42 tests in 0.007s
OK
```

**42/42 test pass.** Lỗi cấu trúc trước đó ở `TestProjectStructure.test_src_package_exists` đã được xử lý bằng cách bổ sung `src/__init__.py`, giúp Python nhận diện `src` là package. Toàn bộ test cấu trúc và test chức năng của chunking, cosine similarity, vector store, metadata filter, xóa document và agent đều pass.

Đã chạy thêm pipeline kiểm tra:

```powershell
py -3.11 ingest.py
```

Kết quả:

```text
ModuleNotFoundError: No module named 'src.chunking'
```

Nguyên nhân là `ingest.py` import cố định `src.chunking`, không import package cá nhân `src.ChuTuanViet_2A202601082`. Theo yêu cầu không sửa code, lỗi này được giữ nguyên và ghi nhận trung thực. `main.py` cũng chưa chạy đến phần demo vì môi trường thiếu dependency `python-dotenv` (`ModuleNotFoundError: No module named 'dotenv'`).

## 4. Dự đoán và kết quả similarity

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế (`MockEmbedder`) | Đối chiếu |
|---|---|---|---|---:|---|
| 1 | Chính sách đổi trả trong 30 ngày. | Sản phẩm được đổi trong vòng 30 ngày. | Cao | 0,2342 | Cùng chiều nhưng điểm thấp |
| 2 | Phí giao hàng do khách hàng thanh toán. | Mô hình cần dữ liệu để huấn luyện. | Thấp | -0,0253 | Phù hợp |
| 3 | Người bán phải cung cấp thông tin sản phẩm chính xác. | Seller cần đăng thông tin sản phẩm đầy đủ. | Cao | 0,2058 | Cùng chiều nhưng điểm thấp |
| 4 | Khách hàng yêu cầu hoàn tiền sau khi trả hàng. | Máy tính xử lý hình ảnh bằng mạng neuron. | Thấp | -0,0835 | Phù hợp |
| 5 | Thời gian giao hàng phụ thuộc vào địa chỉ nhận. | Địa điểm nhận hàng ảnh hưởng đến thời gian giao. | Cao | -0,1308 | Không phù hợp |

Về ngữ nghĩa, các dự đoán ban đầu vẫn hợp lý. Tuy nhiên, `MockEmbedder` tạo vector xác định để phục vụ unit test chứ không phải embedding ngữ nghĩa, nên điểm thực tế không phản ánh tốt độ gần nghĩa của tiếng Việt. Đặc biệt cặp 5 có nghĩa gần nhau nhưng nhận điểm âm. Vì vậy không nên dùng các điểm mock này để kết luận chất lượng chiến lược.

## 5. Kết quả truy xuất với 5 câu hỏi chung

Tôi nạp toàn bộ 7 file Markdown trong `data/k4_ecommerce`, chia bằng `FixedSizeChunker(500, 50)` và thu được **139 chunk**. Do môi trường không có embedding model thật, lần chạy dùng `MockEmbedder`; bảng dưới ghi đúng top-3 theo tên file:

| # | Nguồn của top-1 → top-3 | Nhận xét |
|---|---|---|
| 1 | `seller_conditions.md` → `seller_conditions.md` → `tiki_return_policy.md` | Chunk Tiki liên quan xuất hiện ở top-3 nhưng không ở top-1. |
| 2 | `lazada_refund_policy.md` → `seller_conditions.md` → `lazada_refund_policy.md` | Không truy xuất được chunk Shopee trong top-3. |
| 3 | `seller-listing.md` → `ghn_shipping_policy.md` → `seller_conditions.md` | Có tài liệu người bán ở top-1 và top-3, nhưng còn nhiễu GHN. |
| 4 | `lazada_refund_policy.md` → `seller_conditions.md` → `shopee_return_policy.md` | Có Lazada nhưng thiếu GHN, nên chưa đủ dữ liệu để so sánh. |
| 5 | `tiki_return_policy.md` → `seller_conditions.md` → `seller_conditions.md` | Có Tiki ở top-1 nhưng thiếu các nguồn liên quan khác. |

Kết quả này cho thấy pipeline lưu trữ và xếp hạng chạy được khi gọi trực tiếp package cá nhân, nhưng chất lượng retrieval bằng mock embedding thấp và không đủ cơ sở chấm câu trả lời của agent. Muốn đánh giá có ý nghĩa cần chạy lại cùng dữ liệu bằng embedding đa ngữ thật và một `llm_fn` thực tế.

## 6. Đóng góp cá nhân

- Hoàn thiện các chức năng chunking và similarity trong `src/ChuTuanViet_2A202601082/chunking.py`.
- Hoàn thiện lưu trữ, tìm kiếm, lọc metadata và xóa document trong `src/ChuTuanViet_2A202601082/store.py`.
- Hoàn thiện luồng RAG cơ bản trong `src/ChuTuanViet_2A202601082/agent.py`.
- Bổ sung kiểm tra tham số cho `FixedSizeChunker`.
- Bổ sung `src/__init__.py` để hoàn thiện cấu trúc package mà bộ test yêu cầu.
- Chạy và xác nhận toàn bộ 42/42 test đều pass trên Python 3.11.
- Chạy trực tiếp package cá nhân để kiểm tra thống kê chunking, similarity và top-3 retrieval trên dữ liệu nhóm.

## 7. Kết luận

Fixed-size chunking là baseline đơn giản và dễ kiểm soát, nhưng có thể cắt ngang ranh giới ngữ nghĩa tự nhiên. Sentence chunking giữ câu hoàn chỉnh tốt hơn, còn recursive chunking linh hoạt với tài liệu có cấu trúc. Package cá nhân hiện vượt qua toàn bộ 42 test về cấu trúc và hành vi. Kết quả benchmark hiện tại cũng chỉ ra rõ giới hạn của mock embedding: code retrieval chạy được nhưng thứ hạng chưa phản ánh đúng ngữ nghĩa tiếng Việt.
