import SwiftUI
import WidgetKit

@main
struct VocabSpikeApp: App {

    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            DashboardView()
        }
        .onChange(of: scenePhase) { _, newPhase in
            guard newPhase == .active else { return }
            _ = SpikeStore.installedAt // đặt mốc đo lần đầu chạy
            SpikeLog.append(kind: .appForegrounded, detail: "scenePhase=active")
        }
    }
}
