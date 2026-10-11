# EnglishStudy

Dự án app iOS học từ vựng tiếng Anh qua **widget màn hình khóa**, dành cho người Việt.

> **Trạng thái:** giai đoạn đo đạc kỹ thuật + dựng dữ liệu. Chưa bắt đầu app sản phẩm.

---

## ⚠️ Đọc cái này trước khi làm bất cứ thứ gì

**iOS KHÔNG cho phép widget đổi nội dung mỗi lần mở khóa máy.** Không có API, không
có Shortcuts trigger, không có cách lách nào.

Bằng chứng:

- Apple quy định ngân sách refresh: *"a daily budget typically includes from **40 to
  70 refreshes**... roughly every 15 to 60 minutes"*
  ([tài liệu Apple](https://developer.apple.com/documentation/widgetkit/keeping-a-widget-up-to-date)).
  Người dùng mở khóa máy 80–150 lần/ngày → bất khả thi về mặt toán học.
- Danh sách trigger của Shortcuts **không có "khi mở khóa"**
  ([Apple Support](https://support.apple.com/guide/shortcuts/add-automations-apdfbdbd7123/ios)).
- Silent push (`content-available`) và Background App Refresh **cũng bị giới hạn ngân
  sách** — Apple nói rõ chúng được "budgeted... delivered opportunistically".
- Khảo sát 15 app cùng loại trên App Store: **không app nào làm được**. App minh bạch
  nhất (Lingo Widget) cho người dùng chọn chu kỳ 4h/8h/12h/24h.

**Hệ quả:**

- Thiết kế UX xoay quanh **xoay vòng theo lịch có thể cấu hình**.
- Mô tả trên App Store **tuyệt đối không viết "mỗi lần mở khóa"** — đây là rủi ro bị
  từ chối theo Guideline 2.3.1(a) (metadata sai sự thật).

---

## Cấu trúc repo

```
EnglishStudy/
├── VocabSpike/       Project Xcode đo 3 thứ Apple không công bố — CHẠY TRƯỚC TIÊN
└── data-pipeline/    Pipeline Python dựng dataset từ vựng Anh–Việt
```

### [`VocabSpike/`](./VocabSpike) — đo đạc trên iPhone thật

Không phải app sản phẩm. Dùng để trả lời 3 câu hỏi mà **không tài liệu nào của Apple
trả lời được**, bắt buộc phải đo thực nghiệm:

| Spike | Câu hỏi | Quyết định điều gì |
|---|---|---|
| Refresh | Widget thực tế cập nhật bao nhiêu lần/ngày? | Chu kỳ xoay từ mặc định |
| Layout | Nghĩa tiếng Việt dài bao nhiêu thì bị cắt? | Giới hạn độ dài khi biên tập dữ liệu |
| Interactive | Nút bấm có chạy khi máy còn khóa không? | Có làm nút "Từ tiếp theo" không |

👉 Hướng dẫn chạy: [`VocabSpike/README.md`](./VocabSpike/README.md)

### [`data-pipeline/`](./data-pipeline) — dựng dataset

Sinh ra `vocab.sqlite` để nhúng thẳng vào app iOS.

Kết quả đã chạy kiểm chứng (`--limit 1200`):

| Chỉ số | Giá trị |
|---|---|
| Từ có đủ nghĩa Anh + Việt | **1.092** |
| Có phiên âm IPA | **98%** |
| Có câu ví dụ tiếng Anh | 78% |
| Kích thước SQLite | 512 KB |

👉 Hướng dẫn chạy: [`data-pipeline/README.md`](./data-pipeline/README.md)

---

## Bắt đầu

### Trên Mac

```bash
git clone https://github.com/khieuvm/EnglishStudy.git
cd EnglishStudy

# 1. Dựng project Xcode đo đạc
cd VocabSpike
chmod +x rename.sh
./rename.sh com.tenban vocabspike     # đổi bundle ID thành của bạn
brew install xcodegen
xcodegen generate
open VocabSpike.xcodeproj
```

Sau đó trong Xcode: chọn Team cho **cả 2 target**, thêm capability **App Groups** với
cùng một group ID, rồi cài lên iPhone thật và **để chạy 3–5 ngày**.

### Dựng lại dataset

```bash
cd data-pipeline
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python build.py --limit 5000
```

> Lần chạy đầu sẽ tải lại cache Wiktionary (~35 MB, không commit vào repo).

---

## Nguồn dữ liệu & giấy phép

| Nguồn | Lấy gì | Dùng thương mại |
|---|---|---|
| **WordNet 3.0** (Princeton) | Định nghĩa EN, loại từ, ví dụ, từ đồng nghĩa | ✅ Miễn phí, giữ copyright notice |
| **vi.wiktionary.org** | Nghĩa tiếng Việt | ✅ CC BY-SA 4.0 — phải ghi nguồn |
| **en.wiktionary.org** | Phiên âm IPA | ✅ CC BY-SA 4.0 — phải ghi nguồn |
| **wordfreq** | Tần suất từ → xếp hạng, CEFR | ✅ MIT |

**Không dùng** (đã kiểm tra, không có giấy phép hợp lệ): Oxford 3000/5000, COCA bản
đầy đủ, Merriam-Webster API (gói free chỉ phi thương mại).

Nội dung trong [`data-pipeline/out/ATTRIBUTIONS.md`](./data-pipeline/out/ATTRIBUTIONS.md)
**bắt buộc hiển thị trong app** (ví dụ ở Cài đặt → Giới thiệu → Nguồn dữ liệu).

---

## Lộ trình

- [x] Nghiên cứu thị trường (15 app) + khả năng kỹ thuật WidgetKit
- [x] Data pipeline + dataset mẫu 1.092 từ
- [ ] **Chạy 3 spike trên iPhone thật (3–5 ngày)** ← đang ở đây
- [ ] Dataset đầy đủ 5.000 từ + soát thủ công
- [ ] App chính: SwiftData + CloudKit, FSRS, flashcard, lịch sử
- [ ] Widget sản phẩm: lock screen + home screen + AppIntent
- [ ] Hoàn thiện, TestFlight, App Store

Kiến trúc dự kiến: **SwiftUI + SwiftData + CloudKit** (sync iCloud không cần backend),
target **iOS 17+**, thuật toán lặp lại ngắt quãng **FSRS** (MIT), phát âm bằng
**AVSpeechSynthesizer** (offline, miễn phí).

> Khoảng trống thị trường tìm được: **không app nào kết hợp SRS thật với widget** —
> tất cả chỉ chọn từ ngẫu nhiên.
