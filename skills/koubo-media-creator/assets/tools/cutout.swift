// Person cut-out for the cover: macOS Vision person segmentation → PNG with alpha, cropped to the person.
// build: swiftc -O cutout.swift -o cutout      run: cutout input.jpg output.png [--pad 0.04] [--no-crop]
import AppKit
import CoreImage
import Foundation
import Vision

let args = CommandLine.arguments
guard args.count >= 3 else {
    FileHandle.standardError.write("usage: cutout input output.png [--pad 0.04] [--no-crop]\n".data(using: .utf8)!)
    exit(2)
}
let pad = args.firstIndex(of: "--pad").flatMap { Double(args[$0 + 1]) } ?? 0.04
let crop = !args.contains("--no-crop")
guard let src = CIImage(contentsOf: URL(fileURLWithPath: args[1])) else { print("cannot read \(args[1])"); exit(1) }
let image = src.oriented(forExifOrientation: Int32((src.properties["Orientation"] as? Int) ?? 1))

let request = VNGeneratePersonSegmentationRequest()
request.qualityLevel = .accurate
request.outputPixelFormat = kCVPixelFormatType_OneComponent8
let handler = VNImageRequestHandler(ciImage: image, options: [:])
try handler.perform([request])
guard let maskBuffer = request.results?.first?.pixelBuffer else { print("no person found"); exit(1) }

var mask = CIImage(cvPixelBuffer: maskBuffer)
mask = mask.transformed(by: CGAffineTransform(scaleX: image.extent.width / mask.extent.width,
                                              y: image.extent.height / mask.extent.height))
// soften the matte edge slightly so hair does not look cut with scissors
mask = mask.applyingGaussianBlur(sigma: 1.2).cropped(to: image.extent)
let clear = CIImage(color: .clear).cropped(to: image.extent)
var out = image.applyingFilter("CIBlendWithMask", parameters: [kCIInputBackgroundImageKey: clear, kCIInputMaskImageKey: mask])

let ctx = CIContext()
if crop {
    // bounding box of mask pixels above 50%
    let w = CVPixelBufferGetWidth(maskBuffer), h = CVPixelBufferGetHeight(maskBuffer)
    CVPixelBufferLockBaseAddress(maskBuffer, .readOnly)
    let base = CVPixelBufferGetBaseAddress(maskBuffer)!.assumingMemoryBound(to: UInt8.self)
    let stride = CVPixelBufferGetBytesPerRow(maskBuffer)
    var minX = w, minY = h, maxX = 0, maxY = 0
    for y in 0..<h { for x in 0..<w where base[y * stride + x] > 127 {
        minX = min(minX, x); maxX = max(maxX, x); minY = min(minY, y); maxY = max(maxY, y)
    } }
    CVPixelBufferUnlockBaseAddress(maskBuffer, .readOnly)
    if maxX > minX && maxY > minY {
        let sx = image.extent.width / CGFloat(w), sy = image.extent.height / CGFloat(h)
        let p = CGFloat(pad) * image.extent.width
        // pixel rows run top-down, CoreImage y runs bottom-up
        var r = CGRect(x: CGFloat(minX) * sx - p, y: image.extent.height - CGFloat(maxY + 1) * sy - p,
                       width: CGFloat(maxX - minX + 1) * sx + 2 * p, height: CGFloat(maxY - minY + 1) * sy + 2 * p)
        r = r.intersection(image.extent)
        out = out.cropped(to: r).transformed(by: CGAffineTransform(translationX: -r.minX, y: -r.minY))
    }
}
guard let cg = ctx.createCGImage(out, from: out.extent, format: .RGBA8, colorSpace: CGColorSpace(name: CGColorSpace.sRGB)) else {
    print("render failed"); exit(1)
}
let rep = NSBitmapImageRep(cgImage: cg)
try rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: args[2]))
print("{\"cutout\": \"\(args[2])\", \"width\": \(cg.width), \"height\": \(cg.height)}")
