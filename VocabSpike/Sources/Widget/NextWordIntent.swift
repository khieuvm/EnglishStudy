import AppIntents
import WidgetKit

/// SPIKE 3 — kiểm chứng nút tương tác trên widget màn hình khóa (iOS 17+).
///
/// Điều cần xác minh trên máy thật:
/// 1. Khi màn hình ĐANG KHÓA (chưa Face ID): theo tài liệu Apple, nút KHÔNG chạy.
///    "On a locked device, buttons and toggles are inactive and the system doesn't
///     perform actions unless a person authenticates and unlocks their device."
/// 2. Khi đã mở khóa nhưng vẫn ở màn hình khóa: nút chạy được, và reload do
///    tương tác là ĐƯỢC ĐẢM BẢO (không tính vào ngân sách 40–70/ngày).
///
/// Cách đọc kết quả: mỗi lần bấm sẽ ghi 1 dòng `buttonTapped` vào log.
/// So sánh số lần bạn bấm thực tế với số dòng log để biết nút có "nuốt" lần bấm nào không.
struct NextWordIntent: AppIntent {

    static let title: LocalizedStringResource = "Từ tiếp theo"
    static let description = IntentDescription("Nhảy sang từ kế tiếp trên widget.")

    /// Không cần mở app khi bấm — đây là điểm mấu chốt của interactive widget.
    static let openAppWhenRun: Bool = false

    func perform() async throws -> some IntentResult {
        let count = SpikeStore.incrementButtonTapCount()
        SpikeLog.append(kind: .buttonTapped, detail: "lần bấm #\(count)")

        // WidgetKit tự reload sau khi perform() xong, nhưng gọi tường minh để
        // chắc chắn cả 2 widget cùng cập nhật.
        WidgetCenter.shared.reloadTimelines(ofKind: SpikeConfig.refreshWidgetKind)

        return .result()
    }
}
