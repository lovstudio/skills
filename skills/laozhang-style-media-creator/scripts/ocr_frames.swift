import Foundation
import Vision
import ImageIO

guard CommandLine.arguments.count == 2 else {
    fputs("usage: ocr-frames MEASUREMENTS_DIRECTORY\n", stderr)
    exit(2)
}
let root = URL(fileURLWithPath: CommandLine.arguments[1])
let manager = FileManager.default
let dirs = try manager.contentsOfDirectory(at: root, includingPropertiesForKeys: nil)
for directory in dirs where directory.hasDirectoryPath {
    let dest = directory.appendingPathComponent("ocr.json")
    if manager.fileExists(atPath: dest.path) { continue }
    let files = try manager.contentsOfDirectory(at: directory, includingPropertiesForKeys: nil)
        .filter { $0.lastPathComponent.hasPrefix("frame-") && $0.pathExtension == "jpg" }
        .sorted { $0.lastPathComponent < $1.lastPathComponent }
    guard files.count == 12 else { continue }
    var rows: [[String: Any]] = []
    for file in files {
        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.recognitionLanguages = ["zh-Hans", "en-US"]
        request.usesLanguageCorrection = false
        let faces = VNDetectFaceRectanglesRequest()
        let handler = VNImageRequestHandler(url: file, options: [:])
        try handler.perform([request, faces])
        func box(_ r: CGRect) -> [String: Double] {
            return ["x": r.origin.x, "y": 1-r.origin.y-r.height, "width": r.width, "height": r.height]
        }
        let texts: [[String: Any]] = (request.results ?? []).compactMap { observation in
            guard let top = observation.topCandidates(1).first else { return nil }
            return ["text": top.string, "confidence": top.confidence, "bbox": box(observation.boundingBox)]
        }
        let faceBoxes = (faces.results ?? []).map { box($0.boundingBox) }
        let time = Double(file.deletingPathExtension().lastPathComponent.replacingOccurrences(of: "frame-", with: "")) ?? 0
        rows.append(["image": file.lastPathComponent, "time_seconds": time, "texts": texts, "faces": faceBoxes])
    }
    let data = try JSONSerialization.data(withJSONObject: rows, options: [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes])
    try data.write(to: dest, options: .atomic)
    print("ocr sample=\(directory.lastPathComponent) frames=\(rows.count)")
}
