// Optional macOS video backend. Called by media_preprocessor.py.
import Foundation
import AVFoundation
import CoreImage
import Metal

func fail(_ text: String) -> Never { fputs(text+"\n",stderr); exit(2) }
let args=CommandLine.arguments
if args.count != 8 { fail("input output start duration cube-rgba cube-dimension bitrate-mbps") }
let source=URL(fileURLWithPath:args[1]), destination=URL(fileURLWithPath:args[2])
if FileManager.default.fileExists(atPath:destination.path) { fail("output exists") }
guard let startSeconds=Double(args[3]),let durationSeconds=Double(args[4]),let bitrate=Double(args[7]),startSeconds.isFinite,durationSeconds.isFinite,bitrate.isFinite,startSeconds>=0,durationSeconds>0,(1...200).contains(bitrate) else {fail("invalid parameters")}
let start=CMTime(seconds:startSeconds,preferredTimescale:600000)
let duration=CMTime(seconds:durationSeconds,preferredTimescale:600000)
let asset=AVURLAsset(url:source)
guard let videoTrack=asset.tracks(withMediaType:.video).first else { fail("no video") }
let size=videoTrack.naturalSize
if size.width<=0 || size.height<=0 {fail("invalid dimensions")}
let reader=try AVAssetReader(asset:asset)
reader.timeRange=CMTimeRange(start:start,duration:duration)
let video=AVAssetReaderTrackOutput(track:videoTrack,outputSettings:[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange])
video.alwaysCopiesSampleData=false;reader.add(video)
let writer=try AVAssetWriter(outputURL:destination,fileType:.mp4)
let videoIn=AVAssetWriterInput(mediaType:.video,outputSettings:[AVVideoCodecKey:AVVideoCodecType.h264,AVVideoWidthKey:Int(size.width),AVVideoHeightKey:Int(size.height),AVVideoCompressionPropertiesKey:[AVVideoAverageBitRateKey:Int(bitrate*1_000_000),AVVideoProfileLevelKey:AVVideoProfileLevelH264HighAutoLevel,AVVideoMaxKeyFrameIntervalKey:50],AVVideoColorPropertiesKey:[AVVideoColorPrimariesKey:AVVideoColorPrimaries_ITU_R_709_2,AVVideoTransferFunctionKey:AVVideoTransferFunction_ITU_R_709_2,AVVideoYCbCrMatrixKey:AVVideoYCbCrMatrix_ITU_R_709_2]])
videoIn.transform=videoTrack.preferredTransform
let adaptor=AVAssetWriterInputPixelBufferAdaptor(assetWriterInput:videoIn,sourcePixelBufferAttributes:[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32BGRA,kCVPixelBufferWidthKey as String:Int(size.width),kCVPixelBufferHeightKey as String:Int(size.height),kCVPixelBufferMetalCompatibilityKey as String:true])
writer.add(videoIn)
var audio:AVAssetReaderTrackOutput?;var audioIn:AVAssetWriterInput?
if let at=asset.tracks(withMediaType:.audio).first {
 audio=AVAssetReaderTrackOutput(track:at,outputSettings:[AVFormatIDKey:kAudioFormatLinearPCM]);reader.add(audio!)
 let formats=at.formatDescriptions as! [CMAudioFormatDescription]
 let channels=formats.first.flatMap{CMAudioFormatDescriptionGetStreamBasicDescription($0)?.pointee.mChannelsPerFrame} ?? 2
 audioIn=AVAssetWriterInput(mediaType:.audio,outputSettings:[AVFormatIDKey:kAudioFormatMPEG4AAC,AVSampleRateKey:48000,AVNumberOfChannelsKey:Int(channels),AVEncoderBitRateKey:256000]);writer.add(audioIn!)
}
let cube=try Data(contentsOf:URL(fileURLWithPath:args[5]));guard let dim=Int(args[6]), (2...65).contains(dim) else {fail("invalid cube dimension")}
guard cube.count==dim*dim*dim*4*4 else {fail("cube size mismatch")}
guard let device=MTLCreateSystemDefaultDevice() else {fail("Metal unavailable")}
let context=CIContext(mtlDevice:device,options:[.workingColorSpace:NSNull(),.outputColorSpace:NSNull(),.cacheIntermediates:false])
let filter=CIFilter(name:"CIColorCube",parameters:["inputCubeDimension":dim,"inputCubeData":cube])!
guard writer.startWriting(),reader.startReading() else {fail("cannot start: \(String(describing:writer.error)) \(String(describing:reader.error))")}
writer.startSession(atSourceTime:.zero)
let group=DispatchGroup();group.enter()
let wall=Date();var count=0
videoIn.requestMediaDataWhenReady(on:DispatchQueue(label:"grade.video")) {
 while videoIn.isReadyForMoreMediaData {
  guard let sample=video.copyNextSampleBuffer() else {videoIn.markAsFinished();group.leave();return}
  autoreleasepool {
   let pts=CMTimeSubtract(CMSampleBufferGetPresentationTimeStamp(sample),start)
   if CMTimeCompare(pts,.zero)<0 || CMTimeCompare(pts,duration)>=0 {return}
   guard let original=CMSampleBufferGetImageBuffer(sample) else {fail("missing frame")}
   filter.setValue(CIImage(cvPixelBuffer:original,options:[.colorSpace:NSNull()]),forKey:kCIInputImageKey)
   var target:CVPixelBuffer?
   guard let pool=adaptor.pixelBufferPool,CVPixelBufferPoolCreatePixelBuffer(nil,pool,&target)==kCVReturnSuccess,let target=target else {fail("pixel pool error")}
   context.render(filter.outputImage!,to:target,bounds:CGRect(origin:.zero,size:size),colorSpace:nil)
   if !adaptor.append(target,withPresentationTime:pts) {fail("append video: \(String(describing:writer.error))")}
   count+=1
   if count%250==0 {print("frames=\(count) source_seconds=\(CMTimeGetSeconds(pts)+CMTimeGetSeconds(start)) speed=\(CMTimeGetSeconds(pts)/Date().timeIntervalSince(wall))");fflush(stdout)}
  }
 }
}
if let a=audio,let ai=audioIn {
 group.enter()
 ai.requestMediaDataWhenReady(on:DispatchQueue(label:"grade.audio")) {
  while ai.isReadyForMoreMediaData {
   guard let sample=a.copyNextSampleBuffer() else {ai.markAsFinished();group.leave();return}
   var count:CMItemCount=0
   CMSampleBufferGetSampleTimingInfoArray(sample,entryCount:0,arrayToFill:nil,entriesNeededOut:&count)
   var times=[CMSampleTimingInfo](repeating:CMSampleTimingInfo(duration:.invalid,presentationTimeStamp:.invalid,decodeTimeStamp:.invalid),count:count)
   CMSampleBufferGetSampleTimingInfoArray(sample,entryCount:count,arrayToFill:&times,entriesNeededOut:&count)
   for i in times.indices {times[i].presentationTimeStamp=CMTimeSubtract(times[i].presentationTimeStamp,start);if times[i].decodeTimeStamp.isValid {times[i].decodeTimeStamp=CMTimeSubtract(times[i].decodeTimeStamp,start)}}
   var shifted:CMSampleBuffer?
   CMSampleBufferCreateCopyWithNewTiming(allocator:kCFAllocatorDefault,sampleBuffer:sample,sampleTimingEntryCount:count,sampleTimingArray:&times,sampleBufferOut:&shifted)
   guard let shifted=shifted,ai.append(shifted) else {fail("append audio: \(String(describing:writer.error))")}
  }
 }
}
group.wait()
if reader.status == .failed {fail("reader failed: \(String(describing:reader.error))")}
writer.endSession(atSourceTime:duration)
let finish=DispatchSemaphore(value:0);writer.finishWriting {finish.signal()};finish.wait()
guard writer.status == .completed else {fail("writer failed: \(String(describing:writer.error))")}
print("completed frames=\(count) seconds=\(Date().timeIntervalSince(wall))")
