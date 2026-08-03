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
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [ ] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [ ] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| | | | |
| | | | |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Chu Tuấn Việt]**
- **Loại chiến lược:** [FixedSize]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
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
| Chu Tuấn Việt | FixedSize | [8-10] | Chunk nhất quán, dễ xử lý; quản lý kích thước dễ dự đoán | Có thể cắt thông tin quan trọng ở ranh giới chunk |
| Hà Xuân Sơn | Sentence | [8-10] | Giữ ngữ cảnh tốt; chunk là câu hoàn chỉnh | Số lượng chunk bất đều; câu dài gây vấn đề |
| Vũ Quốc Anh | Recursive | [8-10] | Cân bằng kích thước & ngữ cảnh; phù hợp nhiều chủ đề | Phức tạp hơn; chậm hơn khi dữ liệu lớn |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
