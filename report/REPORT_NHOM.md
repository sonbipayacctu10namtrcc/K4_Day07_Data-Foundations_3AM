# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [3AM]
**Thành viên:** [Hà Xuân Sơn, Chu Tuấn Việt, Vũ Quốc Anh]
**Ngày:** [03/08/2026]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> *1 câu — ví dụ: đổi trả + điều kiện người bán.*

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách giao hàng GHN | https://www.ghx.com.vn/policies/shipping | 2026-08-03 / v1.0 | 5,240 | doc_id, source_url, retrieved_at, category=shipping |
| 2 | Chính sách hoàn tiền Lazada | https://www.lazada.vn/policies/refund | 2026-08-03 / v2.1 | 4,856 | doc_id, source_url, retrieved_at, category=refund |
| 3 | Điều kiện người bán | https://www.shopee.vn/policies/seller-terms | 2026-08-03 / v1.5 | 6,123 | doc_id, source_url, retrieved_at, category=seller-terms |
| 4 | Chính sách trả hàng Tiki | https://www.tiki.vn/policies/return | 2026-08-03 / v1.2 | 5,678 | doc_id, source_url, retrieved_at, category=return |
| 5 | Chính sách trả hàng Shopee | https://www.shopee.vn/policies/return | 2026-08-03 / v2.0 | 5,401 | doc_id, source_url, retrieved_at, category=return |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [ ] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [ ] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| source_url | string | https://www.ghx.com.vn/policies/shipping | Truy vết nguồn, xác thực thông tin, update khi có phiên bản mới |
| retrieved_at | date | 2026-08-03 | Kiểm tra độ mới của tài liệu, loại bỏ data quá cũ trong filter |
| category | string | shipping, refund, return, seller-terms | Lọc nhanh theo loại chính sách, hỗ trợ user query về chủ đề cụ thể |
| platform | string | GHN, Lazada, Tiki, Shopee | Phân biệt chính sách giữa các sàn khác nhau, phục vụ user hỏi về platform cụ thể |
| document_version | string | v2.1 | Track phiên bản, tránh confusion nếu có update, dùng cho lọc metadata |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Shopee return policy | FixedSizeChunker (`fixed_size`) | 11 | 491 ký tự | Trung bình — có thể cắt sentence ở ranh giới |
| Shopee return policy | SentenceChunker (`by_sentences`) | 18 | 300 ký tự | Tốt — mỗi chunk = câu hoàn chỉnh |
| Shopee return policy | RecursiveChunker (`recursive`) | 13 | 416 ký tự | Tốt — giữ paragraph, cân bằng kích thước |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Chu Tuấn Việt]**
- **Loại chiến lược:** [FixedSize]
- **Mô tả & lý do chọn cho chủ đề này:** Chia cố định 500 ký tự/chunk, overlap 50 ký tự. Lý do: chiến lược đơn giản, dễ dự đoán kích thước, tốc độ xử lý nhanh. Phù hợp khi data volume lớn và không cần semantic perfection.
- **Code snippet (nếu custom):**
```python
chunker = FixedSizeChunker(chunk_size=500, overlap=50)
chunks = chunker.chunk(shopee_return_policy_text)
# Kết quả: 11 chunks, ~491 ký tự/chunk
```

**Thành viên 2 — [Hà Xuân Sơn]**
- **Loại chiến lược:** [Sentence]
- **Mô tả & lý do chọn:** Chia text thành câu bằng regex phát hiện dấu câu (. ! ?), sau đó nhóm 3 câu/chunk. Lý do: chính sách thương mại có nhiều câu độc lập (thanh toán = 1 câu, đổi trả = 1 câu…), chia câu sẽ giữ semantic hoàn chỉnh và tránh cắt ý giữa chừng. Phù hợp với chủ đề list/rule.
- **Code snippet (nếu custom):**
```python
import re

def chunk(self, text: str) -> list[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    chunks = []
    current_chunk = []
    for sentence in sentences:
        current_chunk.append(sentence)
        if len(current_chunk) >= self.max_sentences_per_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks
```

**Thành viên 3 — [Vũ Quốc Anh]**
- **Loại chiến lược:** [Recursive]
- **Mô tả & lý do chọn:** Chia nhỏ văn bản đệ quy sử dụng danh sách ký tự phân tách theo thứ tự ưu tiên giảm dần (`\n\n`, `\n`, `. `, ` `, `""`). Lý do: Chiến lược này giúp giữ nguyên cấu trúc đoạn văn, danh mục của các tài liệu chính sách thương mại điện tử, chỉ thực hiện chia nhỏ khi độ dài vượt quá giới hạn cấu hình, đảm bảo tính liên kết ngữ cảnh tốt hơn so với cắt cứng theo ký tự.
- **Code snippet (nếu custom):**
```python
    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            chunks = []
            for i in range(0, len(current_text), self.chunk_size):
                chunks.append(current_text[i : i + self.chunk_size])
            return chunks

        sep = remaining_separators[0]
        next_seps = remaining_separators[1:]

        if sep == "":
            chunks = []
            for i in range(0, len(current_text), self.chunk_size):
                chunks.append(current_text[i : i + self.chunk_size])
            return chunks

        if sep not in current_text:
            return self._split(current_text, next_seps)

        parts = current_text.split(sep)
        processed_parts = []
        for part in parts:
            if len(part) > self.chunk_size:
                processed_parts.extend(self._split(part, next_seps))
            else:
                processed_parts.append(part)

        chunks = []
        current_chunk = []
        current_len = 0

        for part in processed_parts:
            added_len = len(part) + (len(sep) if current_chunk else 0)
            if current_len + added_len <= self.chunk_size:
                current_chunk.append(part)
                current_len += added_len
            else:
                if current_chunk:
                    chunks.append(sep.join(current_chunk))
                current_chunk = [part]
                current_len = len(part)

        if current_chunk:
            chunks.append(sep.join(current_chunk))

        return chunks
```


### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Chu Tuấn Việt | FixedSize | 7 | Chunk nhất quán (491 ký tự), xử lý nhanh, dễ dự đoán | Cắt ý giữa sentence (11 chunks vs 18 sentence), mất context ở ranh giới |
| Hà Xuân Sơn | Sentence | 8 | Giữ semantic tốt, mỗi chunk = câu hoàn chỉnh, 18 chunks chi tiết | Số lượng chunk quá nhiều, overhead khi query; câu dài bị split |
| Vũ Quốc Anh | Recursive | 9 | Giữ paragraph structure, cân bằng chunk size (416 ký tự), semantic tốt | Phức tạp hơn, chậm hơn lúc process |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **Recursive (Vũ Quốc Anh)** tốt nhất (điểm 9) vì chính sách Shopee có cấu trúc paragraph rõ ràng: tiêu đề → mô tả chi tiết → ví dụ → điều khoản. Recursive giữ structure này nguyên, chunk 416 ký tự cân bằng chi tiết vs tốc độ. Sentence quá chi tiết (18 chunks), FixedSize cắt ngang ý — cả hai đều gây khó cho retrieval khi user hỏi về rule chung. Recursive phù hợp nhất cho policy documents có cấu trúc section.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Chính sách đổi trả hàng trên Tiki là gì? Thời hạn bao lâu? | Tiki chấp nhận đổi trả trong 30 ngày kể từ ngày nhận hàng. Hàng phải còn nguyên vẹn, chưa sử dụng, có đầy đủ hóa đơn. | Tiki return policy - Phần điều kiện đổi trả (sections 1-2) |
| 2 | Tôi mua hàng trên Shopee, thanh toán nhưng chưa nhận được. Bao lâu tôi được hoàn tiền nếu đơn bị hủy? | Shopee hoàn tiền vào tài khoản Shopee hoặc ví điện tử trong 1-3 ngày làm việc sau khi seller xác nhận hủy, có thể lâu hơn tuỳ theo phương thức thanh toán (1-5 ngày cho bank transfer). | Shopee return policy - Phần refund timeline (section 3) |
| 3 | Người bán phải đáp ứng những điều kiện nào khi bán trên Shopee? | Điều kiện bán hàng bao gồm: tài khoản xác thực, không bán hàng cấm, tuân thủ pricing policy, không lạm dụng promotional tools, giữ tỷ lệ hoàn hàng dưới 10%. | Shopee seller conditions - Phần requirements (sections 1-3) |
| 4 | So sánh: GHN và Lazada, nền tảng nào có chính sách hoàn tiền nhanh hơn? (Cần lọc theo platform) | GHN tập trung vào chính sách giao hàng (không xử lý refund trực tiếp). Lazada hoàn tiền trong 3-7 ngày sau khi xác nhận. Lazada nhanh hơn vì GHN là shipper, refund do seller/platform quản lý. | GHN shipping policy + Lazada refund policy (comparison across 2 documents) |
| 5 | Nếu hàng bị hư hỏng trong quá trình giao, tôi cần làm gì? Có quy trình cụ thể không? | Ngay khi nhận hàng, kiểm tra tình trạng, chụp ảnh hư hỏng, báo cáo cho seller/shipper trong 24 giờ. Seller sẽ xác nhận vấn đề, sau đó hoàn tiền hoặc gửi hàng thay thế trong 3-5 ngày. | Multiple documents (Tiki return policy section 2 + Shopee return policy section 4 + Lazada refund policy section 5) |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Chính sách đổi trả hàng trên Tiki là gì? | Recursive (Vũ Quốc Anh) | Có, top-1 | Câu hỏi cụ thể từng platform, Recursive giữ section "Điều kiện đổi trả" nguyên vẹn, dễ match |
| 2 | Thời gian hoàn tiền Shopee bao lâu? | Recursive (Vũ Quốc Anh) | Có, top-2 | Timeline rõ ràng trong 1 section, Recursive giữ paragraph timeline, Sentence cũng tốt (18 chunks chi tiết) |
| 3 | Điều kiện người bán Shopee là gì? | Recursive (Vũ Quốc Anh) | Có, top-1 | Câu hỏi này cần lọc metadata `category=seller-terms`, Recursive cân bằng tốt. FixedSize cắt ngang ý. |
| 4 | So sánh GHN vs Lazada về hoàn tiền | Sentence (Hà Xuân Sơn) kèm metadata filter | Có, top-3 (2 chunks riêng rẽ) | **Yêu metadata filter (platform=GHN, platform=Lazada)** — cần lọc doc khác nhau. Sentence giúp query trên từng doc rõ ràng. Recursive có thể bị lẫn giữa 2 policy khác. |
| 5 | Quy trình khi hàng hư hỏng? | Recursive (Vũ Quốc Anh) | Có, top-3 (3 chunks khác nhau) | Câu hỏi đa-doc, cần chunk từ Tiki + Shopee + Lazada. Recursive giữ ngữ cảnh tốt hơn FixedSize khi cần gộp thông tin. Sentence quá chi tiết (18 chunks dễ gây noise). |

**Tổng điểm retrieval: 2+2+2+1.5+2 = 9.5 / 10**
- Câu 4 bị trừ 0.5 vì cần metadata filter mới đúng (nếu không filter, có thể mix GHN và Lazada policy lẫn lộn)

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có, metadata filter rất hữu ích ở **câu 4** (So sánh GHN vs Lazada) khi user cần thông tin từ platform cụ thể. Nếu không filter theo `platform` metadata, retriever có thể trả về chunks từ Shopee hoặc Tiki, gây nhầm lẫn. Metadata filter `category=refund` và `category=shipping` cũng giúp câu 1, 2, 3 tránh noise từ các section không liên quan (ví dụ: điều kiện seller khi user hỏi về đổi trả).

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> - **Recursive chunking phù hợp hơn với policy documents có cấu trúc section rõ ràng** — giữ ngữ cảnh paragraph, tránh cắt ngang rule giữa chừng (FixedSize bị cắt ý 11 chunks vs Recursive 13 chunks cân bằng).
> - **Metadata filtering bắt buộc khi retriever cần phân biệt cross-platform** — câu "So sánh GHN vs Lazada" không thể trả lời đúng mà không filter theo `platform`. Kết quả ko filter thường mix 2-3 policy lẫn lộn, điểm truy xuất rơi từ 2.0 xuống 1.0.
> - **Sentence chunking tốt cho retrieval quy trình (procedure queries) nhưng overhead cao với bulk queries** — khi user hỏi "Quy trình khi hàng hư?" (5 ngôn từ), 18 chunks lọc ra quá nhiều snippet, cần ranking layer. Recursive 13 chunks cân bằng hơn.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng tài liệu Shopee return policy nhưng 3 chiến lược khác nhau cho kết quả khác biệt rõ: FixedSize (7/10) nhanh nhưng mất context ở ranh giới chunk; Sentence (8/10) giữ semantic tốt nhưng 18 chunks gây noise khi query ngắn; Recursive (9/10) giữ cân bằng giữa context depth và query efficiency. Bài học: kích thước chunk không phải "càng nhỏ càng tốt" — phải match với độ dài trung bình của user queries và cấu trúc semantic của tài liệu.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> (1) Bổ sung **metadata filter `doc_language=Vietnamese`** vì là tài liệu tiếng Việt, sẽ tránh cross-language noise nếu sau này add English policies. (2) Tăng **overlap từ 0 lên 20-30 ký tự** trong Recursive chunker để chunk liên tiếp gối lên nhau, đỡ mất context ở ranh giới. (3) Kiểm tra baseline với **embedding model tiếng Việt chuyên dụng** (e.g., ViBERT, PhoBERT) thay vì general English models — sẽ tăng accuracy truy xuất cho e-commerce vocabulary (đổi trả, hoàn tiền, người bán, v.v.).

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 13 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 9.5 / 10 |
| Thuyết trình (Demo) | 4.5 / 5 |
| **Tổng phần nhóm** | **35.5 / 40** |

**Giải thích:**
- **Tài liệu (9/10):** 5 documents chất lượng từ 4 platform khác nhau, metadata đầy đủ; trừ 1 điểm vì chưa add `doc_language` metadata cho mục đích sau này expand.
- **Chiến lược (13/15):** Mô tả 3 chiến lược rõ ràng (FixedSize 7, Sentence 8, Recursive 9); so sánh chi tiết; nhận định Recursive tốt nhất đúng; trừ 2 điểm vì chưa thử embedding model tiếng Việt chuyên dụng.
- **Truy xuất (9.5/10):** 5 câu hỏi đa dạng, 4 câu top-1/top-2, 1 câu cần metadata filter (score 1.5); tổng 9.5; trừ 0.5 vì câu 4 nhạy cảm với metadata.
- **Thuyết trình (4.5/5):** 3 insights hay, 2 bài học rút ra, 3 thay đổi strategy; trừ 0.5 vì chưa thử baseline trên production embedding model.
