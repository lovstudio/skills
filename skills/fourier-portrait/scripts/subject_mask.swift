// Usage: swift subject_mask.swift <input-image> <output-image.png> <output-mask.png>
// Uses Apple Vision on-device models (macOS 14+). Writes the orientation-corrected RGB image and an
// 8-bit mask (white = foreground subject) at the same pixel size, then prints one JSON line:
// {"width":W,"height":H,"faces":[[x,y,w,h],...]} in top-left-origin pixels, largest face first.
// Reading through Core Image also makes HEIC selfies work without extra decoders.
import AppKit
import CoreImage
import Foundation
import Vision

func fail(_ msg: String, _ code: Int32) -> Never {
    FileHandle.standardError.write((msg + "\n").data(using: .utf8)!)
    exit(code)
}

func writePNG(_ image: CIImage, _ url: URL, gray: Bool) {
    let ctx = CIContext()
    let cg = gray
        ? ctx.createCGImage(image, from: image.extent, format: .L8, colorSpace: CGColorSpaceCreateDeviceGray())
        : ctx.createCGImage(image, from: image.extent, format: .RGBA8, colorSpace: CGColorSpace(name: CGColorSpace.sRGB)!)
    guard let cg, let png = NSBitmapImageRep(cgImage: cg).representation(using: .png, properties: [:]) else {
        fail("cannot encode \(url.lastPathComponent)", 1)
    }
    do { try png.write(to: url) } catch { fail("cannot write \(url.path): \(error)", 1) }
}

let args = CommandLine.arguments
guard args.count == 4 else { fail("usage: subject_mask.swift <input> <image.png> <mask.png>", 2) }
guard let raw = CIImage(contentsOf: URL(fileURLWithPath: args[1]), options: [.applyOrientationProperty: true]) else {
    fail("cannot read image", 1)
}
// Move the oriented extent to the origin so mask and image share pixel coordinates.
let image = raw.transformed(by: CGAffineTransform(translationX: -raw.extent.minX, y: -raw.extent.minY))
let W = Int(image.extent.width), H = Int(image.extent.height)
writePNG(image, URL(fileURLWithPath: args[2]), gray: false)

let maskRequest = VNGenerateForegroundInstanceMaskRequest()
let faceRequest = VNDetectFaceRectanglesRequest()
let handler = VNImageRequestHandler(ciImage: image, options: [:])
do { try handler.perform([maskRequest, faceRequest]) } catch { fail("vision failed: \(error)", 1) }

guard let result = maskRequest.results?.first, !result.allInstances.isEmpty else {
    fail("no foreground subject found", 3)
}
let buffer = try result.generateScaledMaskForImage(forInstances: result.allInstances, from: handler)
writePNG(CIImage(cvPixelBuffer: buffer), URL(fileURLWithPath: args[3]), gray: true)

// Vision boxes are normalized with a bottom-left origin.
let faces = (faceRequest.results ?? [])
    .map { f -> [Int] in
        let b = f.boundingBox
        return [Int(b.minX * Double(W)), Int((1 - b.maxY) * Double(H)), Int(b.width * Double(W)), Int(b.height * Double(H))]
    }
    .sorted { $0[2] * $0[3] > $1[2] * $1[3] }
let json = try JSONSerialization.data(withJSONObject: ["width": W, "height": H, "faces": faces])
print(String(data: json, encoding: .utf8)!)
