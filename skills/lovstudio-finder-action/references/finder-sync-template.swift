import Cocoa
import FinderSync

class FinderSync: FIFinderSync {

    override init() {
        super.init()
        FIFinderSyncController.default().directoryURLs = [URL(fileURLWithPath: "/")]
    }

    override func menu(for menuKind: FIMenuKind) -> NSMenu? {
        // .contextualMenuForContainer = blank-space right-click
        // .contextualMenuForItems    = file/folder right-click
        guard menuKind == .contextualMenuForContainer else { return nil }

        let menu = NSMenu(title: "")
        let item = NSMenuItem(
            title: "MENU_TITLE",
            action: #selector(menuAction(_:)),
            keyEquivalent: ""
        )
        item.image = NSImage(systemSymbolName: "SF_SYMBOL_NAME", accessibilityDescription: nil)
        menu.addItem(item)
        return menu
    }

    @objc func menuAction(_ sender: AnyObject?) {
        guard let target = FIFinderSyncController.default().targetedURL() else { return }
        // ACTION_IMPLEMENTATION
    }
}
