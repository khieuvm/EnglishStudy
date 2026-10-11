import Foundation

/// Bộ đếm chia sẻ giữa app chính và widget extension qua App Group UserDefaults.
enum SpikeStore {

    private enum Key {
        static let timelineRequestCount = "timelineRequestCount"
        static let buttonTapCount = "buttonTapCount"
        static let lastTimelineRequestAt = "lastTimelineRequestAt"
        static let installedAt = "installedAt"
    }

    private static var defaults: UserDefaults? {
        UserDefaults(suiteName: SpikeConfig.appGroupID)
    }

    /// Gọi mỗi lần WidgetKit yêu cầu timeline mới. Trả về số thứ tự lần gọi.
    @discardableResult
    static func incrementTimelineRequestCount() -> Int {
        guard let defaults else { return -1 }
        let next = defaults.integer(forKey: Key.timelineRequestCount) + 1
        defaults.set(next, forKey: Key.timelineRequestCount)
        defaults.set(Date(), forKey: Key.lastTimelineRequestAt)
        return next
    }

    @discardableResult
    static func incrementButtonTapCount() -> Int {
        guard let defaults else { return -1 }
        let next = defaults.integer(forKey: Key.buttonTapCount) + 1
        defaults.set(next, forKey: Key.buttonTapCount)
        return next
    }

    static var timelineRequestCount: Int {
        defaults?.integer(forKey: Key.timelineRequestCount) ?? 0
    }

    static var buttonTapCount: Int {
        defaults?.integer(forKey: Key.buttonTapCount) ?? 0
    }

    static var lastTimelineRequestAt: Date? {
        defaults?.object(forKey: Key.lastTimelineRequestAt) as? Date
    }

    /// Mốc bắt đầu đo, đặt lần đầu app chạy. Dùng để tính số reload/ngày.
    static var installedAt: Date {
        if let existing = defaults?.object(forKey: Key.installedAt) as? Date {
            return existing
        }
        let now = Date()
        defaults?.set(now, forKey: Key.installedAt)
        return now
    }

    static func resetAll() {
        guard let defaults else { return }
        [Key.timelineRequestCount, Key.buttonTapCount,
         Key.lastTimelineRequestAt, Key.installedAt].forEach(defaults.removeObject(forKey:))
        SpikeLog.clear()
    }
}
