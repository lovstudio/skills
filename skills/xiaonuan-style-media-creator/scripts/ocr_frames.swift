import Foundation
import Vision
// usage: ocr_frames FRAMES_DIR OUT_JSON   (frames named t-<seconds>.jpg; compile with swiftc -O)
let args = CommandLine.arguments
guard args.count == 3 else { fputs("usage: ocr_frames FRAMES_DIR OUT_JSON\n", stderr); exit(2) }
let dir = URL(fileURLWithPath: args[1])
let files = try FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil)
    .filter { $0.pathExtension == "jpg" }.sorted { $0.lastPathComponent < $1.lastPathComponent }
var rows: [[String: Any]] = []
for f in files {
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.recognitionLanguages = ["zh-Hans", "en-US"]
    req.usesLanguageCorrection = false
    let handler = VNImageRequestHandler(url: f, options: [:])
    try handler.perform([req])
    let texts: [[String: Any]] = (req.results ?? []).compactMap { o in
        guard let top = o.topCandidates(1).first else { return nil }
        let r = o.boundingBox
        return ["text": top.string, "confidence": top.confidence,
                "bbox": ["x": r.origin.x, "y": 1 - r.origin.y - r.height, "width": r.width, "height": r.height]]
    }
    let name = f.deletingPathExtension().lastPathComponent
    let t = Double(name.replacingOccurrences(of: "t-", with: "")) ?? -1
    rows.append(["time_seconds": t, "texts": texts])
}
let data = try JSONSerialization.data(withJSONObject: rows, options: [.prettyPrinted, .sortedKeys])
try data.write(to: URL(fileURLWithPath: args[2]), options: .atomic)
print("ocr frames=\(rows.count) -> \(args[2])")
