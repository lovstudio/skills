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
        // Support both modes for maximum flexibility
        guard menuKind == .contextualMenuForContainer || menuKind == .contextualMenuForItems else {
            return nil
        }

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
        var targetPath: String

        // Priority: selected folder > current directory
        if let selectedItems = FIFinderSyncController.default().selectedItemURLs(),
           let firstItem = selectedItems.first {
            var isDir: ObjCBool = false
            if FileManager.default.fileExists(atPath: firstItem.path, isDirectory: &isDir), isDir.boolValue {
                targetPath = firstItem.path
            } else {
                targetPath = firstItem.deletingLastPathComponent().path
            }
        } else if let target = FIFinderSyncController.default().targetedURL() {
            targetPath = target.path
        } else {
            return
        }

        // ACTION_IMPLEMENTATION
        // Example: Open terminal at targetPath
        // Example: Create file at targetPath
        // Example: Run AppleScript
    }
}
