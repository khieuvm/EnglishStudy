# Plan: App học từ vựng tiếng Anh qua Widget màn hình khóa (iOS)

## 0. Tiến độ hiện tại

| Hạng mục | Trạng thái |
|---|---|
| Nghiên cứu thị trường & khả năng kỹ thuật | ✅ Xong |
| Mã nguồn 3 spike ([`VocabSpike/`](../VocabSpike)) | ✅ Viết xong, **chờ bạn chạy trên iPhone thật** |
| Data pipeline ([`data-pipeline/`](../data-pipeline)) | ✅ Xong và đã chạy kiểm chứng |
| Dataset mẫu 1.092 từ Anh–Việt | ✅ Đã sinh ra, kiểm tra toàn vẹn OK |
| App chính + widget sản phẩm | ⏳ Chờ kết quả spike |

**Việc bạn cần làm tiếp theo:** clone repo về Mac, mở thư mục [`VocabSpike/`](../VocabSpike),
cài lên iPhone và để chạy 3–5 ngày. Xem hướng dẫn trong [`VocabSpike/README.md`](../VocabSpike/README.md).

---

## 1. Bối cảnh & quyết định đã chốt

| Hạng mục | Lựa chọn |
|---|---|
| Phạm vi | Widget-first + iCloud sync + nhiều bộ từ (TOEIC/IELTS/giao tiếp) + phát âm |
| Đối tượng | Người Việt học tiếng Anh — UI tiếng Việt, nghĩa song ngữ Anh–Việt |
| Kinh nghiệm dev | Biết lập trình, chưa từng làm iOS/SwiftUI → plan có bước học/setup |
| Thiết bị | Có Mac + iPhone thật để test |

---

## 2. Phát hiện quan trọng nhất từ nghiên cứu

> **⚠️ Sự thật kỹ thuật phải chấp nhận trước khi bắt đầu:**
> **iOS KHÔNG cho phép widget đổi nội dung mỗi lần mở khóa máy.** Không có API, không có Shortcuts trigger, không có cách lách nào. **Không một app nào trong 15 app đã khảo sát làm được điều này** — tất cả đều xoay vòng theo lịch định sẵn.

**Bằng chứng:**
- Apple quy định rõ ngân sách refresh: *"a daily budget typically includes from **40 to 70 refreshes**... roughly every 15 to 60 minutes"* ([Apple docs](https://developer.apple.com/documentation/widgetkit/keeping-a-widget-up-to-date)). Người dùng mở khóa máy 80–150 lần/ngày → bất khả thi về mặt toán học.
- Danh sách trigger của Shortcuts không có "khi mở khóa" ([Apple Support](https://support.apple.com/guide/shortcuts/add-automations-apdfbdbd7123/ios)).
- Silent push và Background App Refresh **cũng bị giới hạn ngân sách** ("budgeted... delivered opportunistically") — không phải cách lách.
- App open-source `keepline` ghi thẳng trong tài liệu: *"A line does not change on every unlock."*

**→ Hệ quả cho sản phẩm:** Thiết kế UX xoay quanh **xoay vòng theo lịch có thể cấu hình** (như Lingo Widget: 4h/8h/12h/24h). Marketing phải nói **"từ mới mỗi giờ / nhiều lần trong ngày"**, TUYỆT ĐỐI không nói "mỗi lần mở khóa" — vì đó là rủi ro bị từ chối theo App Store Guideline 2.3.1(a) (metadata sai sự thật).

### Ràng buộc WidgetKit cần biết
| Điều | Chi tiết |
|---|---|
| Loại widget khóa màn hình | `accessoryInline` (1 dòng), `accessoryCircular` (icon/gauge), `accessoryRectangular` (**nhiều dòng — dùng cái này cho từ + nghĩa**) |
| Màu sắc | Màn hình khóa iPhone **luôn ép chế độ đơn sắc `.vibrant`** — không bao giờ có full màu. Thiết kế phải đẹp ở dạng trắng/mờ. |
| Kích thước | Apple **không công bố pixel cụ thể** — phải dùng `ViewThatFits` + đo thực nghiệm trong Xcode Preview |
| Nút bấm tương tác | iOS 17+ `Button(intent:)` được hỗ trợ, nhưng **"trên thiết bị đang khóa, nút không hoạt động trừ khi người dùng xác thực mở khóa"**. Reload do bấm nút thì **được đảm bảo 100%**, không tính vào ngân sách. |
| Quảng cáo | **Cấm quảng cáo trong widget** (Guideline 2.5.16/2.5.18) |

### Khoảng trống thị trường (cơ hội khác biệt hóa)
1. **Không app nào kết hợp SRS thật (FSRS/SM-2) với widget** — tất cả chỉ random/tuần tự. Đây là ngách trống rõ ràng.
2. Đối thủ bị chê nhiều nhất: widget không cập nhật, **paywall chặn lịch sử từ đã lưu**, sync lỗi, crash, phân loại độ khó sai (app của Dogan Ekici bị chê hiển thị "cosmic" là từ nâng cao).
3. Thị trường VN: Vocadaily, VocabNote, eJOY đều **không lấy widget làm trung tâm** → ngách widget-first song ngữ còn trống.
4. Nút "Từ tiếp theo" tương tác trên màn hình khóa: gần như chưa đối thủ nào làm.

### Đối thủ đáng theo dõi nhất
| App | Rating/Reviews | Điểm đáng học |
|---|---|---|
| Vocabulary – Learn words daily (Monkey Taps) | 4.77★ / 219,646 | Dẫn đầu thị trường, nhưng widget bị chê "hỏng nhiều tháng" |
| Word of the Day・Vocabulary (Vocabulous) | 4.67★ / 38,953 | Widget có minh họa đẹp |
| WordUp (Geeks) | 4.76★ / 13,845 | Gamification + AI, nhưng bị chê crash/sync lỗi |
| **Lingo Widget** (Oguz Doruk) | 4.74★ / 101 | **Cho chọn chu kỳ 4h/8h/12h/24h — mô hình trung thực nhất, nên copy** |
| Vocabulary Widget (Kawaii) | 4.2★ / 5 | Home widget và Lock widget có layout riêng biệt |
| Vocadaily (VN) | 4.6★ / 324 | Đối thủ VN gần nhất |

### Nguồn dữ liệu hợp pháp (quan trọng — tránh rắc rối bản quyền)
| Nguồn | Dùng thương mại được? |
|---|---|
| **WordNet (Princeton)** | ✅ Cho phép rõ ràng, miễn phí, chỉ cần giữ copyright notice |
| **Wiktionary / Kaikki.org** | ✅ CC BY-SA 4.0 — phải ghi nguồn + share-alike phần dữ liệu |
| **COCA top-5000** | ✅ Bản 5000 từ đầu miễn phí (bản đầy đủ phải mua) |
| **AVSpeechSynthesizer (Apple)** | ✅ Miễn phí, offline, có sẵn trong SDK — **dùng cái này cho phát âm** |
| Oxford 3000/5000 | ❌ Không có license công khai — **phải tránh** |
| Merriam-Webster API | ❌ Free tier chỉ phi thương mại |
| NGSL | ⚠️ Nói là "free, open-source" nhưng không có trang license — cần hỏi trực tiếp |

### Thuật toán lặp lại ngắt quãng
- **FSRS** (`open-spaced-repetition`) — **MIT**, chính xác hơn SM-2, đang được maintain tích cực.
- **`4rays/swift-fsrs`** — MIT, bản port Swift dùng được luôn làm dependency.
- ⚠️ **Tránh** `JuliusBrussee/revu-swift` (GPL-3.0 — copyleft, không copy vào app thương mại).
- Tham khảo kiến trúc: **`kyledold/WordOfTheDay`** (MIT) — SwiftUI + Widget, gần nhất với dự án này.

---

## 3. Kiến trúc đề xuất

```
VocabWidget.xcodeproj
├── VocabWidgetApp/          (app chính, SwiftUI)
│   ├── Features/            Home, WordList, Study, Settings, Decks
│   ├── Core/                SRS engine (FSRS), TTS, Scheduler
│   └── Data/                SwiftData models + CloudKit sync
├── VocabWidgetExtension/    (Widget Extension)
│   ├── Provider/            TimelineProvider (sinh 24-48 entry/ngày)
│   ├── Views/               Lock: inline/circular/rectangular; Home: small/medium
│   └── Intents/             AppIntent "Từ tiếp theo", "Đã thuộc", "Lưu từ"
└── Shared/ (App Group)      Models, bộ từ, logic chọn từ dùng chung
```

**Quyết định kỹ thuật:**
- **SwiftData + CloudKit** (`.automatic`) cho đồng bộ iCloud — không cần backend, không cần tài khoản, miễn phí. (Yêu cầu iOS 17+.)
- **App Group** để app chính và widget extension chia sẻ cùng một store.
- **Deployment target: iOS 17.0** — cần cho interactive widget và SwiftData. (iOS 16 thì mất nút bấm.)
- **Cơ chế widget:** `getTimeline` trả về **một mảng nhiều entry đã tính trước** (ví dụ 24–48 slot/ngày, cách nhau ≥5 phút), mỗi slot gắn sẵn 1 từ do FSRS chọn. Đây là pattern Apple thiết kế sẵn, không tốn ngân sách refresh.
- **Phát âm:** `AVSpeechSynthesizer` (offline, miễn phí). Widget không phát được âm thanh → nút phát âm chỉ có trong app.
- **Dữ liệu từ vựng:** đóng gói sẵn file JSON/SQLite trong bundle (offline-first), không phụ thuộc API lúc chạy.

---

## 4. Danh sách công việc

### Giai đoạn 0 — Học nền tảng & setup
- `setup-xcode` — Cài Xcode, tạo Apple ID dev, bật Developer Mode trên iPhone, chạy thử app "Hello World" lên máy thật.
- `learn-swiftui` — Học Swift + SwiftUI cơ bản (State/Binding, List, NavigationStack, Sheet) qua Apple Tutorials + 100 Days of SwiftUI (chỉ cần phần SwiftUI).
- `learn-widgetkit` — Học WidgetKit: xem WWDC22 "Complications and widgets: Reloaded" + WWDC23 "Bring widgets to life". Đọc code `kyledold/WordOfTheDay`.

### Giai đoạn 1 — Spike kỹ thuật (BẮT BUỘC làm trước khi xây sản phẩm)

> ✅ **Mã nguồn đã viết xong** tại [`VocabSpike/`](../VocabSpike) — gồm cả 3 spike trong một
> project duy nhất, có sẵn `project.yml` cho XcodeGen và hướng dẫn chi tiết.
> Chỉ còn bước chạy trên iPhone thật.

- `spike-widget-refresh` — **Việc quan trọng nhất của cả dự án.** Widget đẩy 48 slot/ngày, ghi log mỗi lần `getTimeline` vào App Group, app chính tính ra số reload/ngày và khoảng cách trung vị. Theo dõi 3–5 ngày. Kết quả quyết định chu kỳ mặc định của sản phẩm.
- `spike-lockscreen-layout` — Widget xoay vòng 4 chế độ đo: thước đếm ký tự, 2 dòng, 3 dòng, câu ví dụ. Chụp ảnh so sánh ở chế độ đơn sắc.
- `spike-interactive-intent` — Nút `Button(intent:)` ghi log mỗi lần bấm, để xác minh nút có chạy khi máy còn khóa hay không.

### Giai đoạn 2 — Dữ liệu & nội dung

> ✅ **Pipeline đã xong và chạy kiểm chứng** tại [`data-pipeline/`](../data-pipeline).
> Kết quả với `--limit 1200`: **1.092 từ** có đủ nghĩa Anh + Việt, **98%** có IPA,
> **78%** có câu ví dụ, SQLite 512 KB. Chạy `python build.py --limit 5000` để dựng bộ thật.

- `build-wordlist` — ✅ Xong. WordNet (định nghĩa EN, cho phép dùng thương mại) + wordfreq (tần suất → CEFR). Đã loại danh từ riêng và quy dạng biến thể về dạng gốc. **Không** dùng Oxford 3000/5000.
- `translate-vietnamese` — ⏳ Tự động hoá xong (nguồn: **vi.wiktionary.org**, CC BY-SA, độ phủ 96%). Còn lại: soát thủ công `out/missing-vietnamese.txt` (49 từ) và `out/needs-review.txt` (22 từ), cùng việc khớp nghĩa chi tiết cho ~2000 từ lõi.
- `build-decks` — ⏳ Deck tự sinh theo tần suất/CEFR đã xong (core-500, core-1500, core-3000, cefr-a1…c2). Deck TOEIC/IELTS cần bạn tự biên soạn, thả file `.txt` vào `curated/` (có file mẫu `toeic-600.txt`).
- `data-pipeline` — ✅ Xong. Xuất `vocab.sqlite` + `vocab.json` + `ATTRIBUTIONS.md` + báo cáo chất lượng. Có cache HTTP, retry chống rate-limit.

### Giai đoạn 3 — App chính
- `data-layer` — Định nghĩa model SwiftData (Word, Deck, ReviewLog, UserSettings), bật CloudKit sync, cấu hình App Group.
- `srs-engine` — Tích hợp FSRS (dùng `4rays/swift-fsrs` hoặc tự port từ `py-fsrs`). Hàm `nextDueWords(count:)` để widget và app cùng gọi.
- `app-ui-core` — Màn hình chính (từ hôm nay), danh sách bộ từ, chi tiết từ (nghĩa, phiên âm IPA, ví dụ, nút phát âm).
- `app-study-flow` — Luồng học: flashcard lật thẻ, đánh giá 4 mức (Again/Hard/Good/Easy) feed vào FSRS, quiz trắc nghiệm.
- `app-history` — **Lịch sử & sổ tay từ đã lưu, KHÔNG paywall** (đây là điểm đối thủ bị chê nhiều nhất).
- `app-settings` — Cài đặt: chọn bộ từ đang học, **chu kỳ xoay widget (1h/4h/8h/24h)**, bật/tắt thông báo, tình trạng đồng bộ iCloud.
- `tts` — Phát âm qua `AVSpeechSynthesizer`, giọng en-US/en-GB, có nút nghe lại.

### Giai đoạn 4 — Widget
- `widget-lockscreen` — 3 family màn hình khóa: inline (chỉ từ), circular (tiến độ hôm nay), rectangular (từ + loại từ + nghĩa Việt).
- `widget-homescreen` — small/medium với layout riêng, nhiều thông tin hơn, hỗ trợ màu đầy đủ.
- `widget-timeline` — `TimelineProvider` sinh entry theo chu kỳ người dùng chọn, lấy từ qua FSRS, chính sách `.after(date)` + reload khi app foreground.
- `widget-interactive` — AppIntent "Từ tiếp theo" / "Đã thuộc" / "Lưu từ" trên widget (nhớ: chỉ chạy khi máy đã mở khóa).
- `widget-config` — `AppIntentConfiguration` cho phép người dùng chọn bộ từ ngay trên widget mà không cần mở app.
- `notifications` — Thông báo cục bộ theo giờ làm kênh bổ sung (hợp lệ theo Guideline 2.5.4, khác với lạm dụng background refresh).

### Giai đoạn 5 — Hoàn thiện & phát hành
- `polish-ux` — Onboarding, trang hướng dẫn "cách thêm widget vào màn hình khóa" (đối thủ hay thiếu → nguồn review 1 sao), Dark Mode, Dynamic Type, VoiceOver.
- `test-device` — Test trên iPhone thật nhiều ngày: xác minh sync iCloud 2 máy, widget cập nhật đúng, không crash, pin không hao bất thường.
- `monetization` — Mô hình: miễn phí hoàn toàn phần lõi (widget + học + lịch sử), Pro mở khóa bộ từ nâng cao/thống kê/không giới hạn bộ từ. Tránh dark pattern.
- `appstore-prep` — Screenshot, mô tả (**không dùng cụm "mỗi lần mở khóa"**), privacy nutrition label, ATTRIBUTIONS cho WordNet/Wiktionary, chính sách bảo mật.
- `submit` — Nộp TestFlight → thu phản hồi → nộp App Store Review.

---

## 5. Rủi ro & cách xử lý

| Rủi ro | Mức độ | Xử lý |
|---|---|---|
| Widget cập nhật ít hơn kỳ vọng | **Cao** | `spike-widget-refresh` làm trước tiên; đặt chu kỳ mặc định bảo thủ (4h); trong app giải thích minh bạch |
| Bị từ chối vì metadata sai sự thật (2.3.1a) | Trung bình | Không bao giờ viết "mỗi lần mở khóa" trong mô tả/screenshot |
| Bị từ chối vì "chỉ là vỏ bọc widget" (4.2) | Trung bình | App chính phải có luồng học đầy đủ (flashcard, quiz, thống kê) |
| CloudKit sync xung đột giữa widget và app | Trung bình | Widget **chỉ đọc**, mọi ghi dữ liệu đi qua app chính hoặc AppIntent |
| License dữ liệu | Trung bình | Chỉ dùng WordNet + Wiktionary + COCA-5000; có trang ATTRIBUTIONS trong app |
| Chất lượng bản dịch tiếng Việt | Trung bình | Người soát bộ lõi 2000 từ; có nút báo lỗi trong app |
| Thị trường bão hòa | Trung bình | Khác biệt bằng: SRS thật + song ngữ + không paywall lịch sử + minh bạch chu kỳ |

---

## 6. Khoảng trống nghiên cứu còn lại

- Giá subscription của đối thủ **không xác minh được** (chỉ 2/15 app công khai giá) — cần kiểm tra thủ công trên App Store bằng iPhone.
- Reddit / Stack Overflow / Apple Dev Forums **không truy cập được** trong phiên nghiên cứu → thiếu các chia sẻ thực chiến của dev khác. Nên tự tra cứu thêm thủ công.
- **Kích thước pixel chính xác của widget màn hình khóa không tồn tại trong tài liệu Apple** — bắt buộc phải đo bằng Xcode Preview (đã đưa vào `spike-lockscreen-layout`).

---

## 7. Bước tiếp theo ngay

1. **Clone repo về Mac → mở [`VocabSpike/`](../VocabSpike) → cài lên iPhone → để chạy 3–5 ngày.**
   Đây là đường găng: kết quả quyết định chu kỳ xoay từ và giới hạn độ dài nghĩa.
2. Trong lúc chờ spike: chạy `python build.py --limit 5000` để dựng dataset đầy đủ,
   rồi soát `out/needs-review.txt` và `out/missing-vietnamese.txt`.
3. Song song: học SwiftUI (Apple Tutorials / 100 Days of SwiftUI).
4. Khi có số liệu spike → điền vào bảng kết luận cuối `VocabSpike/README.md` → bắt
   đầu Giai đoạn 3 (app chính).
