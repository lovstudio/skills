import Foundation
import Vision
import AppKit

let args = CommandLine.arguments
guard args.count > 1 else {
    print("{\"error\":\"usage: vision_ocr <image>...\"}")
    exit(1)
}

for path in args.dropFirst() {
    guard let image = NSImage(contentsOfFile: path),
          let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        print("{\"file\":\"\(path)\",\"error\":\"cannot-load\"}")
        continue
    }

    let request = VNRecognizeTextRequest { request, error in
        if let error = error {
            print("{\"file\":\"\(path)\",\"error\":\"\(error.localizedDescription)\"}")
            return
        }
        let observations = (request.results as? [VNRecognizedTextObservation]) ?? []
        var lines: [[String: Any]] = []
        for obs in observations {
            guard let candidate = obs.topCandidates(1).first else { continue }
            let bb = obs.boundingBox
            lines.append([
                "text": candidate.string,
                "x": Double(bb.origin.x),
                "y": Double(bb.origin.y),
                "w": Double(bb.size.width),
                "h": Double(bb.size.height),
                "conf": Double(candidate.confidence)
            ])
        }
        lines.sort { a, b in
            let ay = a["y"] as! Double
            let by = b["y"] as! Double
            if abs(ay - by) > 0.012 { return ay > by }
            return (a["x"] as! Double) < (b["x"] as! Double)
        }
        let object: [String: Any] = ["file": path, "lines": lines]
        if let data = try? JSONSerialization.data(withJSONObject: object, options: []) {
            if let output = String(data: data, encoding: .utf8) {
                print(output)
            }
        }
    }
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["zh-Hans", "en-US"]
    request.usesLanguageCorrection = true

    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    do {
        try handler.perform([request])
    } catch {
        print("{\"file\":\"\(path)\",\"error\":\"\(error.localizedDescription)\"}")
    }
}
