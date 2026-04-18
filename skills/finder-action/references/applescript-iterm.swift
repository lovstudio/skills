// AppleScript snippet for opening iTerm2 at a specific path
// Use inside FinderSync.swift menuAction

func openInITerm(at path: String) {
    let escapedPath = path.replacingOccurrences(of: "'", with: "'\\''")
    let script = """
    tell application "iTerm"
        activate
        tell current window
            create tab with default profile
            tell current session
                write text "cd '\(escapedPath)'"
            end tell
        end tell
    end tell
    """

    var error: NSDictionary?
    if let appleScript = NSAppleScript(source: script) {
        appleScript.executeAndReturnError(&error)
        if let error = error {
            NSLog("AppleScript error: \(error)")
        }
    }
}

// For Terminal.app instead of iTerm:
func openInTerminal(at path: String) {
    let escapedPath = path.replacingOccurrences(of: "'", with: "'\\''")
    let script = """
    tell application "Terminal"
        activate
        do script "cd '\(escapedPath)'"
    end tell
    """

    var error: NSDictionary?
    if let appleScript = NSAppleScript(source: script) {
        appleScript.executeAndReturnError(&error)
    }
}
