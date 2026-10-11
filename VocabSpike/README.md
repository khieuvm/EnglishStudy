# VocabSpike — Dự án đo đạc trước khi xây app thật

Đây **không phải** app sản phẩm. Đây là dự án đo 3 thứ mà **không có tài liệu nào của Apple trả lời được** — bắt buộc phải đo trên iPhone thật:

| Spike | Câu hỏi cần trả lời | Ảnh hưởng tới sản phẩm |
|---|---|---|
| **1. Refresh** | Widget màn hình khoá thực tế cập nhật bao nhiêu lần/ngày? | Quyết định chu kỳ xoay từ mặc định (1h / 4h / 8h / 24h) |
| **2. Layout** | Từ + nghĩa tiếng Việt dài bao nhiêu ký tự thì bị cắt? | Quyết định độ dài nghĩa khi biên tập dữ liệu |
| **3. Interactive** | Nút "Từ tiếp theo" có bấm được khi máy đang khoá không? | Quyết định có làm nút này hay không |

> **Dự đoán trước khi đo** (từ tài liệu Apple): refresh ~40–70 lần/ngày, nút **KHÔNG** chạy khi máy còn khoá. Mục tiêu của spike là **xác nhận bằng số liệu thật trên máy bạn**, không phải tin vào tài liệu.

---

## Yêu cầu

- macOS + Xcode 15 trở lên
- iPhone thật chạy iOS 17 trở lên (⚠️ Simulator **không** phản ánh đúng hành vi refresh)
- Apple ID (tài khoản miễn phí là đủ cho spike — chỉ cần nhớ provisioning profile miễn phí hết hạn sau 7 ngày, xem mục Lưu ý)

---

## Cài đặt — Cách A: XcodeGen (khuyên dùng)

```bash
# 1. Copy thư mục VocabSpike sang Mac, rồi cd vào đó
cd VocabSpike

# 2. Đổi bundle ID + App Group thành của bạn
chmod +x rename.sh
./rename.sh com.tenban vocabspike

# 3. Cài XcodeGen (nếu chưa có) và sinh project
brew install xcodegen
xcodegen generate

# 4. Mở project
open VocabSpike.xcodeproj
```

Sau khi mở Xcode:

1. Chọn target **VocabSpike** → tab **Signing & Capabilities** → chọn **Team** của bạn.
2. Bấm **+ Capability** → thêm **App Groups** → bấm **+** → nhập đúng App Group vừa đổi ở bước 2 (ví dụ `group.com.tenban.vocabspike`).
3. Lặp lại bước 1–2 cho target **VocabSpikeWidgetExtension**. **Phải cùng một App Group** thì widget mới ghi log cho app đọc được.
4. Chọn scheme **VocabSpike**, chọn iPhone thật, bấm **⌘R**.

## Cài đặt — Cách B: Tạo thủ công trong Xcode

<details>
<summary>Bấm để xem (dùng khi không muốn cài XcodeGen)</summary>

1. Xcode → **File > New > Project > iOS > App**. Tên `VocabSpike`, Interface **SwiftUI**, Language **Swift**. Bỏ chọn Core Data/Tests.
2. **File > New > Target > iOS > Widget Extension**. Tên `VocabSpikeWidgetExtension`. **Bỏ chọn** "Include Live Activity" và **bỏ chọn** "Include Configuration App Intent". Bấm **Activate** khi Xcode hỏi.
3. Xoá các file mẫu Xcode tự sinh trong cả 2 target (`ContentView.swift`, `VocabSpikeWidgetExtension.swift`, `VocabSpikeWidgetExtensionBundle.swift`, `AppIntent.swift`).
4. Kéo thả các file từ `Sources/` vào Xcode, chú ý **Target Membership** (cột bên phải):
   | Thư mục | Thuộc target nào |
   |---|---|
   | `Sources/Shared/*.swift` | ✅ VocabSpike **và** ✅ VocabSpikeWidgetExtension |
   | `Sources/App/*.swift` | ✅ Chỉ VocabSpike |
   | `Sources/Widget/*.swift` | ✅ Chỉ VocabSpikeWidgetExtension |
5. Với **cả 2 target**: tab **Signing & Capabilities** → **+ Capability** → **App Groups** → thêm cùng một group `group.com.tenban.vocabspike`.
6. Mở `Sources/Shared/SpikeConfig.swift`, sửa `appGroupID` cho khớp.
7. Đặt **Minimum Deployment** = **iOS 17.0** cho cả 2 target.

</details>

---

## Chạy spike

### Bước 1 — Cài app lên iPhone

Build & run, mở app một lần. App sẽ đặt mốc bắt đầu đo. **Rút cáp ra, dùng máy bình thường.**

### Bước 2 — Thêm widget vào màn hình khoá

1. Nhấn giữ màn hình khoá → **Tuỳ chỉnh** → **Màn hình khoá**.
2. Bấm vào vùng widget **dưới đồng hồ** → tìm **VocabSpike** → thêm **Spike · Đo refresh** (chọn ô chữ nhật).
3. Bấm vào vùng **trên đồng hồ** (dòng nhỏ) → thêm **Spike · Đo refresh** (dạng inline).
4. Thêm tiếp **Spike · Đo layout** vào một màn hình khoá **thứ hai** để so sánh (Tuỳ chỉnh → thêm màn hình khoá mới).
5. Thêm cả 2 widget ra **màn hình chính** để so sánh refresh giữa lock screen và home screen.

### Bước 3 — Dùng máy bình thường 3–5 ngày

Quan trọng: **đừng mở app liên tục**. Mở app sẽ làm widget refresh miễn phí (không tính ngân sách) và làm sai số liệu. Apple cũng nói hệ thống cần **vài ngày để học thói quen người dùng** — đo 1 ngày đầu sẽ ra kết quả thấp giả tạo.

Mỗi lần mở khoá máy, chỉ cần **liếc nhìn dòng `trễ ...`** trên widget:
- Các slot cách nhau 30 phút. Nếu thấy `trễ 5 phút` → hệ thống bám sát lịch, rất tốt.
- Nếu thấy `trễ 3 giờ` → hệ thống đang hiển thị entry cũ, refresh bị bóp.

### Bước 4 — Kiểm tra nút tương tác (spike 3)

1. Khi màn hình **còn khoá** (chưa Face ID): bấm nút mũi tên `→` trên widget. Ghi nhớ bạn đã bấm mấy lần.
2. Mở khoá, mở app, xem mục **"Số lần bấm nút widget"**.
3. **Nếu số đó = 0** → xác nhận đúng tài liệu Apple: nút không chạy khi máy khoá → **nút "Từ tiếp theo" trên màn hình khoá là vô dụng cho trường hợp "vừa cầm máy lên"**.
4. Mở khoá rồi bấm lại ở màn hình khoá → số phải tăng.

### Bước 5 — Chụp ảnh đo layout (spike 2)

Widget **Spike · Đo layout** xoay vòng qua 4 chế độ, mỗi chế độ 5 phút:

| Chế độ | Nội dung | Cần ghi nhận |
|---|---|---|
| 0 · Thước đo | `123456789_` lặp lại ở 3 cỡ chữ | Đếm được bao nhiêu ký tự trước khi bị cắt (ở từng cỡ chữ) |
| 1 · 2 dòng | `ubiquitous` + `phổ biến khắp nơi` | Có vừa không, có bị xuống dòng không |
| 2 · 3 dòng | từ + loại từ + nghĩa dài | Nghĩa dài bị cắt ở đâu |
| 3 · Câu ví dụ | câu tiếng Anh đầy đủ | Câu ví dụ có hiển thị nổi trên lock screen không |

Chụp màn hình cả 4 chế độ. **Nhớ test với dấu tiếng Việt** — dấu mũ/dấu thanh làm chữ cao hơn và có thể bị cắt ở dòng cuối.

> Ngoài ra, kiểm tra ở **cả 2 kiểu hình nền**: nền sáng và nền tối. Widget màn hình khoá iPhone luôn bị ép về **chế độ đơn sắc (vibrant)**, không bao giờ có màu đầy đủ.

### Bước 6 — Đọc kết quả

Mở app, mục **Kết quả đo refresh**:

- **Reload / ngày** — con số quan trọng nhất. So với trần 40–70 Apple công bố.
- **Khoảng cách trung vị** — chu kỳ xoay từ của sản phẩm thật **không nên ngắn hơn** con số này.
- Bấm **Xuất log dạng CSV** → AirDrop sang Mac → mở bằng Numbers/Excel để vẽ biểu đồ theo giờ trong ngày (sẽ thấy ban đêm gần như không refresh).

---

## Kết luận cần rút ra

Điền vào bảng này sau 3–5 ngày, rồi mang sang bước thiết kế sản phẩm thật:

```
Reload thực tế / ngày      : ______
Khoảng cách trung vị       : ______
Khoảng cách dài nhất       : ______
→ Chu kỳ xoay từ mặc định  : ______

Số ký tự vừa accessoryRectangular, cỡ .caption2 : ______ ký tự × ______ dòng
Số ký tự vừa accessoryInline                    : ______ ký tự
→ Giới hạn độ dài nghĩa tiếng Việt khi biên tập : ______ ký tự

Nút bấm khi máy còn khoá có chạy không? : CÓ / KHÔNG
→ Có làm nút "Từ tiếp theo" không?       : CÓ / KHÔNG
```

---

## Lưu ý

- **Tài khoản Apple ID miễn phí**: provisioning profile hết hạn sau **7 ngày**, app sẽ ngừng chạy. Nếu muốn đo đủ 5–7 ngày liền mạch, hoặc đăng ký Apple Developer Program ($99/năm), hoặc build lại vào ngày thứ 6 (build lại **không** xoá dữ liệu trong App Group).
- **Đừng bật Low Power Mode** trong thời gian đo — chế độ này bóp refresh rất mạnh và sẽ cho kết quả bi quan giả tạo.
- Nếu widget hiện "không có dữ liệu" hoặc log trống: 99% là **App Group chưa khớp** giữa 2 target. Kiểm tra lại `SpikeConfig.appGroupID` và cả 2 file `.entitlements`.
