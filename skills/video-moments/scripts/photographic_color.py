"""Source-aware still grading. NumPy is loaded only for the photographic command."""
import hashlib
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageCms


def camera_color(video):
    """Read only the matching Sony sidecar's color fields, never camera identity."""
    video = Path(video)
    names = {video.stem.lower() + suffix for suffix in (".xml", "m01.xml")}
    matches = [p for p in video.parent.iterdir()
               if p.is_file() and p.name.lower() in names and not p.name.startswith("._")]
    if not matches:
        return {}
    if len(matches) != 1:
        return {"error": "Ambiguous color sidecars; inspect before grading"}
    path = matches[0]
    try:
        if path.stat().st_size > 4 * 1024 * 1024:
            raise ValueError("Color sidecar exceeds 4 MiB")
        payload = path.read_bytes()
        if b"<!DOCTYPE" in payload.upper() or b"<!ENTITY" in payload.upper():
            raise ValueError("Color sidecar cannot contain DTD or entity declarations")
        root = ET.fromstring(payload)
        keys = {"CaptureGammaEquation", "CaptureColorPrimaries", "CodingEquations"}
        fields = {}
        for element in root.iter():
            key = element.get("name")
            if key in keys:
                value = element.get("value", "").lower()
                if key in fields and fields[key] != value:
                    raise ValueError("Conflicting color fields in sidecar")
                fields[key] = value
        return {"sidecar": str(path), "sha256": hashlib.sha256(payload).hexdigest(), **fields}
    except (ET.ParseError, ValueError, OSError) as exc:
        return {"sidecar": str(path), "error": str(exc)}


def resolve_mode(source, requested):
    camera = source.get("camera_color", {})
    transfer = source.get("color_transfer", "unknown")
    gamma = camera.get("CaptureGammaEquation", "")
    primaries = camera.get("CaptureColorPrimaries", "")
    if transfer in ("smpte2084", "arib-std-b67"):
        raise ValueError("HDR needs a reviewed color-managed transform before this SDR workflow")
    if camera.get("error"):
        raise ValueError(camera["error"])
    log = "log" in gamma or "log" in transfer
    if log:
        if gamma not in ("s-log3", "s-log3-cine") or primaries != "s-gamut3-cine":
            raise ValueError("Unsupported or incomplete Log metadata; do not apply ordinary SDR gains")
        inferred = "slog3-sgamut3cine"
    elif gamma == "rec709" and primaries == "rec709":
        inferred = "bt709"
    elif transfer == "bt709" and source.get("color_primaries") == "bt709":
        inferred = "bt709"
    elif transfer == "iec61966-2-1":
        inferred = "srgb"
    else:
        inferred = None
    if requested == "auto":
        if not inferred:
            raise ValueError("Unknown source color. Inspect metadata, then explicitly choose --color-mode; "
                             "srgb is only for already normalized SDR frames")
        return inferred
    if inferred and requested != inferred:
        raise ValueError(f"--color-mode {requested} conflicts with source metadata ({inferred})")
    return requested


def numpy():
    try:
        import numpy as np
        return np
    except ImportError as exc:
        raise ValueError("photographic requires NumPy; install numpy in the selected Python runtime") from exc


def decode_video(source, time, input_range=None):
    np = numpy()
    matrix = source.get("color_space", "unknown")
    if matrix == "unknown":
        matrix = {"rec709": "bt709"}.get(source.get("camera_color", {}).get("CodingEquations"))
    if matrix != "bt709":
        raise ValueError("Source YUV matrix must be confirmed as bt709 for this color transform")
    declared_range = source.get("color_range", "unknown")
    if input_range and declared_range not in ("unknown", input_range):
        raise ValueError("--input-range conflicts with the source range")
    color_range = input_range or declared_range
    if color_range not in ("pc", "tv"):
        raise ValueError("Unknown YUV range; inspect then pass --input-range pc or tv")
    command = ["ffmpeg", "-v", "error", "-noautorotate", "-ss", str(time), "-i", source["path"],
               "-map", "0:v:0", "-frames:v", "1", "-an", "-sn", "-vf",
               f"scale=in_color_matrix=bt709:in_range={color_range}:out_range=pc,format=rgb48le",
               "-pix_fmt", "rgb48le", "-f", "rawvideo", "pipe:1"]
    result = subprocess.run(command, capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.decode(errors="replace")[-2000:])
    shape = (source["height"], source["width"], 3)
    if len(result.stdout) != shape[0] * shape[1] * 6:
        raise ValueError("Decoded frame dimensions differ from source metadata")
    rgb = np.frombuffer(result.stdout, dtype="<u2").reshape(shape).astype(np.float64) / 65535
    return rgb, {"matrix": matrix, "range": color_range, "precision": "rgb48le", "command": command}


def slog3_to_linear(rgb):
    np = numpy()
    return np.where(rgb >= 171.2102946929 / 1023,
                    10 ** ((rgb * 1023 - 420) / 261.5) * .19 - .01,
                    (rgb * 1023 - 95) * .01125 / (171.2102946929 - 95))


def primary_matrix(primaries):
    np = numpy()
    p = np.array(primaries)
    m = np.array([p[:, 0] / p[:, 1], np.ones(3), (1 - p.sum(axis=1)) / p[:, 1]])
    white = np.array([.3127 / .329, 1, (1 - .3127 - .329) / .329])
    return m @ np.diag(np.linalg.solve(m, white))


def grade(rgb, mode, parameters):
    np = numpy()
    if mode == "slog3-sgamut3cine":
        transform = np.linalg.solve(primary_matrix([[.64, .33], [.3, .6], [.15, .06]]),
                                    primary_matrix([[.766, .275], [.225, .8], [.089, -.087]]))
        linear = slog3_to_linear(rgb) @ transform.T
    elif mode == "bt709":
        linear = np.where(rgb < .081, rgb / 4.5, ((rgb + .099) / 1.099) ** (1 / .45))
    else:
        linear = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
    linear = np.maximum(linear, 0) * 2 ** parameters["exposure"]
    linear *= np.array([parameters["red"], parameters["green"], parameters["blue"]])
    weights = np.array([.2126, .7152, .0722])
    if mode != "srgb" or parameters["exposure"] != 0:
        luminance = linear @ weights
        knee = .75
        mapped = np.where(luminance <= knee, luminance,
                          knee + (1 - knee) * (1 - np.exp(-np.maximum(luminance-knee, 0) / (1-knee))))
        linear *= (mapped / np.maximum(luminance, 1e-10))[..., None]
    rgb = np.where(linear <= .0031308, linear * 12.92, 1.055 * linear ** (1 / 2.4) - .055)
    luminance = rgb @ weights
    rgb = luminance[..., None] + (rgb - luminance[..., None]) * parameters["saturation"]
    rgb = (rgb - .5) * parameters["contrast"] + .5 + parameters["brightness"]
    rgb = np.clip(rgb, 0, 1) ** (1 / parameters["gamma"])
    return Image.fromarray(np.uint8(np.round(rgb * 255)))


def srgb_profile():
    return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


def normalized_frame(path):
    np = numpy()
    with Image.open(path) as im:
        if im.info.get("icc_profile"):
            import io
            source = ImageCms.ImageCmsProfile(io.BytesIO(im.info["icc_profile"]))
            im = ImageCms.profileToProfile(im, source, ImageCms.createProfile("sRGB"), outputMode="RGB")
        return np.asarray(im.convert("RGB"), dtype=np.float64) / 255
