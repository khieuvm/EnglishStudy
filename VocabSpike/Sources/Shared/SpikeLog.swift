import Foundation

/// Một dòng log ghi lại sự kiện đo đạc.
struct SpikeLogEntry: Codable, Identifiable, Hashable {

    enum Kind: String, Codable {
        case timelineRequested
        case buttonTapped
        case appForegrounded
        case manualReload

        var label: String {
            switch self {
            case .timelineRequested: return "WidgetKit xin timeline"
            case .buttonTapped:      return "Bấm nút trên widget"
            case .appForegrounded:   return "Mở app"
            case .manualReload:      return "Reload thủ công"
            }
        }
    }

    var id: UUID = UUID()
    let kind: Kind
    let timestamp: Date
    let detail: String
}

/// Ghi log dạng JSONL vào file trong App Group container, để widget extension
/// và app chính cùng đọc/ghi được.
///
/// Dùng JSONL (mỗi dòng 1 JSON) thay vì mảng JSON để append rẻ và không hỏng
/// file khi extension bị kill giữa chừng.
enum SpikeLog {

    private static let fileName = "spike-log.jsonl"

    private static let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        return encoder
    }()

    private static let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()

    static var fileURL: URL? {
        FileManager.default
            .containerURL(forSecurityApplicationGroupIdentifier: SpikeConfig.appGroupID)?
            .appendingPathComponent(fileName)
    }

    static func append(kind: SpikeLogEntry.Kind, detail: String) {
        append(SpikeLogEntry(kind: kind, timestamp: Date(), detail: detail))
    }

    static func append(_ entry: SpikeLogEntry) {
        guard let fileURL, var line = try? encoder.encode(entry) else { return }
        line.append(0x0A)

        if FileManager.default.fileExists(atPath: fileURL.path) {
            guard let handle = try? FileHandle(forWritingTo: fileURL) else { return }
            defer { try? handle.close() }
            _ = try? handle.seekToEnd()
            try? handle.write(contentsOf: line)
        } else {
            try? line.write(to: fileURL, options: .atomic)
        }
    }

    static func load() -> [SpikeLogEntry] {
        guard let fileURL,
              let data = try? Data(contentsOf: fileURL),
              let text = String(data: data, encoding: .utf8) else { return [] }

        return text
            .split(separator: "\n", omittingEmptySubsequences: true)
            .compactMap { line in
                guard let lineData = line.data(using: .utf8) else { return nil }
                return try? decoder.decode(SpikeLogEntry.self, from: lineData)
            }
    }

    static func clear() {
        guard let fileURL else { return }
        try? FileManager.default.removeItem(at: fileURL)
    }

    /// Xuất toàn bộ log dạng CSV để dán vào Excel/Sheets mà phân tích.
    static func exportCSV() -> String {
        let formatter = ISO8601DateFormatter()
        var rows = ["timestamp,kind,detail"]
        for entry in load().sorted(by: { $0.timestamp < $1.timestamp }) {
            let detail = entry.detail.replacingOccurrences(of: ",", with: ";")
            rows.append("\(formatter.string(from: entry.timestamp)),\(entry.kind.rawValue),\(detail)")
        }
        return rows.joined(separator: "\n")
    }
}
