import CoreImage
import Foundation
import Vision

enum MaskError: Error {
    case usage
    case noResult
}

struct Response: Encodable {
    let mode: String
    let width: Int
    let height: Int
    let boxes: [[Double]]
}

func parseArguments() throws -> (input: URL, output: URL) {
    var inputPath: String?
    var outputPath: String?
    var index = 1
    while index < CommandLine.arguments.count {
        let argument = CommandLine.arguments[index]
        if argument == "--input", index + 1 < CommandLine.arguments.count {
            inputPath = CommandLine.arguments[index + 1]
            index += 2
            continue
        }
        if argument == "--output", index + 1 < CommandLine.arguments.count {
            outputPath = CommandLine.arguments[index + 1]
            index += 2
            continue
        }
        throw MaskError.usage
    }
    guard let inputPath, let outputPath else {
        throw MaskError.usage
    }
    return (URL(fileURLWithPath: inputPath), URL(fileURLWithPath: outputPath))
}

func writeMask(_ image: CIImage, to url: URL) throws {
    let context = CIContext(options: nil)
    try context.writePNGRepresentation(
        of: image,
        to: url,
        format: .Lf,
        colorSpace: CGColorSpaceCreateDeviceGray()
    )
}

func foregroundMask(input: URL, output: URL) throws -> Response? {
    let handler = VNImageRequestHandler(url: input)
    let request = VNGenerateForegroundInstanceMaskRequest()
    try handler.perform([request])
    guard let observation = request.results?.first, !observation.allInstances.isEmpty else {
        return nil
    }
    let pixelBuffer = try observation.generateScaledMaskForImage(forInstances: observation.allInstances, from: handler)
    let image = CIImage(cvPixelBuffer: pixelBuffer)
    try writeMask(image, to: output)
    return Response(mode: "vision_foreground", width: Int(image.extent.width), height: Int(image.extent.height), boxes: [])
}

func saliencyMask(input: URL, output: URL) throws -> Response? {
    let handler = VNImageRequestHandler(url: input)
    let request = VNGenerateAttentionBasedSaliencyImageRequest()
    try handler.perform([request])
    guard let observation = request.results?.first else {
        return nil
    }
    let image = CIImage(cvPixelBuffer: observation.pixelBuffer)
    try writeMask(image, to: output)
    let boxes = (observation.salientObjects ?? []).map { rectangle in
        [
            Double(rectangle.boundingBox.origin.x),
            Double(rectangle.boundingBox.origin.y),
            Double(rectangle.boundingBox.size.width),
            Double(rectangle.boundingBox.size.height),
        ]
    }
    return Response(mode: "vision_saliency", width: Int(image.extent.width), height: Int(image.extent.height), boxes: boxes)
}

do {
    let arguments = try parseArguments()
    if let response = try foregroundMask(input: arguments.input, output: arguments.output) ?? saliencyMask(input: arguments.input, output: arguments.output) {
        let payload = try JSONEncoder().encode(response)
        FileHandle.standardOutput.write(payload)
        FileHandle.standardOutput.write("\n".data(using: .utf8)!)
    } else {
        throw MaskError.noResult
    }
} catch MaskError.usage {
    FileHandle.standardError.write("Usage: workbench_mask_vision.swift --input <image> --output <mask.png>\n".data(using: .utf8)!)
    exit(64)
} catch {
    FileHandle.standardError.write("\(error)\n".data(using: .utf8)!)
    exit(1)
}
