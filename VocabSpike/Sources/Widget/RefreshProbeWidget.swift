import SwiftUI
import WidgetKit

/// SPIKE 1 — đo tần suất WidgetKit THỰC SỰ cập nhật widget trên máy thật.
///
/// Cách đo gồm 2 tín hiệu độc lập:
///
/// 1. **Số lần gọi `getTimeline`** — ghi vào log mỗi lần hệ thống xin timeline mới.
///    Đây là tín hiệu chính xác nhất về ngân sách refresh (Apple công bố 40–70/ngày).
///
/// 2. **Độ trễ hiển thị** — widget in ra `Text(entry.date, style: .relative)`.
///    Chuỗi này TỰ ĐỘNG đếm lên mà KHÔNG tốn ngân sách refresh. Nếu các slot cách
///    nhau 30 phút mà bạn liếc màn hình khóa thấy "trễ 2 giờ", nghĩa là hệ thống
///    đang hiển thị entry cũ và không kịp nhảy slot.
struct RefreshProbeEntry: TimelineEntry {
    let date: Date
    let slotIndex: Int
    let totalSlots: Int
    let generatedAt: Date
    let reloadCount: Int
}

struct RefreshProbeProvider: TimelineProvider {

    func placeholder(in context: Context) -> RefreshProbeEntry {
        RefreshProbeEntry(
            date: .now,
            slotIndex: 0,
            totalSlots: SpikeConfig.slotsPerTimeline,
            generatedAt: .now,
            reloadCount: 0
        )
    }

    func getSnapshot(in context: Context, completion: @escaping (RefreshProbeEntry) -> Void) {
        completion(placeholder(in: context))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<RefreshProbeEntry>) -> Void) {
        let now = Date()
        let reloadCount = SpikeStore.incrementTimelineRequestCount()

        SpikeLog.append(
            kind: .timelineRequested,
            detail: "family=\(context.family) slots=\(SpikeConfig.slotsPerTimeline) "
                  + "interval=\(Int(SpikeConfig.slotInterval / 60))m preview=\(context.isPreview)"
        )

        // Đẩy SẴN nhiều entry trong MỘT lần gọi — đây là pattern Apple thiết kế
        // cho đúng nhu cầu "đổi nội dung theo lịch" mà không tốn thêm refresh.
        let entries = (0..<SpikeConfig.slotsPerTimeline).map { index in
            RefreshProbeEntry(
                date: now.addingTimeInterval(SpikeConfig.slotInterval * Double(index)),
                slotIndex: index,
                totalSlots: SpikeConfig.slotsPerTimeline,
                generatedAt: now,
                reloadCount: reloadCount
            )
        }

        // Xin timeline mới khi slot cuối đã được dùng.
        let nextRefresh = entries.last?.date ?? now.addingTimeInterval(SpikeConfig.slotInterval)
        completion(Timeline(entries: entries, policy: .after(nextRefresh)))
    }
}

struct RefreshProbeView: View {

    @Environment(\.widgetFamily) private var family
    let entry: RefreshProbeEntry

    var body: some View {
        content
    }

    @ViewBuilder
    private var content: some View {
        switch family {

        case .accessoryInline:
            // Chỉ 1 dòng, không icon phụ, không nút bấm được.
            Text("S\(entry.slotIndex) · trễ \(entry.date, style: .relative)")

        case .accessoryCircular:
            Gauge(value: Double(entry.slotIndex),
                  in: 0...Double(max(entry.totalSlots - 1, 1))) {
                Text("S")
            } currentValueLabel: {
                Text("\(entry.slotIndex)")
            }
            .gaugeStyle(.accessoryCircular)

        case .accessoryRectangular:
            HStack(spacing: 4) {
                VStack(alignment: .leading, spacing: 0) {
                    Text("slot \(entry.slotIndex)/\(entry.totalSlots - 1) · r\(entry.reloadCount)")
                        .font(.headline)
                    Text("trễ \(entry.date, style: .relative)")
                    Text(entry.generatedAt, format: .dateTime.day().month().hour().minute())
                }
                .font(.caption2)
                .minimumScaleFactor(0.8)

                Spacer(minLength: 0)

                // SPIKE 3: nút này phải KHÔNG chạy khi máy còn khóa.
                Button(intent: NextWordIntent()) {
                    Image(systemName: "arrow.forward.circle")
                }
                .buttonStyle(.plain)
            }

        default:
            VStack(alignment: .leading, spacing: 4) {
                Text("Slot \(entry.slotIndex) / \(entry.totalSlots - 1)")
                    .font(.headline)
                Text("Độ trễ: \(entry.date, style: .relative)")
                Text("Timeline #\(entry.reloadCount)")
                Text("Tạo lúc \(entry.generatedAt, format: .dateTime.day().month().hour().minute())")
                    .foregroundStyle(.secondary)

                Button(intent: NextWordIntent()) {
                    Label("Từ tiếp theo", systemImage: "arrow.forward")
                }
                .buttonStyle(.bordered)
            }
            .font(.caption)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        }
    }
}

struct RefreshProbeWidget: Widget {

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: SpikeConfig.refreshWidgetKind,
                            provider: RefreshProbeProvider()) { entry in
            RefreshProbeView(entry: entry)
                .containerBackground(.fill.tertiary, for: .widget)
        }
        .configurationDisplayName("Spike · Đo refresh")
        .description("Đo tần suất widget thực sự được cập nhật.")
        .supportedFamilies([
            .accessoryInline,
            .accessoryCircular,
            .accessoryRectangular,
            .systemSmall,
            .systemMedium
        ])
    }
}
