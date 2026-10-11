import SwiftUI
import WidgetKit

/// Bảng điều khiển của spike: đọc log từ App Group, tính thống kê, xuất CSV.
struct DashboardView: View {

    @State private var entries: [SpikeLogEntry] = []
    @State private var analysis: SpikeAnalysis?
    @State private var showingResetAlert = false

    var body: some View {
        NavigationStack {
            List {
                resultSection
                checklistSection
                logSection
                actionsSection
            }
            .navigationTitle("VocabSpike")
            .refreshable { reload() }
            .onAppear { reload() }
            .alert("Xoá toàn bộ dữ liệu đo?", isPresented: $showingResetAlert) {
                Button("Huỷ", role: .cancel) {}
                Button("Xoá", role: .destructive) {
                    SpikeStore.resetAll()
                    reload()
                }
            } message: {
                Text("Mốc đo sẽ bắt đầu lại từ đầu.")
            }
        }
    }

    // MARK: - Kết quả spike

    @ViewBuilder
    private var resultSection: some View {
        Section("Kết quả đo refresh") {
            if let analysis {
                LabeledContent("Thời gian đo", value: SpikeAnalysis.format(analysis.measuredDuration))
                LabeledContent("Tổng số lần reload", value: "\(analysis.totalReloads)")
                LabeledContent("Reload / ngày", value: String(format: "%.1f", analysis.reloadsPerDay))
                LabeledContent("Khoảng cách ngắn nhất", value: SpikeAnalysis.format(analysis.shortestGap))
                LabeledContent("Khoảng cách trung vị", value: SpikeAnalysis.format(analysis.medianGap))
                LabeledContent("Khoảng cách dài nhất", value: SpikeAnalysis.format(analysis.longestGap))
                LabeledContent("Số lần bấm nút widget", value: "\(SpikeStore.buttonTapCount)")

                Text(analysis.verdict)
                    .font(.callout)
                    .foregroundStyle(.secondary)

                Text("Tham chiếu: Apple công bố ngân sách 40–70 lần refresh/ngày cho widget được xem thường xuyên.")
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
            } else {
                Text("Chưa có dữ liệu.").foregroundStyle(.secondary)
            }
        }
    }

    // MARK: - Checklist quan sát thủ công

    private var checklistSection: some View {
        Section("Việc cần quan sát bằng mắt") {
            checklistRow("Thêm widget 'Spike · Đo refresh' vào màn hình KHOÁ (cả 3 vị trí: trên đồng hồ, dưới đồng hồ)")
            checklistRow("Mỗi lần mở khoá, liếc xem dòng 'trễ ...' là bao nhiêu — đây là độ trễ thực tế")
            checklistRow("Thử bấm nút mũi tên KHI MÁY CÒN KHOÁ → theo tài liệu Apple nút phải KHÔNG chạy")
            checklistRow("Bấm lại SAU KHI Face ID → số 'lần bấm nút' ở trên phải tăng")
            checklistRow("Chụp màn hình widget 'Spike · Đo layout' ở cả 4 chế độ để đếm số ký tự bị cắt")
            checklistRow("Để máy chạy bình thường 3–5 ngày rồi mới đọc kết quả")
        }
    }

    private func checklistRow(_ text: String) -> some View {
        Label(text, systemImage: "circle")
            .font(.caption)
            .labelStyle(.titleAndIcon)
    }

    // MARK: - Log

    private var logSection: some View {
        Section("Log (\(entries.count) dòng)") {
            if entries.isEmpty {
                Text("Chưa có log. Thêm widget vào màn hình khoá rồi quay lại.")
                    .foregroundStyle(.secondary)
            } else {
                ForEach(entries.prefix(100)) { entry in
                    VStack(alignment: .leading, spacing: 2) {
                        HStack {
                            Text(entry.kind.label).font(.caption).bold()
                            Spacer()
                            Text(entry.timestamp, format: .dateTime.day().month().hour().minute().second())
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                        Text(entry.detail)
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
    }

    // MARK: - Hành động

    private var actionsSection: some View {
        Section {
            Button {
                WidgetCenter.shared.reloadAllTimelines()
                SpikeLog.append(kind: .manualReload, detail: "reloadAllTimelines")
                reload()
            } label: {
                Label("Reload widget thủ công", systemImage: "arrow.clockwise")
            }

            ShareLink(item: SpikeLog.exportCSV()) {
                Label("Xuất log dạng CSV", systemImage: "square.and.arrow.up")
            }

            Button(role: .destructive) {
                showingResetAlert = true
            } label: {
                Label("Xoá dữ liệu đo", systemImage: "trash")
            }
        } footer: {
            Text("App Group: \(SpikeConfig.appGroupID)\nSlot: \(SpikeConfig.slotsPerTimeline) × \(Int(SpikeConfig.slotInterval / 60)) phút")
                .font(.caption2)
        }
    }

    private func reload() {
        let loaded = SpikeLog.load().sorted { $0.timestamp > $1.timestamp }
        entries = loaded
        analysis = SpikeAnalysis.make(from: loaded, since: SpikeStore.installedAt)
    }
}

#Preview {
    DashboardView()
}
