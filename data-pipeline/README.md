# Data Pipeline — Dựng dataset từ vựng Anh–Việt

Sinh ra file **`out/vocab.sqlite`** để nhúng thẳng vào app iOS, cùng bản JSON để
kiểm tra bằng mắt và các file báo cáo chất lượng.

## Nguồn dữ liệu (đã kiểm tra giấy phép)

| Nguồn | Lấy gì | Dùng thương mại |
|---|---|---|
| **WordNet 3.0** (Princeton) | Định nghĩa tiếng Anh, loại từ, câu ví dụ, từ đồng nghĩa | ✅ Miễn phí, chỉ cần giữ copyright notice |
| **vi.wiktionary.org** | **Nghĩa tiếng Việt** | ✅ CC BY-SA 4.0 — phải ghi nguồn |
| **en.wiktionary.org** | Phiên âm IPA (US/UK) | ✅ CC BY-SA 4.0 — phải ghi nguồn |
| **wordfreq** | Tần suất từ → xếp hạng & ước lượng CEFR | ✅ MIT |

**Không dùng** Oxford 3000/5000 (không có giấy phép công khai), COCA bản đầy đủ
(phải mua), Merriam-Webster API (gói free chỉ phi thương mại). Chi tiết trong
`out/ATTRIBUTIONS.md` do pipeline tự sinh — **nội dung này bắt buộc hiển thị trong app**.

---

## Cách chạy

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python build.py --limit 200        # chạy thử nhanh
python build.py --limit 3000       # dựng bộ thật
python build.py --limit 3000 --offline   # dùng lại cache, không gọi mạng
```

> ⚠️ Mở `vocabpipe/wiktionary.py` và sửa hằng `USER_AGENT` thành email thật của bạn.
> Wikimedia yêu cầu User-Agent có thông tin liên hệ.

### Tham số

| Tham số | Ý nghĩa |
|---|---|
| `--limit N` | Số từ phổ biến nhất cần xử lý |
| `--offline` | Chỉ dùng cache, không gọi mạng |
| `--no-lemmatize` | Không quy dạng biến thể về dạng gốc |
| `--include-incomplete` | Xuất cả từ chưa có nghĩa tiếng Việt |
| `--max-senses N` | Số nghĩa WordNet lấy tối đa mỗi từ |

---

## Kết quả thực tế (chạy với `--limit 1200`)

| Chỉ số | Giá trị |
|---|---|
| Từ xuất ra (có đủ nghĩa Anh + Việt) | **1.092** (91% ứng viên) |
| Có phiên âm IPA | **98%** |
| Có câu ví dụ tiếng Anh | **78%** |
| Thiếu nghĩa tiếng Việt | 49 từ → `out/missing-vietnamese.txt` |
| Cần soát loại từ thủ công | 22 từ → `out/needs-review.txt` |
| Kích thước SQLite | ~512 KB |

Ngoại suy: `--limit 5000` sẽ cho khoảng 4.000–4.500 từ, SQLite khoảng 2 MB —
thừa sức nhúng vào app bundle.

---

## File xuất ra

```
out/
├── vocab.sqlite            ← nhúng vào app iOS
├── vocab.json              ← xem/kiểm tra bằng mắt, diff giữa các lần chạy
├── ATTRIBUTIONS.md         ← BẮT BUỘC hiển thị trong app
├── missing-vietnamese.txt  ← từ cần bổ sung nghĩa Việt thủ công
├── needs-review.txt        ← từ cần soát lại loại từ
└── http-cache.sqlite       ← cache Wiktionary, đừng xoá (chạy lại sẽ rất nhanh)
```

### Lược đồ `vocab.sqlite`

```sql
words(id, headword, rank, zipf, cefr, pos, pos_vi, ipa_us, ipa_uk,
      definition_en, definition_vi, definition_vi_alt, vi_source,
      example_en, synonyms)

decks(id, slug, name_vi, description_vi, cefr, word_count)
deck_words(deck_id, word_id, position)
meta(key, value)
```

`definition_vi_alt` và `synonyms` lưu dạng chuỗi JSON.

---

## Deck tự biên soạn (TOEIC / IELTS)

Thả file `.txt` vào thư mục `curated/`:

```
# name: TOEIC 600
# description: Từ vựng nền cho mục tiêu TOEIC 600
# cefr: B1
account
agreement
...
```

Từ nào chưa có trong dataset sẽ được báo ra màn hình khi chạy — tăng `--limit`
hoặc thêm từ đó thủ công.

> ⚠️ **Bản quyền**: các danh sách "600 từ TOEIC" / "3000 từ IELTS" trôi nổi trên
> mạng hầu hết là bản biên soạn có bản quyền của nhà xuất bản. Copy nguyên si vào
> app thương mại là vi phạm. Hãy tự chọn từ hoặc dùng nguồn có giấy phép rõ ràng.

---

## Các quyết định kỹ thuật đáng chú ý

### 1. Xếp hạng nghĩa theo corpus SemCor, không theo thứ tự WordNet

`wn.synsets()` trả danh từ trước bất kể thực tế. Nếu lấy phần tử đầu tiên:

| Từ | Nghĩa sai (thứ tự mặc định) | Nghĩa đúng (xếp theo SemCor) |
|---|---|---|
| get | *"cú đỡ bóng tưởng không thể đỡ được"* (quần vợt) | **"có được, kiếm được"** |
| see | *"toà giám mục"* | **"nhìn thấy"** |
| think | *"một lần suy nghĩ"* (danh từ) | **"nghĩ, suy nghĩ"** |

Pipeline dùng `lemma.count()` (tần suất trong corpus SemCor) để xếp hạng.
Đây chính là lỗi phân loại mà nhiều app đối thủ đang mắc.

### 2. Khớp loại từ giữa hai ngôn ngữ

Chỉ xét loại từ mà **cả WordNet và vi.wiktionary đều có**, rồi chọn loại từ có
tần suất SemCor cao nhất. Nhờ vậy nghĩa Anh và nghĩa Việt nói về cùng một nghĩa,
không còn cảnh nghĩa Anh là danh từ còn nghĩa Việt là động từ.

Nếu loại từ chọn được yếu hơn hẳn loại từ phổ biến nhất (vi.wiktionary thiếu mục),
từ đó được ghi vào `needs-review.txt` thay vì âm thầm cho qua.

### 3. vi.wiktionary tách động từ thành hai template

`{{-intr-verb-}}` (nội động từ) và `{{-trans-verb-}}` (ngoại động từ). Bỏ sót hai
template này khiến **hầu hết động từ bị gán nhầm thành danh từ** (số động từ trong
dataset tăng từ 89 lên 181 sau khi sửa).

Cũng lưu ý `{{-pron-}}` trong vi.wiktionary là **phát âm**, không phải đại từ.

### 4. Quy dạng biến thể về dạng gốc

"years" và "year" phải là **một** mục trong app học từ vựng, và vi.wiktionary cũng
chỉ có mục cho dạng gốc. Pipeline dùng `wn._morphy()` để lấy toàn bộ dạng gốc khả
dĩ rồi chọn theo tần suất:

- `years → year`, `took → take`, `best → good`, `using → use`
- `data → data` (giữ nguyên, vì "datum" hiếm hơn hẳn)

Nhờ bước này, số từ thiếu nghĩa tiếng Việt giảm từ 180 xuống 46.

### 5. Lọc danh từ riêng

WordNet đánh dấu thực thể có tên riêng bằng `instance_hypernyms()`. Nhờ đó loại bỏ
*texas, russia, africa, germany, india* khỏi danh sách từ vựng, trong khi vẫn giữ
*japan* (sơn mài), *trump* (quân bài), *smith* (thợ rèn) — đều là từ chung hợp lệ.

### 6. Chống rate limit

Wikimedia trả HTTP 429 khi gọi quá nhanh. Pipeline retry với backoff luỹ thừa và
tôn trọng header `Retry-After`. Lô thất bại **không** được ghi vào cache để lần
chạy sau thử lại. Trước khi có cơ chế này, độ phủ IPA chỉ đạt 87%; sau khi có là 98%.

---

## Việc còn phải làm thủ công

1. **`out/missing-vietnamese.txt`** — bổ sung nghĩa tiếng Việt cho các từ
   vi.wiktionary chưa có.
2. **`out/needs-review.txt`** — soát lại loại từ.
3. **Khớp nghĩa ở mức chi tiết hơn loại từ** — pipeline mới khớp được loại từ, chưa
   khớp được từng nghĩa cụ thể. Ví dụ "wear": nghĩa Anh là *"be dressed in"* nhưng
   nghĩa Việt lấy phải *"mòn đi"* (vi.wiktionary xếp nội động từ trước). Cần người
   soát bộ lõi (~2000 từ phổ biến nhất).
4. **Câu ví dụ** — 22% số từ chưa có câu ví dụ do WordNet không cung cấp.
