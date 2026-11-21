"""Render the Fourier epicycle portrait as a vertical video (skia raster -> ffmpeg pipe)."""
from __future__ import annotations

import math
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib
import numpy as np
import skia
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

import fourier

matplotlib.rcParams["mathtext.fontset"] = "cm"

BG = (18, 15, 14)
TEAL = (124, 197, 178)
GOLD = (232, 195, 90)
CORAL = (247, 116, 84)
CREAM = (240, 230, 214)
GRAY = (165, 160, 155)


def hexrgb(c):
    return "#%02x%02x%02x" % c


def c4(rgb, a=1.0):
    return skia.Color4f(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, max(0.0, min(1.0, a)))


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ramp(t, a, b):
    return smooth((t - a) / (b - a)) if b > a else float(t >= a)


def math_image(parts, px, gap=0.0):
    """Mathtext (Computer Modern) rendered to a cropped skia image; parts = [(tex, rgb), ...]."""
    dpi = 100
    fig = Figure(figsize=(24, 4), dpi=dpi)
    fig.patch.set_alpha(0)
    canvas = FigureCanvasAgg(fig)
    renderer = canvas.get_renderer()
    x = 20.0
    for tex, rgb in parts:
        t = fig.text(x / (24 * dpi), 0.45, tex, color=hexrgb(rgb), fontsize=px * 72 / dpi, va="baseline")
        x = t.get_window_extent(renderer=renderer).x1 + gap * px
    canvas.draw()
    rgba = np.asarray(canvas.buffer_rgba()).copy()
    ys, xs = np.nonzero(rgba[..., 3])
    rgba = np.ascontiguousarray(rgba[max(0, ys.min() - 4): ys.max() + 5, max(0, xs.min() - 4): xs.max() + 5])
    return skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType)


@dataclass
class Style:
    width: int = 1080
    height: int = 1920
    fps: int = 30
    safe_top: int = 160
    safe_bottom: int = 260
    safe_side: int = 46
    title: str = ""
    logo: Path | None = None
    font_family: str = "Songti SC"
    stages: list = field(default_factory=lambda: [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024])
    stage_seconds: list = field(default_factory=lambda: [1.4, 1.4, 1.6, 1.8, 2.0, 2.4, 2.8, 3.2, 3.8, 4.4, 5.4])
    intro_seconds: float = 3.2
    outro_seconds: float = 5.5


class Scene:
    def __init__(self, z, sp, ink, cutout, style: Style):
        self.z, self.sp, self.st = z, sp, style
        self.m = len(z)
        self.tgrid = 2 * np.pi * np.arange(self.m) / self.m
        self.errors = [fourier.relative_error(z, fourier.reconstruct(sp, n, self.tgrid)) for n in style.stages]
        self.decay = fourier.decay_exponent(sp)
        self._recon_cache = {}
        self.logo_h = 80
        self.logo_top = style.height - style.safe_bottom - 16 - self.logo_h
        self.label_top = self.logo_top - 215  # "N = ..." and "error = ..." sit above the logo
        self._layout(style.stages[-1])
        self._assets(ink, cutout)
        starts = np.cumsum([style.intro_seconds] + list(style.stage_seconds))
        self.stage_start = starts[:-1]
        self.draw_end = starts[-1]
        self.duration = self.draw_end + style.outro_seconds

    # ---------- geometry ----------
    def _chains(self):
        """Per chain: (terms, rotation multiplier). xy: x chain as is, y chain rotated 90 degrees."""
        if self.sp.mode == "xy":
            return [(self.sp.terms[0], 1.0, TEAL), (self.sp.terms[1], 1j, GOLD)]
        return [(self.sp.terms[0], 1.0, TEAL)]

    @staticmethod
    def joints(terms, rot, n, t):
        # Real series use the real part of each rotating vector; rot=1j turns the y chain so its
        # vertical component carries y(t). Complex mode uses the vectors as they are.
        v = terms.amp[:n] * np.exp(1j * (terms.freq[:n] * t + terms.phase[:n]))
        return np.concatenate([[0], np.cumsum(v * rot)])

    def _layout(self, n):
        st = self.st
        d = self.z - self.sp.center
        dbox = (d.real.min(), d.real.max(), d.imag.min(), d.imag.max())
        ts = np.linspace(0, 2 * np.pi, 720, endpoint=False)
        boxes = []
        for terms, rot, _ in self._chains():
            pts = np.concatenate([self.joints(terms, rot, n, t) for t in ts])
            r1 = terms.amp[0]
            boxes.append((min(pts.real.min(), -r1), max(pts.real.max(), r1),
                          min(pts.imag.min(), -r1), max(pts.imag.max(), r1)))
        top, bottom = st.safe_top + 150, self.label_top - 30
        left, right = st.safe_side, st.width - st.safe_side
        gap = 28
        if self.sp.mode == "xy":
            bx, by = boxes
            # x chain sits above the drawing, y chain to its left; tips project onto the pen.
            span_w = max(dbox[1], bx[1]) - (dbox[0] - by[1] + by[0])
            span_h = max(dbox[3], by[3]) - (dbox[2] - bx[3] + bx[2])
            s = min((right - left - gap) / span_w, (bottom - top - gap) / span_h)
            ox = left + (right - left - gap - s * span_w) / 2 + gap + s * (by[1] - by[0]) - s * dbox[0]
            oy = top + (bottom - top - gap - s * span_h) / 2 + gap + s * (bx[3] - bx[2]) - s * dbox[2]
            self.centers = [complex(ox, oy + s * dbox[2] - gap - s * bx[3]),
                            complex(ox + s * dbox[0] - gap - s * by[1], oy)]
        else:
            (b,) = boxes
            box = (min(dbox[0], b[0]), max(dbox[1], b[1]), min(dbox[2], b[2]), max(dbox[3], b[3]))
            s = min((right - left) / (box[1] - box[0]), (bottom - top) / (box[3] - box[2]))
            ox = (left + right) / 2 - s * (box[0] + box[1]) / 2
            oy = (top + bottom) / 2 - s * (box[2] + box[3]) / 2
            self.centers = [complex(ox, oy)]
        self.scale, self.origin = s, complex(ox, oy)
        # Hero pose (intro photo and final reveal): portrait centred in the upper part of the frame.
        w, h = dbox[1] - dbox[0], dbox[3] - dbox[2]
        s2 = min((st.width - 2 * 90) / w, 640 / h)
        self.scale2 = s2
        self.origin2 = complex(st.width / 2 - s2 * (dbox[0] + dbox[1]) / 2, top + 20 - s2 * dbox[2])
        self.reveal_bottom = top + 20 + s2 * h

    def recon(self, n):
        if n not in self._recon_cache:
            zn = fourier.reconstruct(self.sp, n, self.tgrid) - self.sp.center
            self._recon_cache[n] = [skia.Point(float(p.real), float(p.imag)) for p in zn]
        return self._recon_cache[n]

    # ---------- static assets ----------
    def _assets(self, ink, cutout):
        st = self.st
        h, w = ink.shape
        rgba = np.zeros((h, w, 4), np.uint8)
        rgba[..., :3] = CREAM
        rgba[..., 3] = ink
        self.ink_img = skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType)
        rgba = np.ascontiguousarray(cutout[..., [2, 1, 0, 3]])
        self.photo_img = skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType)
        # Line art pixel (u, v) sits at data point (u + .5, v + .5) relative to the path's frame.
        self.ink_offset = complex(-0.5, -0.5) - self.sp.center
        self.title_font = skia.Font(skia.Typeface(st.font_family, skia.FontStyle.Bold()), 54)
        self.logo = skia.Image.open(str(st.logo)) if st.logo else None
        self.n_imgs = [math_image([(r"$N\,=$", CREAM), (rf"${n}$", CORAL)], 76, gap=0.28) for n in st.stages]
        self.err_imgs = [math_image([(rf"$\mathrm{{error}}\,=\,{e * 100:.2f}\%$", CREAM)], 54) for e in self.errors]
        if self.sp.mode == "xy":
            self.formulas = [
                math_image([(r"$x(t)$", TEAL), (r"$=\,{\sum}_k\,a_k\,\cos kt+b_k\,\sin kt$", CREAM)], 60, gap=0.25),
                math_image([(r"$y(t)$", GOLD), (r"$=\,{\sum}_k\,c_k\,\cos kt+d_k\,\sin kt$", CREAM)], 60, gap=0.25),
                math_image([(rf"$r_k\sim k^{{-{self.decay:.2f}}}$", CREAM)], 56),
            ]
        else:
            self.formulas = [
                math_image([(r"$z(t)$", TEAL), (r"$=\,{\sum}_k\,c_k\,e^{ikt}$", CREAM)], 64, gap=0.25),
                math_image([(rf"$|c_k|\sim k^{{-{self.decay:.2f}}}$", CREAM)], 56),
            ]

    # ---------- frame ----------
    def draw(self, canvas, sec):
        st = self.st
        canvas.clear(c4(BG))
        stage = int(np.searchsorted(self.stage_start, sec, side="right")) - 1
        drawing = 0 <= stage and sec < self.draw_end
        out_t = sec - self.draw_end  # seconds into the outro (negative before it)

        # 1 = hero pose, 0 = drawing pose: the photo shrinks into place, the result grows back out.
        move = max(1 - ramp(sec, 1.3, 2.5), ramp(out_t, 0.6, 1.8))
        s = self.scale + (self.scale2 - self.scale) * move
        o = self.origin + (self.origin2 - self.origin) * move

        def to_screen(m):
            canvas.save()
            canvas.translate(o.real, o.imag)
            canvas.scale(s, s)
            m()
            canvas.restore()

        # Intro: cut-out photo dissolves into line art, which then dims into the tracing guide.
        photo_a = ramp(sec, 0.0, 0.5) * (1 - ramp(sec, 1.4, 2.3))
        if photo_a > 0:
            to_screen(lambda: canvas.drawImage(self.photo_img, self.ink_offset.real, self.ink_offset.imag,
                                               skia.SamplingOptions(skia.FilterMode.kLinear),
                                               skia.Paint(Alpha=int(255 * photo_a))))
        guide_a = ramp(sec, 1.4, 2.3) * (1 - 0.88 * ramp(sec, 2.4, st.intro_seconds))
        if out_t > 0:
            guide_a = max(0.12 * (1 - ramp(out_t, 0.0, 0.6)), ramp(out_t, 0.9, 2.0))
        if guide_a > 0:
            to_screen(lambda: canvas.drawImage(self.ink_img, self.ink_offset.real, self.ink_offset.imag,
                                               skia.SamplingOptions(skia.FilterMode.kLinear),
                                               skia.Paint(Alpha=int(255 * guide_a))))

        trail_w = 2.4
        if drawing or out_t >= 0:
            k = stage if drawing else len(st.stages) - 1
            prog = (sec - self.stage_start[k]) / st.stage_seconds[k] if drawing else 1.0
            idx = max(2, int(prog * self.m) + 1)
            pts = self.recon(st.stages[k])
            if drawing and k > 0:  # previous pass fades away as the next one starts
                fade = 1 - ramp(sec - self.stage_start[k], 0.0, 0.6)
                if fade > 0:
                    self._trail(canvas, to_screen, self.recon(st.stages[k - 1]), len(pts), s, trail_w,
                                CORAL, 0.45 * fade, glow=False)
            trail_a = 1 - ramp(out_t, 0.9, 2.0) if out_t > 0 else 1.0
            if trail_a > 0:
                self._trail(canvas, to_screen, pts, min(idx, len(pts)), s, trail_w, CORAL, trail_a, glow=True)

        last = len(st.stages) - 1
        k = stage if drawing else (last if out_t >= 0 else 0)
        chain_a = ramp(sec, 2.4, st.intro_seconds) * (1 - ramp(out_t, 0.0, 0.6))
        if chain_a > 0:
            prog = (sec - self.stage_start[k]) / st.stage_seconds[k] if drawing else (1.0 if out_t >= 0 else 0.0)
            self._chains_frame(canvas, st.stages[k], 2 * np.pi * prog, s, o, chain_a)

        if chain_a > 0:  # labels share the chains' fade
            self._blit_center(canvas, self.n_imgs[k], st.width / 2, self.label_top, chain_a)
            self._blit_center(canvas, self.err_imgs[k], st.width / 2, self.label_top + 100, chain_a)
        if out_t > 0:
            y = self.reveal_bottom + 70
            for i, img in enumerate(self.formulas):
                a = ramp(out_t, 1.6 + 0.35 * i, 2.4 + 0.35 * i)
                self._blit_center(canvas, img, st.width / 2, y, a)
                y += img.height() + 34

        if st.title:
            paint = skia.Paint(AntiAlias=True, Color4f=c4(CREAM, ramp(sec, 0.0, 0.6)))
            w = self.title_font.measureText(st.title)
            canvas.drawString(st.title, (st.width - w) / 2, st.safe_top + 78, self.title_font, paint)
        if self.logo:
            lw = self.logo_h * self.logo.width() / self.logo.height()
            rect = skia.Rect.MakeXYWH((st.width - lw) / 2, self.logo_top, lw, self.logo_h)
            canvas.drawImageRect(self.logo, rect, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear),
                                 skia.Paint(Alpha=int(255 * 0.9 * ramp(sec, 0.0, 0.6))))

    def _trail(self, canvas, to_screen, pts, n, s, width, rgb, alpha, glow):
        path = skia.Path()
        path.addPoly(pts[:n], False)

        def paint_it():
            if glow:
                canvas.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style,
                                                 StrokeWidth=7 / s, Color4f=c4(rgb, 0.22 * alpha),
                                                 MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3 / s)))
            canvas.drawPath(path, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=width / s,
                                             StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap,
                                             Color4f=c4(rgb, alpha)))
        to_screen(paint_it)

    def _chains_frame(self, canvas, n, t, s, o, alpha):
        pen = o + s * (fourier.reconstruct(self.sp, n, np.array([t]))[0] - self.sp.center)
        for (terms, rot, rgb), center in zip(self._chains(), self.centers):
            j = center + s * self.joints(terms, rot, n, t)
            radii = s * terms.amp[:n]
            circles = skia.Path()
            big = skia.Path()
            for i in range(n):
                r = radii[i]
                if r < 0.8:
                    break
                (big if i < 2 else circles).addCircle(float(j[i].real), float(j[i].imag), float(r))
            stroke = dict(AntiAlias=True, Style=skia.Paint.kStroke_Style)
            canvas.drawPath(big, skia.Paint(StrokeWidth=2.0, Color4f=c4(rgb, 0.75 * alpha), **stroke))
            canvas.drawPath(circles, skia.Paint(StrokeWidth=1.3, Color4f=c4(rgb, 0.42 * alpha), **stroke))
            arms = skia.Path()
            arms.addPoly([skia.Point(float(p.real), float(p.imag)) for p in j], False)
            canvas.drawPath(arms, skia.Paint(StrokeWidth=1.4, Color4f=c4(rgb, 0.85 * alpha),
                                             StrokeJoin=skia.Paint.kRound_Join, **stroke))
            tip = j[-1]
            if self.sp.mode == "xy":
                line = skia.Path()
                line.moveTo(float(tip.real), float(tip.imag))
                line.lineTo(float(pen.real), float(pen.imag))
                canvas.drawPath(line, skia.Paint(StrokeWidth=1.6, Color4f=c4(GRAY, 0.6 * alpha),
                                                 PathEffect=skia.DashPathEffect.Make([10.0, 8.0], 0.0), **stroke))
            canvas.drawCircle(float(tip.real), float(tip.imag), 5.5,
                              skia.Paint(AntiAlias=True, Color4f=c4(rgb, alpha)))
        glow = skia.Paint(AntiAlias=True, Color4f=c4(CORAL, 0.5 * alpha),
                          MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6))
        canvas.drawCircle(float(pen.real), float(pen.imag), 9, glow)
        canvas.drawCircle(float(pen.real), float(pen.imag), 5, skia.Paint(AntiAlias=True, Color4f=c4((255, 240, 230), alpha)))

    @staticmethod
    def _blit_center(canvas, img, cx, y, alpha):
        if alpha <= 0:
            return
        canvas.drawImage(img, cx - img.width() / 2, y, skia.SamplingOptions(skia.FilterMode.kLinear),
                         skia.Paint(Alpha=int(255 * min(1, alpha))))


def render(scene: Scene, out: Path, *, stills_dir: Path | None = None, still_times=(), crf=16):
    st = scene.st
    info = skia.ImageInfo.Make(st.width, st.height, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType)
    surface = skia.Surface.MakeRaster(info)
    canvas = surface.getCanvas()
    if stills_dir:
        stills_dir.mkdir(parents=True, exist_ok=True)
        for sec in still_times:
            scene.draw(canvas, sec)
            surface.makeImageSnapshot().save(str(stills_dir / f"still_{sec:05.2f}.png"), skia.kPNG)
    if out is None:
        return
    frames = int(math.ceil(scene.duration * st.fps))
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{st.width}x{st.height}",
           "-r", str(st.fps), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(frames):
        scene.draw(canvas, f / st.fps)
        proc.stdin.write(surface.toarray().tobytes())
        if f % (st.fps * 5) == 0:
            print(f"[render] {f}/{frames} frames", flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        raise SystemExit("ffmpeg failed")
    print(f"[render] wrote {out} ({frames} frames, {scene.duration:.1f}s)")
