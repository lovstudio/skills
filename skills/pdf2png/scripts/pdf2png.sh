#!/bin/bash
# Convert PDF to vertically concatenated PNG (using macOS native CoreGraphics)
# Usage: pdf2png.sh file1.pdf [file2.pdf ...]

for f in "$@"; do
  [[ "$f" == *.pdf ]] || continue
  output="${f%.pdf}.png"
  /usr/bin/python3 - "$f" "$output" <<'PYEOF'
import sys
from Quartz import (CGPDFDocumentCreateWithURL,
    CGPDFDocumentGetNumberOfPages, CGPDFDocumentGetPage,
    CGPDFPageGetBoxRect, kCGPDFMediaBox,
    CGColorSpaceCreateDeviceRGB, CGBitmapContextCreate,
    kCGImageAlphaPremultipliedLast, CGContextDrawPDFPage,
    CGContextScaleCTM, CGBitmapContextCreateImage,
    CGContextDrawImage, CGRectMake)
from CoreFoundation import CFURLCreateWithFileSystemPath, kCFURLPOSIXPathStyle
from AppKit import NSBitmapImageRep, NSPNGFileType

url = CFURLCreateWithFileSystemPath(None, sys.argv[1], kCFURLPOSIXPathStyle, False)
doc = CGPDFDocumentCreateWithURL(url)
n = CGPDFDocumentGetNumberOfPages(doc)
scale = 2.0
images, total_h, max_w = [], 0, 0
for i in range(1, n + 1):
    page = CGPDFDocumentGetPage(doc, i)
    r = CGPDFPageGetBoxRect(page, kCGPDFMediaBox)
    w, h = int(r.size.width * scale), int(r.size.height * scale)
    cs = CGColorSpaceCreateDeviceRGB()
    ctx = CGBitmapContextCreate(None, w, h, 8, 4 * w, cs, kCGImageAlphaPremultipliedLast)
    CGContextScaleCTM(ctx, scale, scale)
    CGContextDrawPDFPage(ctx, page)
    images.append((CGBitmapContextCreateImage(ctx), w, h))
    total_h += h
    max_w = max(max_w, w)

cs = CGColorSpaceCreateDeviceRGB()
ctx = CGBitmapContextCreate(None, max_w, total_h, 8, 4 * max_w, cs, kCGImageAlphaPremultipliedLast)
y = total_h
for img, w, h in images:
    y -= h
    CGContextDrawImage(ctx, CGRectMake(0, y, w, h), img)
rep = NSBitmapImageRep.alloc().initWithCGImage_(CGBitmapContextCreateImage(ctx))
data = rep.representationUsingType_properties_(NSPNGFileType, None)
data.writeToFile_atomically_(sys.argv[2], True)
PYEOF
  echo "Created: $output"
done
