import Foundation

/// Cấu hình dùng chung cho cả app và widget extension.
///
/// ⚠️ ĐỔI `appGroupID` cho khớp với App Group bạn tạo trong Apple Developer portal
/// (và khớp với 2 file .entitlements). Phải bắt đầu bằng "group.".
enum SpikeConfig {

    static let appGroupID = "group.com.example.vocabspike"

    static let refreshWidgetKind = "RefreshProbeWidget"
    static let layoutWidgetKind = "LayoutProbeWidget"

    /// Khoảng cách giữa 2 slot trong timeline.
    /// Apple khuyến nghị tối thiểu ~5 phút. Để 30 phút là mức an toàn mà vẫn
    /// đủ dày để quan sát độ trễ refresh thực tế.
    static let slotInterval: TimeInterval = 30 * 60

    /// Số slot đẩy lên trong MỘT lần getTimeline.
    /// 48 slot x 30 phút = phủ 24 giờ chỉ với 1 lần gọi getTimeline.
    static let slotsPerTimeline = 48

    /// Chuỗi thước đo để đếm số ký tự vừa khít trên widget màn hình khóa.
    static let ruler = "123456789_123456789_123456789_123456789_"

    /// Mẫu text thật, song ngữ, để đo giới hạn hiển thị.
    static let sampleHeadword = "ubiquitous"
    static let samplePOS = "adj"
    static let sampleShortVI = "phổ biến khắp nơi"
    static let sampleLongVI = "có mặt ở khắp mọi nơi, phổ biến rộng rãi đến mức ai cũng thấy"
    static let sampleEN = "Smartphones have become ubiquitous in modern life."
}
