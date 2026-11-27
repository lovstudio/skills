"""mono 风格的可编辑 PPTX 工具包：纸纹底 + 单色油墨 + 近黑，原生文本排版，图片转单色调。

依赖：python-pptx、Pillow、numpy。
自检：python3 mono_pptx_kit.py --demo /tmp/mono-demo.pptx

用法见 references/styles/mono.md。所有素材路径都由调用方传入，本文件不含任何个人路径。
"""
from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

INKS = {  # 同一份 deck 只用一种油墨
    "rust": "A75D38",
    "cobalt": "2148B8",
    "botanical": "008A4B",
    "signal-red": "C83232",
    "charcoal": "30343A",
    "aubergine": "63365F",
}


@dataclass
class Theme:
    paper: str = "E4E1DB"
    ink: str = INKS["rust"]
    dark: str = "2C2C2A"
    soft: str = "77716A"
    rule: str = "BDB6AC"
    grain: float = 6.0          # 图片颗粒强度，0 关闭
    paper_grain: float = 4.5    # 纸纹颗粒强度
    latin: str = "Arial"
    ea: str = "微软雅黑"
    mono: str = "Consolas"
    display: str = "Impact"     # 大数字、年份
    wide: str = "Arial Black"   # 英文单词标题


def _rgb(h: str) -> np.ndarray:
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


class MonoDeck:
    W, H, M = 13.333, 7.5, 0.9

    def __init__(self, theme: Theme | None = None, notes_md: str | Path | None = None,
                 logo: str | Path | None = None, cache_dir: str | Path = "ink"):
        self.t = theme or Theme()
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = Inches(self.W), Inches(self.H)
        self.layout = self.prs.slide_layouts[6]
        self.cache = Path(cache_dir)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.PAPER, self.INK, self.DARK, self.SOFT, self.RULE = (
            RGBColor.from_string(h) for h in (self.t.paper, self.t.ink, self.t.dark, self.t.soft, self.t.rule))
        self.notes = self._parse_notes(notes_md) if notes_md else {}
        self.count = 0
        self._install_master(logo)

    # ------------------------------------------------------------ 讲稿与母版
    @staticmethod
    def _parse_notes(md):
        notes, cur = {}, None
        for ln in Path(md).read_text(encoding="utf-8").splitlines():
            m = re.match(r"^## (P\d+)\b", ln)
            if m:
                cur = f"P{int(m.group(1)[1:]):02d}"
                notes[cur] = []
            elif cur and not ln.startswith("---"):
                notes[cur].append(ln)
        return {k: "\n".join(v).strip() for k, v in notes.items()}

    def paper_texture(self) -> Path:
        out = self.cache / f"paper-{self.t.paper}-{self.t.paper_grain}.jpg"
        if not out.exists():
            rng = np.random.default_rng(3)
            base = _rgb(self.t.paper)[None, None, :] + rng.normal(0, self.t.paper_grain, (900, 1600))[..., None]
            blot = np.asarray(Image.fromarray((rng.random((18, 32)) * 255).astype(np.uint8)).resize((1600, 900), Image.BICUBIC),
                              dtype=np.float32)
            base += ((blot - 128) / 128 * 3.0)[..., None]
            Image.fromarray(base.clip(0, 255).astype(np.uint8)).save(out, quality=90)
        return out

    def _install_master(self, logo):
        """纸纹与 Logo 放进版式（母版层）：先在临时页上画，再把图片元素挪进版式，最后删掉临时页。"""
        tmp = self.prs.slides.add_slide(self.layout)
        tmp.shapes.add_picture(str(self.paper_texture()), 0, 0, self.prs.slide_width, self.prs.slide_height)
        if logo:
            tmp.shapes.add_picture(str(self.ink_logo(logo)), Inches(self.W - 1.75), Inches(0.32), height=Inches(0.3))
        for shp in list(tmp.shapes):
            el = shp._element
            blip = el.find(".//" + qn("a:blip"))
            part = tmp.part.related_part(blip.get(qn("r:embed")))
            blip.set(qn("r:embed"), self.layout.part.relate_to(part, RT.IMAGE))
            self.layout.shapes._spTree.append(el)
        ids = self.prs.slides._sldIdLst
        last = ids[-1]
        self.prs.part.drop_rel(last.rId)
        ids.remove(last)

    def new(self):
        self.count += 1
        s = self.prs.slides.add_slide(self.layout)
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = self.PAPER
        s.notes_slide.notes_text_frame.text = self.notes.get(f"P{self.count:02d}", "")
        return s

    def save(self, path):
        self.prs.save(str(path))
        return Path(path)

    # ------------------------------------------------------------ 图片
    def duo(self, path) -> Path:
        """任意图片 → 纸色底上的单色油墨调；透明底先垫白。"""
        p = Path(path)
        key = hashlib.md5(f"{p.resolve()}|{self.t.ink}|{self.t.paper}|{self.t.grain}".encode()).hexdigest()[:10]
        out = self.cache / f"{p.stem}-{key}.jpg"
        if out.exists():
            return out
        im = Image.open(p)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
            bg.alpha_composite(im)
            im = bg
        im = im.convert("RGB")
        im.thumbnail((2000, 2000))
        a = np.asarray(im).astype(np.float32) / 255
        lum = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
        lo, hi = np.percentile(lum, 1), np.percentile(lum, 99)
        t = np.clip((lum - lo) / max(1e-3, hi - lo), 0, 1)
        res = _rgb(self.t.paper) * t[..., None] + _rgb(self.t.ink) * (1 - t[..., None])
        if self.t.grain:
            res += np.random.default_rng(7).normal(0, self.t.grain, res.shape[:2])[..., None]
        Image.fromarray(res.clip(0, 255).astype(np.uint8)).save(out, quality=90)
        return out

    def ink_logo(self, path, color: str | None = None) -> Path:
        """Logo → 单色油墨，透明底。"""
        color = color or self.t.ink
        p = Path(path)
        out = self.cache / f"{p.stem}-ink-{color}.png"
        if out.exists():
            return out
        a = np.asarray(Image.open(p).convert("RGBA")).astype(np.float32) / 255
        lum = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
        mask = a[..., 3] * np.clip((1 - lum) * 2.5, 0, 1)
        res = np.zeros(a.shape, dtype=np.uint8)
        res[..., :3] = _rgb(color)
        res[..., 3] = (mask * 255).astype(np.uint8)
        Image.fromarray(res).save(out)
        return out

    def pic(self, s, path, x, y, w, h, mode="cover", focus=0.35):
        """mode=cover 铺满并裁切（focus 决定裁切偏向），mode=fit 完整放入居中。"""
        iw, ih = Image.open(path).size
        if mode == "cover":
            sh = s.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))
            rb, ri = w / h, iw / ih
            if ri > rb:
                c = 1 - rb / ri
                sh.crop_left, sh.crop_right = c * focus, c * (1 - focus)
            else:
                c = 1 - ri / rb
                sh.crop_top, sh.crop_bottom = c * focus, c * (1 - focus)
            return sh
        sc = min(w / iw, h / ih)
        pw, ph = iw * sc, ih * sc
        return s.shapes.add_picture(str(path), Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2), Inches(pw), Inches(ph))

    def photo(self, s, path, x, y, w, h, cap=None, focus=0.35, mode="cover", cap_size=14):
        self.pic(s, self.duo(path), x, y, w, h, mode, focus)
        if cap:
            self.text(s, x, y + h + 0.06, w, 0.35, cap, cap_size, True, self.DARK)

    def icon(self, s, path, x, y, size=0.55):
        return self.pic(s, self.duo(path), x, y, size, size, "fit")

    def raw(self, s, path, x, y, w, h):
        """原色图片（例如二维码，转色可能扫不出）。"""
        return s.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))

    # ------------------------------------------------------------ 文本与线条
    def _font(self, run, size, bold, color, face):
        f = run.font
        f.size, f.color.rgb = Pt(size), color
        f.name = face or self.t.latin
        f.bold = False if face in (self.t.display, self.t.wide) else bold
        rpr = run._r.get_or_add_rPr()
        for tag in ("a:ea", "a:cs"):
            el = rpr.find(qn(tag))
            if el is None:
                el = rpr.makeelement(qn(tag), {})
                rpr.append(el)
            el.set("typeface", self.t.ea)

    def text(self, s, x, y, w, h, content, size=22, bold=False, color=None, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, spacing=1.15, gap=0, face=None):
        """content：字符串；或段落列表，段落可以是字符串、(文字, 选项) 或 runs 列表 [(文字, 选项), ...]。
        选项键：size、bold、color、face、align、gap。"""
        color = color or self.DARK
        tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        paras = content if isinstance(content, list) else [content]
        for i, para in enumerate(paras):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            runs = para if isinstance(para, list) else [para]
            popt = {}
            for item in runs:
                t, o = (item, {}) if isinstance(item, str) else item
                popt.update({k: v for k, v in o.items() if k in ("align", "gap")})
                r = p.add_run()
                r.text = t
                self._font(r, o.get("size", size), o.get("bold", bold), o.get("color", color), o.get("face", face))
            p.alignment = popt.get("align", align)
            p.line_spacing = spacing
            if i and popt.get("gap", gap):
                p.space_before = Pt(popt.get("gap", gap))
        return tb

    def rule(self, s, x, y, w, color=None, weight=1.0):
        c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y), Inches(x + w), Inches(y))
        c.line.color.rgb = color or self.RULE
        c.line.width = Pt(weight)
        return c

    def line(self, s, x1, y1, x2, y2, color=None, weight=2.0, arrow=False):
        c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        c.line.color.rgb = color or self.INK
        c.line.width = Pt(weight)
        if arrow:
            ln = c.line._get_or_add_ln()
            ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
        return c

    def block(self, s, x, y, w, h, fill=None, shape=MSO_SHAPE.RECTANGLE, outline=None, weight=2.0):
        shp = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
        if fill is None:
            shp.fill.background()
        else:
            shp.fill.solid()
            shp.fill.fore_color.rgb = fill
        if outline is None:
            shp.line.fill.background()
        else:
            shp.line.color.rgb = outline
            shp.line.width = Pt(weight)
        shp.shadow.inherit = False
        return shp

    # ------------------------------------------------------------ 版式积木
    def title(self, s, t, y=0.75, size=40, color=None, w=11.5):
        return self.text(s, self.M, y, w, 1.0, t, size, True, color or self.INK)

    def big(self, s, x, y, w, h, t, size, color=None, align=PP_ALIGN.LEFT):
        """大数字、年份。"""
        return self.text(s, x, y, w, h, t, size, color=color or self.INK, align=align, face=self.t.display, spacing=0.9)

    def word(self, s, x, y, w, h, t, size, color=None, align=PP_ALIGN.LEFT):
        """英文单词标题：比 Impact 宽，不显得挤。"""
        return self.text(s, x, y, w, h, t, size, color=color or self.INK, align=align, face=self.t.wide, spacing=0.95)

    def say(self, s, y, t, size=26, color=None):
        """结论句：页面底部的一行大字。"""
        return self.text(s, self.M, y, 11.6, 0.8, t, size, True, color or self.INK)

    def question(self, t, size=60):
        """问题页：大字居中，底部一个小色点。"""
        s = self.new()
        self.text(s, 1.2, 1.4, self.W - 2.4, 4.2, t, size, True, self.INK, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE, spacing=1.2)
        self.block(s, self.W / 2 - 0.16, 6.15, 0.32, 0.32, self.DARK, MSO_SHAPE.OVAL)
        return s

    def qa(self, portrait=None, qrs=(), logo=None, thanks="谢谢"):
        """Q&A 页：讲者照片在右，二维码保持原色。qrs = [(图片路径, 说明), ...]"""
        s = self.new()
        if portrait:
            self.pic(s, self.duo(portrait), 8.4, 0, self.W - 8.4, self.H, "cover", 0.15)
        self.word(s, self.M, 0.9, 7.2, 1.9, "Q & A", 110)
        self.text(s, self.M + 0.05, 2.85, 6, 0.6, thanks, 30, True, self.DARK)
        for i, (qr, cap) in enumerate(qrs):
            x = self.M + i * 2.45
            self.block(s, x - 0.08, 3.72, 2.06, 2.06, RGBColor(0xFF, 0xFF, 0xFF))
            self.raw(s, qr, x, 3.8, 1.9, 1.9)
            self.text(s, x - 0.08, 5.92, 2.06, 0.4, cap, 18, True, self.INK, PP_ALIGN.CENTER)
        if logo:
            s.shapes.add_picture(str(self.ink_logo(logo)), Inches(self.M), Inches(6.6), height=Inches(0.36))
        return s


# ---------------------------------------------------------------- 自检样张
def _demo(out: Path):
    work = out.parent / (out.stem + "-assets")
    work.mkdir(parents=True, exist_ok=True)
    # 合成一张有明暗层次的“照片”和一个带透明圆角的“图标”
    yy, xx = np.mgrid[0:600, 0:900]
    photo = np.stack([(xx / 900 * 255), (yy / 600 * 200), (128 + 100 * np.sin(xx / 60))], -1).clip(0, 255).astype(np.uint8)
    Image.fromarray(photo).save(work / "photo.png")
    ic = np.zeros((256, 256, 4), dtype=np.uint8)
    ic[32:224, 32:224] = (40, 120, 220, 255)
    Image.fromarray(ic).save(work / "icon.png")
    notes = work / "notes.md"
    notes.write_text("## P01 封面\n开场。\n\n## P02 问题\n提问。\n\n## P03 数字\n讲数字。\n\n"
                     "## P04 照片\n讲照片。\n\n## P05 问答\n问答。\n", encoding="utf-8")

    d = MonoDeck(Theme(), notes_md=notes, logo=work / "icon.png", cache_dir=work / "ink")
    s = d.new()
    d.pic(s, d.duo(work / "photo.png"), 7.0, 0, d.W - 7.0, d.H)
    d.text(s, d.M, 1.9, 5.9, 1.6, "示例标题", 80, True, d.INK)
    d.text(s, d.M, 3.7, 5.9, 1.2, ["副标题第一行", "副标题第二行"], 24, spacing=1.3)
    d.question("这是一个问题页？", 72)
    s = d.new()
    d.title(s, "大数字")
    d.big(s, d.M, 1.6, 5, 2.4, "2026", 160)
    d.word(s, 7.0, 2.0, 5.5, 1.0, "Agent", 60, d.DARK)
    d.say(s, 6.2, "一句结论放在底部")
    s = d.new()
    d.title(s, "照片与图标")
    d.photo(s, work / "photo.png", d.M, 1.7, 5.5, 3.5, "图注")
    d.icon(s, work / "icon.png", 7.0, 1.7, 1.0)
    d.qa()
    d.save(out)
    return d


def main():
    ap = argparse.ArgumentParser(description="mono 风格 PPTX 工具包")
    ap.add_argument("--demo", metavar="OUT.pptx", help="生成 5 页自检样张")
    a = ap.parse_args()
    if not a.demo:
        ap.print_help()
        return
    out = Path(a.demo)
    d = _demo(out)
    prs = Presentation(str(out))
    assert len(prs.slides) == 5, len(prs.slides)
    assert all(sl.notes_slide.notes_text_frame.text.strip() for sl in prs.slides), "每页都应有备注"
    pics = [sh for sh in prs.slides[0].slide_layout.shapes if sh.shape_type == 13]
    assert len(pics) >= 2, "母版里应有纸纹和 Logo"
    print(f"ok: {out} · {len(prs.slides)} slides · master pictures {len(pics)} · cache {d.cache}")


if __name__ == "__main__":
    main()
