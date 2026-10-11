import Foundation

/// Tính toán thống kê từ log — đây chính là KẾT QUẢ của spike đo refresh.
struct SpikeAnalysis {

    let totalReloads: Int
    let measuredDuration: TimeInterval
    let reloadsPerDay: Double
    let gaps: [TimeInterval]

    var medianGap: TimeInterval? {
        guard !gaps.isEmpty else { return nil }
        let sorted = gaps.sorted()
        let mid = sorted.count / 2
        return sorted.count % 2 == 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid]
    }

    var shortestGap: TimeInterval? { gaps.min() }
    var longestGap: TimeInterval? { gaps.max() }

    /// So với ngân sách Apple công bố: 40–70 lần refresh/ngày.
    var verdict: String {
        guard measuredDuration >= 3600 else {
            return "Chưa đủ dữ liệu — cần chạy ít nhất 1 giờ, lý tưởng là 3–5 ngày."
        }
        switch reloadsPerDay {
        case ..<10:  return "Rất thấp (<10/ngày). Chu kỳ an toàn nên đặt 8–24 giờ."
        case ..<25:  return "Thấp (10–25/ngày). Chu kỳ an toàn: 4–8 giờ."
        case ..<45:  return "Trung bình (25–45/ngày). Chu kỳ an toàn: 1–4 giờ."
        default:     return "Cao (>45/ngày), sát trần Apple công bố. Chu kỳ 1 giờ khả thi."
        }
    }

    static func make(from entries: [SpikeLogEntry], since: Date) -> SpikeAnalysis {
        let reloads = entries
            .filter { $0.kind == .timelineRequested }
            .map(\.timestamp)
            .sorted()

        let duration = max(Date().timeIntervalSince(since), 1)
        let perDay = Double(reloads.count) / (duration / 86_400)

        var gaps: [TimeInterval] = []
        for index in 1..<max(reloads.count, 1) where reloads.count > 1 {
            gaps.append(reloads[index].timeIntervalSince(reloads[index - 1]))
        }

        return SpikeAnalysis(
            totalReloads: reloads.count,
            measuredDuration: duration,
            reloadsPerDay: perDay,
            gaps: gaps
        )
    }

    static func format(_ interval: TimeInterval?) -> String {
        guard let interval else { return "—" }
        let formatter = DateComponentsFormatter()
        formatter.allowedUnits = [.day, .hour, .minute]
        formatter.unitsStyle = .abbreviated
        formatter.maximumUnitCount = 2
        return formatter.string(from: interval) ?? "—"
    }
}
