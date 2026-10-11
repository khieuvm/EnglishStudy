import SwiftUI
import WidgetKit

/// SPIKE 2 — đo giới hạn hiển thị của widget màn hình khóa.
///
/// Apple KHÔNG công bố kích thước pixel của các accessory family, nên cách duy
/// nhất để biết "từ + nghĩa tiếng Việt dài bao nhiêu thì bị cắt" là đo thực nghiệm.
///
/// Widget này xoay vòng qua các chế độ đo, mỗi chế độ 1 phút, để bạn chụp màn hình
/// so sánh. Nhớ quan sát ở chế độ ĐƠN SẮC của màn hình khóa (vibrant) — nơi
/// widget luôn bị ép về một màu, không bao giờ có màu đầy đủ trên iPhone.
enum LayoutProbeMode: Int, CaseIterable {
    case ruler          // đếm số ký tự vừa khít
    case twoLine        // từ + nghĩa ngắn
    case threeLine      // từ + loại từ + nghĩa dài
    case englishExample // câu ví dụ tiếng Anh đầy đủ

    var title: String {
        switch self {
        case .ruler:          return "Thước đo ký tự"
        case .twoLine:        return "2 dòng"
        case .threeLine:      return "3 dòng"
        case .englishExample: return "Câu ví dụ"
        }
    }
}

struct LayoutProbeEntry: TimelineEntry {
    let date: Date
    let mode: LayoutProbeMode
}

struct LayoutProbeProvider: TimelineProvider {

    func placeholder(in context: Context) -> LayoutProbeEntry {
        LayoutProbeEntry(date: .now, mode: .ruler)
    }

    func getSnapshot(in context: Context, completion: @escaping (LayoutProbeEntry) -> Void) {
        completion(placeholder(in: context))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<LayoutProbeEntry>) -> Void) {
        let now = Date()
        // Xoay nhanh qua 4 chế độ để chụp ảnh so sánh, rồi lặp lại.
        let entries = LayoutProbeMode.allCases.enumerated().map { index, mode in
            LayoutProbeEntry(date: now.addingTimeInterval(Double(index) * 300), mode: mode)
        }
        let next = now.addingTimeInterval(Double(LayoutProbeMode.allCases.count) * 300)
        completion(Timeline(entries: entries, policy: .after(next)))
    }
}

struct LayoutProbeView: View {

    @Environment(\.widgetFamily) private var family
    let entry: LayoutProbeEntry

    var body: some View {
        content
            .minimumScaleFactor(1.0) // KHÔNG cho thu nhỏ: muốn thấy chỗ bị cắt thật
    }

    @ViewBuilder
    private var content: some View {
        switch family {

        case .accessoryInline:
            Text(inlineText)

        case .accessoryCircular:
            VStack(spacing: 0) {
                Text("\(entry.mode.rawValue)")
                    .font(.title2)
                Text("mode")
                    .font(.system(size: 8))
            }

        default:
            VStack(alignment: .leading, spacing: 0) {
                switch entry.mode {
                case .ruler:
                    Text(SpikeConfig.ruler).font(.caption2)
                    Text(SpikeConfig.ruler).font(.caption)
                    Text(SpikeConfig.ruler).font(.footnote)

                case .twoLine:
                    Text(SpikeConfig.sampleHeadword).font(.headline)
                    Text(SpikeConfig.sampleShortVI).font(.caption)

                case .threeLine:
                    Text("\(SpikeConfig.sampleHeadword) (\(SpikeConfig.samplePOS))")
                        .font(.headline)
                    Text(SpikeConfig.sampleLongVI).font(.caption2)

                case .englishExample:
                    Text(SpikeConfig.sampleHeadword).font(.headline)
                    Text(SpikeConfig.sampleEN).font(.caption2)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        }
    }

    private var inlineText: String {
        switch entry.mode {
        case .ruler:          return SpikeConfig.ruler
        case .twoLine:        return "\(SpikeConfig.sampleHeadword): \(SpikeConfig.sampleShortVI)"
        case .threeLine:      return "\(SpikeConfig.sampleHeadword): \(SpikeConfig.sampleLongVI)"
        case .englishExample: return SpikeConfig.sampleEN
        }
    }
}

struct LayoutProbeWidget: Widget {

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: SpikeConfig.layoutWidgetKind,
                            provider: LayoutProbeProvider()) { entry in
            LayoutProbeView(entry: entry)
                .containerBackground(.fill.tertiary, for: .widget)
        }
        .configurationDisplayName("Spike · Đo layout")
        .description("Đo số ký tự hiển thị vừa trên widget màn hình khóa.")
        .supportedFamilies([
            .accessoryInline,
            .accessoryCircular,
            .accessoryRectangular,
            .systemSmall,
            .systemMedium
        ])
    }
}

#Preview("Lock · Rectangular", as: .accessoryRectangular) {
    LayoutProbeWidget()
} timeline: {
    LayoutProbeEntry(date: .now, mode: .ruler)
    LayoutProbeEntry(date: .now, mode: .twoLine)
    LayoutProbeEntry(date: .now, mode: .threeLine)
    LayoutProbeEntry(date: .now, mode: .englishExample)
}

#Preview("Lock · Inline", as: .accessoryInline) {
    LayoutProbeWidget()
} timeline: {
    LayoutProbeEntry(date: .now, mode: .ruler)
    LayoutProbeEntry(date: .now, mode: .threeLine)
}
