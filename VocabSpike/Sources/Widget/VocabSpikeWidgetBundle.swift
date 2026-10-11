import SwiftUI
import WidgetKit

@main
struct VocabSpikeWidgetBundle: WidgetBundle {
    var body: some Widget {
        RefreshProbeWidget()
        LayoutProbeWidget()
    }
}
