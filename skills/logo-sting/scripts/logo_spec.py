#!/usr/bin/env python3
"""Official logo SVG -> logo spec JSON (logo-sting-spec/v1) for the logo sting.

  python3 logo_spec.py --svg logo.svg --accent '#E5603A' --out spec.json
  python3 logo_spec.py --svg logo.svg --mark 3 --order 2,0,1 --out spec.json

Every visible <path> is read in document order (through <g>, <a> and <switch>); its path data is copied verbatim and
its bounding box is exact (Bezier and arc extrema are solved, not sampled). The lockup is split into the mark (shapes
that slam in one per beat) and the word (everything that lands together on the bar):

  --mark auto  (default) split at the widest horizontal gap between shape clusters if it is wider than 4 % of the
               logo: paths left of it are the mark, right of it the word; no such gap -> the whole logo is the mark
  --mark N     the first N paths in document order are the mark

Each mark path is one stroke; a mark of more than 6 paths is grouped by overlapping boxes. --order sets hit order and
grouping explicitly: 0-based indices into the mark paths, '+' joins paths into one stroke (e.g. 2,0+1).

Shapes are never redrawn or edited. A translate or uniform scale (on the path or any parent) is baked by rewriting the
coordinates; any other transform, non-path shapes (rect, text, use ...), clip paths and masks, stroke-only paths and
badge/knock-out lockups (shapes of one colour drawn on a shape of another) are rejected with the reason. Fills only
inform the colours: the sting paints every shape in colors.final.
"""
import argparse
import hashlib
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import quoteattr

SCHEMA = "logo-sting-spec/v1"
SVG_NS = "http://www.w3.org/2000/svg"
MAX_STROKES = 6
GAP_MIN = 0.04  # a mark/word split needs a horizontal gap wider than this share of the logo width
CHROMA_MIN = 24  # fills whose RGB channels spread less than this are white, black or grey: never the accent
HOT_MIX = 0.6  # default hot colour: the accent mixed this far toward white

CMD_ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}
NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
SEP = re.compile(r"[\s,]*")
CONTAINERS = {"svg", "g", "a", "switch"}
SKIP = {"defs", "style", "title", "desc", "metadata", "clipPath", "mask", "linearGradient", "radialGradient", "pattern",
        "symbol", "marker", "filter", "foreignObject", "script", "font", "font-face"}
SHAPES = {"rect", "circle", "ellipse", "line", "polyline", "polygon", "text", "use", "image"}
PROPS = ("fill", "fill-rule", "stroke", "stroke-width", "display", "visibility", "clip-path", "mask", "filter")
INHERITED = ("fill", "fill-rule", "stroke", "stroke-width", "visibility")
NAMED = {"white": "#FFFFFF", "black": "#000000", "red": "#FF0000", "lime": "#00FF00", "green": "#008000",
         "blue": "#0000FF", "yellow": "#FFFF00", "orange": "#FFA500", "gray": "#808080", "grey": "#808080"}


class SpecError(Exception):
    pass


def fail(msg):
    raise SpecError(msg)


def warn(msg):
    print(f"logo_spec: warning: {msg}", file=sys.stderr)


# ------------------------------------------------------------------------------------------------ path data


def parse_d(d):
    """Path data -> [[cmd, [argset, ...], end_offset], ...]; argsets keep the implicit repeats of one letter."""
    out, i, n, cmd = [], 0, len(d), None
    while True:
        i = SEP.match(d, i).end()
        if i >= n:
            break
        ch = d[i]
        if ch.isalpha():
            if ch.upper() not in CMD_ARGS:
                fail(f"path data: unknown command {ch!r} at offset {i}")
            cmd = ch
            out.append([cmd, [[]] if cmd in "Zz" else [], i + 1])
            i += 1
            continue
        if cmd is None or cmd in "Zz":
            fail(f"path data: number without a command at offset {i}: {d[max(0, i - 12): i + 12]!r}")
        args = []
        for j in range(CMD_ARGS[cmd.upper()]):
            if j:
                i = SEP.match(d, i).end()
            if cmd in "Aa" and j in (3, 4):  # arc flags may be packed without separators
                if i < n and d[i] in "01":
                    args.append(float(d[i]))
                    i += 1
                    continue
                fail(f"path data: bad arc flag at offset {i}")
            m = NUM.match(d, i)
            if not m:
                fail(f"path data: expected a number for {cmd!r} at offset {i}: {d[max(0, i - 12): i + 12]!r}")
            args.append(float(m.group()))
            i = m.end()
        out[-1][1].append(args)
        out[-1][2] = i
    if not out:
        return out
    if out[0][0] not in "Mm":
        fail("path data must start with a moveto")
    for c, sets, _ in out:
        if c not in "Zz" and not sets:
            fail(f"path data: command {c!r} without arguments")
    return out


def walk(cmds):
    """Absolute segments: ('M', p), ('L', p0, p1), ('Z', p0, p1), ('C', p0, c1, c2, p1), ('Q', p0, c, p1),
    ('A', p0, rx, ry, phi_deg, large, sweep, p1)."""
    cx = cy = sx = sy = 0.0
    last_c = last_q = None
    for cmd, sets, _ in cmds:
        up = cmd.upper()
        rel = cmd != up
        for k, a in enumerate(sets):
            ox, oy = (cx, cy) if rel else (0.0, 0.0)
            nc = nq = None
            p0 = (cx, cy)
            if up == "M" and k == 0:
                cx, cy = a[0] + ox, a[1] + oy
                sx, sy = cx, cy
                yield ("M", (cx, cy))
            elif up in "ML":
                cx, cy = a[0] + ox, a[1] + oy
                yield ("L", p0, (cx, cy))
            elif up == "H":
                cx = a[0] + ox
                yield ("L", p0, (cx, cy))
            elif up == "V":
                cy = a[0] + oy
                yield ("L", p0, (cx, cy))
            elif up in "CS":
                if up == "C":
                    c1, c2, p1 = (a[0] + ox, a[1] + oy), (a[2] + ox, a[3] + oy), (a[4] + ox, a[5] + oy)
                else:
                    c1 = (2 * cx - last_c[0], 2 * cy - last_c[1]) if last_c else p0
                    c2, p1 = (a[0] + ox, a[1] + oy), (a[2] + ox, a[3] + oy)
                yield ("C", p0, c1, c2, p1)
                nc = c2
                cx, cy = p1
            elif up in "QT":
                if up == "Q":
                    q, p1 = (a[0] + ox, a[1] + oy), (a[2] + ox, a[3] + oy)
                else:
                    q = (2 * cx - last_q[0], 2 * cy - last_q[1]) if last_q else p0
                    p1 = (a[0] + ox, a[1] + oy)
                yield ("Q", p0, q, p1)
                nq = q
                cx, cy = p1
            elif up == "A":
                p1 = (a[5] + ox, a[6] + oy)
                yield ("A", p0, a[0], a[1], a[2], a[3], a[4], p1)
                cx, cy = p1
            else:  # Z
                yield ("Z", p0, (sx, sy))
                cx, cy = sx, sy
            last_c, last_q = nc, nq


def arc_centre(p0, rx, ry, phi_deg, large, sweep, p1):
    """SVG endpoint -> centre parametrisation (implementation notes F.6.5); None when the arc is a straight line."""
    if p0 == p1:
        return None
    rx, ry = abs(rx), abs(ry)
    if rx == 0 or ry == 0:
        return None
    phi = math.radians(phi_deg % 360)
    cp, sp = math.cos(phi), math.sin(phi)
    dx2, dy2 = (p0[0] - p1[0]) / 2, (p0[1] - p1[1]) / 2
    x1p, y1p = cp * dx2 + sp * dy2, -sp * dx2 + cp * dy2
    lam = x1p ** 2 / rx ** 2 + y1p ** 2 / ry ** 2
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    coef = math.sqrt(max(0.0, num / den)) * (-1 if large == sweep else 1)
    cxp, cyp = coef * rx * y1p / ry, -coef * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (p0[0] + p1[0]) / 2
    cy = sp * cxp + cp * cyp + (p0[1] + p1[1]) / 2
    th1 = math.atan2((y1p - cyp) / ry, (x1p - cxp) / rx)
    th2 = math.atan2((-y1p - cyp) / ry, (-x1p - cxp) / rx)
    dth = (th2 - th1) % (2 * math.pi)
    if not sweep and dth > 0:
        dth -= 2 * math.pi
    return cx, cy, rx, ry, cp, sp, th1, dth


def arc_point(ac, th):
    cx, cy, rx, ry, cp, sp = ac[:6]
    return (cx + rx * cp * math.cos(th) - ry * sp * math.sin(th), cy + rx * sp * math.cos(th) + ry * cp * math.sin(th))


def _unit_roots(a, b, c):
    """Roots of a t^2 + b t + c inside (0, 1)."""
    if abs(a) < 1e-12:
        return [-c / b] if abs(b) > 1e-12 and 0 < -c / b < 1 else []
    disc = b * b - 4 * a * c
    if disc < 0:
        return []
    r = math.sqrt(disc)
    return [t for t in ((-b + r) / (2 * a), (-b - r) / (2 * a)) if 0 < t < 1]


def _cubic(p0, c1, c2, p1, t):
    m = 1 - t
    return tuple(m ** 3 * p0[i] + 3 * m * m * t * c1[i] + 3 * m * t * t * c2[i] + t ** 3 * p1[i] for i in (0, 1))


def _quad(p0, q, p1, t):
    m = 1 - t
    return tuple(m * m * p0[i] + 2 * m * t * q[i] + t * t * p1[i] for i in (0, 1))


def bbox(cmds):
    """Exact bounding box [x0, y0, x1, y1] of the drawn segments, or None when nothing is drawn."""
    pts = []
    for s in walk(cmds):
        kind = s[0]
        if kind == "M":
            continue
        p0, p1 = s[1], s[-1]
        pts += [p0, p1]
        if kind == "C":
            _, p0, c1, c2, p1 = s
            for i in (0, 1):
                a = p1[i] - 3 * c2[i] + 3 * c1[i] - p0[i]
                b = 2 * (c2[i] - 2 * c1[i] + p0[i])
                pts += [_cubic(p0, c1, c2, p1, t) for t in _unit_roots(a, b, c1[i] - p0[i])]
        elif kind == "Q":
            _, p0, q, p1 = s
            for i in (0, 1):
                den = p0[i] - 2 * q[i] + p1[i]
                if abs(den) > 1e-12 and 0 < (p0[i] - q[i]) / den < 1:
                    pts.append(_quad(p0, q, p1, (p0[i] - q[i]) / den))
        elif kind == "A":
            ac = arc_centre(*s[1:])
            if ac:
                _, _, rx, ry, cp, sp, th1, dth = ac
                for base in (math.atan2(-ry * sp, rx * cp), math.atan2(ry * cp, rx * sp)):
                    for th in (base, base + math.pi):
                        if ((th - th1) * (1 if dth > 0 else -1)) % (2 * math.pi) <= abs(dth):
                            pts.append(arc_point(ac, th))
    if not pts:
        return None
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return [min(xs), min(ys), max(xs), max(ys)]


def flatten(cmds, n=16):
    """Closed polylines, one per subpath, curves sampled n times (for winding and inside tests only)."""
    polys, cur = [], None
    for s in walk(cmds):
        kind = s[0]
        if kind == "M":
            cur = [s[1]]
            polys.append(cur)
            continue
        if cur is None:  # drawing straight after a closepath starts a new subpath at its start point
            cur = [s[1]]
            polys.append(cur)
        if kind in "LZ":
            cur.append(s[2])
        elif kind == "C":
            cur += [_cubic(*s[1:], k / n) for k in range(1, n + 1)]
        elif kind == "Q":
            cur += [_quad(*s[1:], k / n) for k in range(1, n + 1)]
        else:
            ac = arc_centre(*s[1:])
            cur += [arc_point(ac, ac[6] + ac[7] * k / (2 * n)) for k in range(1, 2 * n + 1)] if ac else [s[-1]]
        if kind == "Z":
            cur = None
    return [p for p in polys if len(p) > 2]


def signed_area(poly):
    return 0.5 * sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))


def winding(polys, pt):
    w = 0
    x, y = pt
    for poly in polys:
        for i in range(len(poly)):
            (x0, y0), (x1, y1) = poly[i - 1], poly[i]
            if y0 <= y < y1 and (x1 - x0) * (y - y0) - (x - x0) * (y1 - y0) > 0:
                w += 1
            elif y1 <= y < y0 and (x1 - x0) * (y - y0) - (x - x0) * (y1 - y0) < 0:
                w -= 1
    return w


def filled(shape, pt):
    w = winding(shape["polys"], pt)
    return w % 2 == 1 if shape["rule"] == "evenodd" else w != 0


def fmt(v):
    s = ("%.6f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def bake(cmds, s, tx, ty):
    """Rewrite path data under x' = s x + tx, y' = s y + ty (s > 0): a whole-shape move and uniform scale."""
    out = []
    for n, (cmd, sets, _) in enumerate(cmds):
        up = cmd.upper()
        rel = cmd != up
        parts = []
        for k, a in enumerate(sets):
            a = list(a)
            shift = not rel or (n == 0 and k == 0)  # a leading 'm' is absolute
            if up == "H":
                a = [s * a[0] + (tx if shift else 0)]
            elif up == "V":
                a = [s * a[0] + (ty if shift else 0)]
            elif up == "A":
                a = [s * a[0], s * a[1], a[2], a[3], a[4], s * a[5] + (tx if shift else 0), s * a[6] + (ty if shift else 0)]
            else:
                a = [s * v + ((tx if j % 2 == 0 else ty) if shift else 0) for j, v in enumerate(a)]
            parts.append(" ".join(fmt(v) for v in a))
        out.append(cmd + " ".join(parts))
    return "".join(out)


def absolute_start(d, cmds):
    """The same path with a leading relative moveto spelled absolute, so it can follow other path data."""
    cmd, sets, end = cmds[0]
    if cmd == "M":
        return d
    head = "M" + " ".join(fmt(v) for v in sets[0])
    if len(sets) > 1:
        head += "l" + " ".join(fmt(v) for a in sets[1:] for v in a)
    return head + d[end:]


# ------------------------------------------------------------------------------------------------ svg tree


def local(el):
    tag = el.tag
    if not isinstance(tag, str):
        return None
    if tag.startswith("{"):
        ns, _, name = tag[1:].partition("}")
        return name if ns == SVG_NS else None
    return tag


def decls(text):
    out = {}
    for item in (text or "").split(";"):
        k, sep, v = item.partition(":")
        if sep:
            out[k.strip().lower()] = v.strip()
    return out


def parse_css(root):
    rules = []
    for el in root.iter():
        if local(el) != "style":
            continue
        text = re.sub(r"/\*.*?\*/", "", "".join(el.itertext()), flags=re.S)
        for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", text):
            d = decls(body)
            for s in sel.split(","):
                s = s.strip()
                if re.fullmatch(r"[A-Za-z][\w-]*", s):
                    rules.append((0, "tag", s, d))
                elif re.fullmatch(r"\.[\w-]+", s):
                    rules.append((1, "class", s[1:], d))
                elif re.fullmatch(r"#[\w-]+", s):
                    rules.append((2, "id", s[1:], d))
    rules.sort(key=lambda r: r[0])  # stable: source order within a specificity
    return rules


def specified(el, css):
    """Presentation attributes < CSS rules (tag < class < id) < style attribute."""
    sp = {p: el.get(p).strip() for p in PROPS if el.get(p) is not None}
    tag, classes, eid = local(el), (el.get("class") or "").split(), el.get("id")
    for _, kind, key, d in css:
        if (kind == "tag" and key == tag) or (kind == "class" and key in classes) or (kind == "id" and key == eid):
            sp.update({k: v for k, v in d.items() if k in PROPS})
    sp.update({k: v for k, v in decls(el.get("style")).items() if k in PROPS})
    return sp


def parse_color(v):
    v = (v or "").strip()
    low = v.lower()
    if low in ("none", "transparent"):
        return "none"
    m = re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", v)
    if m:
        h = m.group(1)
        return "#" + ("".join(c * 2 for c in h) if len(h) == 3 else h).upper()
    m = re.fullmatch(r"rgba?\(([^)]*)\)", low)
    if m:
        ch = [c.strip() for c in m.group(1).replace("/", ",").split(",")][:3]
        if len(ch) == 3:
            try:
                vals = [float(c[:-1]) * 2.55 if c.endswith("%") else float(c) for c in ch]
            except ValueError:
                return None
            return "#" + "".join("%02X" % max(0, min(255, int(x + 0.5))) for x in vals)
    return NAMED.get(low)


def rgb(hexc):
    n = int(hexc[1:], 16)
    return (n >> 16) & 255, (n >> 8) & 255, n & 255


def chromatic(hexc):
    if not hexc or not hexc.startswith("#"):
        return False
    c = rgb(hexc)
    return max(c) - min(c) >= CHROMA_MIN


def flag_color(v, name):
    c = parse_color(v)
    if not c or not re.fullmatch(r"#?[0-9a-fA-F]{3}([0-9a-fA-F]{3})?", v.strip()):
        fail(f"--{name} must be a hex colour like #E5603A, got {v!r}")
    return c


def mat_mul(m1, m2):
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2, a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def parse_transform(s, where):
    m = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    if re.sub(r"[a-zA-Z]+\s*\([^)]*\)|[\s,]", "", s):
        fail(f"{where}: cannot read transform {s!r}")
    for name, args in re.findall(r"([a-zA-Z]+)\s*\(([^)]*)\)", s):
        v = [float(x) for x in NUM.findall(args)]
        if name == "matrix" and len(v) == 6:
            t = tuple(v)
        elif name == "translate" and len(v) in (1, 2):
            t = (1.0, 0.0, 0.0, 1.0, v[0], v[1] if len(v) == 2 else 0.0)
        elif name == "scale" and len(v) in (1, 2):
            t = (v[0], 0.0, 0.0, v[-1], 0.0, 0.0)
        elif name == "rotate" and len(v) in (1, 3):
            c, sn = math.cos(math.radians(v[0])), math.sin(math.radians(v[0]))
            t = (c, sn, -sn, c, 0.0, 0.0)
            if len(v) == 3:
                t = mat_mul(mat_mul((1, 0, 0, 1, v[1], v[2]), t), (1, 0, 0, 1, -v[1], -v[2]))
        elif name in ("skewX", "skewY") and len(v) == 1:
            k = math.tan(math.radians(v[0]))
            t = (1.0, 0.0, k, 1.0, 0.0, 0.0) if name == "skewX" else (1.0, k, 0.0, 1.0, 0.0, 0.0)
        else:
            fail(f"{where}: cannot read transform {s!r}")
        m = mat_mul(m, t)
    return m


def uniform(m):
    """(s, tx, ty) when the matrix is a translate plus a positive uniform scale, else None."""
    a, b, c, d, e, f = m
    tol = 1e-9 * max(1.0, abs(a))
    if abs(b) <= tol and abs(c) <= tol and abs(a - d) <= tol and a > 0:
        return a, e, f
    return None


def collect(root, css):
    """Visible paths in paint order, with their computed fill, fill rule and full transform."""
    shapes, problems, counts = [], [], {}

    def where_of(el, name):
        counts[name] = counts.get(name, 0) + 1
        bits = [f"<{name}> #{counts[name]}"]
        for key in ("id", "class"):
            if el.get(key):
                bits.append(f"{key}={el.get(key)!r}")
        if name == "text":
            bits.append(repr(" ".join("".join(el.itertext()).split())))
        return " ".join(bits)

    def visit(el, ctm, inh, is_root=False):
        name = local(el)
        if name is None or name in SKIP:
            return
        where = where_of(el, name)
        sp = specified(el, css)
        if sp.get("display") == "none":
            return
        st = dict(inh)
        st.update({p: sp[p] for p in INHERITED if p in sp and sp[p] != "inherit"})
        if el.get("transform"):
            ctm = mat_mul(ctm, parse_transform(el.get("transform"), where))
        for p in ("clip-path", "mask"):
            if sp.get(p, "none") != "none":
                problems.append(f"{where} has {p}={sp[p]!r}: the visible shape depends on it; release the clipping "
                                "mask / expand the appearance in the design tool and export again")
        if sp.get("filter", "none") != "none":
            warn(f"{where} has filter={sp['filter']!r}: ignored, only the shapes are used")
        if name == "svg" and not is_root:
            problems.append(f"{where}: nested <svg> is not supported; flatten it into the main document")
            return
        if name in CONTAINERS:
            kids = list(el)
            if name == "switch":  # the first child whose test passes renders; unknown extensions never pass
                kids = [k for k in kids if local(k) is not None and not (k.get("requiredExtensions") or "").strip()][:1]
            for k in kids:
                visit(k, ctm, st)
            return
        if name in SHAPES:
            why = ("live text has no path data and depends on installed fonts; convert the text to outlines "
                   "(Illustrator: Type > Create Outlines, Figma: Outline stroke / Flatten) and export again"
                   if name == "text" else
                   "a <use> reference; expand/ungroup it in the design tool" if name == "use" else
                   "a raster image cannot be animated as shapes" if name == "image" else
                   "only <path> shapes are read; convert it to a path (Illustrator: Object > Compound Path > Make, "
                   "or export with 'convert shapes to paths')")
            problems.append(f"{where}: {why}")
            return
        if name != "path":
            warn(f"{where}: unknown element ignored")
            return
        if st.get("visibility") in ("hidden", "collapse"):
            return
        d = el.get("d") or ""
        try:
            cmds = parse_d(d)
        except SpecError as e:
            problems.append(f"{where}: {e}")
            return
        if not cmds:
            return
        fill = parse_color(st.get("fill", "black"))
        stroke = parse_color(st.get("stroke", "none"))
        if fill == "none":
            if stroke != "none":
                problems.append(f"{where} is stroke-only (fill none, stroke {st.get('stroke')!r}): outline the stroke "
                                "(Illustrator: Object > Path > Outline Stroke) and export again")
            return
        if stroke != "none" and (st.get("stroke-width") or "1").strip() not in ("0", "0px"):
            warn(f"{where} has a stroke ({st.get('stroke')}): ignored, outline it for an exact match")
        if ctm != (1.0, 0.0, 0.0, 1.0, 0.0, 0.0):
            u = uniform(ctm)
            if not u:
                problems.append(f"{where}: its transform (matrix {[round(v, 6) for v in ctm]}) rotates, skews or "
                                "scales unevenly; only translate and uniform scale can be baked without redrawing "
                                "the shape. Apply/expand the transform in the design tool and export again")
                return
            d = bake(cmds, *u)
            cmds = parse_d(d)
        box = bbox(cmds)
        if box is None:
            return
        shapes.append({"d": d, "cmds": cmds, "box": box, "fill": fill, "fill_src": st.get("fill", "black"),
                       "rule": "evenodd" if st.get("fill-rule") == "evenodd" else "nonzero", "where": where})

    visit(root, (1.0, 0.0, 0.0, 1.0, 0.0, 0.0), {}, is_root=True)
    if problems:
        fail("the SVG cannot be used as it is:\n  - " + "\n  - ".join(problems))
    return shapes


def doc_fills(root, css):
    """Every fill written anywhere in the document, in order: attributes, style attributes, then <style> rules."""
    out = []
    for el in root.iter():
        name = local(el)
        if name is None:
            continue
        for src, val in (("fill attribute", el.get("fill")), ("style attribute", decls(el.get("style")).get("fill"))):
            if val:
                out.append((parse_color(val), f"{src} on <{name}>"))
    for _, kind, key, d in css:
        if "fill" in d:
            out.append((parse_color(d["fill"]), f"<style> rule {'.' if kind == 'class' else '#' if kind == 'id' else ''}{key}"))
    return out


# ------------------------------------------------------------------------------------------------ grouping


def union(boxes):
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]


def split_auto(shapes):
    """(mark, word, note): split at the widest horizontal gap between clusters of boxes, if wide enough."""
    lb = union([s["box"] for s in shapes])
    width = lb[2] - lb[0]
    order = sorted(range(len(shapes)), key=lambda i: shapes[i]["box"][0])
    best, run = None, shapes[order[0]]["box"][2]
    for j in range(1, len(order)):
        b = shapes[order[j]]["box"]
        if b[0] > run and (best is None or b[0] - run > best[0]):
            best = (b[0] - run, j, run, b[0])
        run = max(run, b[2])
    if best is None or width <= 0 or best[0] <= GAP_MIN * width:
        widest = f"widest gap {best[0]:.2f} = {100 * best[0] / width:.1f} %" if best and width > 0 else "no gap"
        return list(range(len(shapes))), [], f"no clear gap ({widest} of width {width:.2f}, needs > {100 * GAP_MIN:.0f} %): the whole logo is the mark"
    gap, j, x0, x1 = best
    left = set(order[:j])
    mark = [i for i in range(len(shapes)) if i in left]
    word = [i for i in range(len(shapes)) if i not in left]
    return mark, word, f"gap {gap:.2f} at x {x0:.2f}..{x1:.2f} ({100 * gap / width:.1f} % of width {width:.2f})"


def group_overlapping(idx, shapes):
    parent = {i: i for i in idx}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for a in idx:
        for b in idx:
            if a < b:
                p, q = shapes[a]["box"], shapes[b]["box"]
                if p[0] <= q[2] and q[0] <= p[2] and p[1] <= q[3] and q[1] <= p[3]:
                    parent[find(a)] = find(b)
    groups = {}
    for i in idx:
        groups.setdefault(find(i), []).append(i)
    return sorted(groups.values(), key=lambda g: g[0])


def parse_order(text, mark):
    groups = []
    for tok in text.split(","):
        try:
            groups.append([int(x) for x in tok.strip().split("+")])
        except ValueError:
            fail(f"--order: cannot read {tok!r}; use indices like 2,0,1 or 0+1,2")
    flat = sorted(i for g in groups for i in g)
    if flat != list(range(len(mark))):
        fail(f"--order must use every mark path index 0..{len(mark) - 1} exactly once, got {text!r}")
    return [[mark[i] for i in g] for g in groups]


def outer_sign(shape):
    polys = shape["polys"]
    a = max((signed_area(p) for p in polys), key=abs, default=0.0)
    return (a > 0) - (a < 0)


def joined(group, shapes):
    members = [shapes[i] for i in group]
    if len(members) == 1:
        return members[0]["d"], members[0]["rule"]
    rules = {m["rule"] for m in members}
    signs = {outer_sign(m) for m in members} - {0}
    if len(rules) > 1 or len(signs) > 1:
        names = ", ".join(m["where"] for m in members)
        why = "mixed fill rules" if len(rules) > 1 else "opposite winding directions"
        fail(f"cannot join {names} into one stroke: {why} would cut holes where they overlap. "
             "Choose the strokes explicitly with --order (indices into the mark paths, '+' joins) or --mark N")
    return " ".join(absolute_start(m["d"], m["cmds"]) for m in members), rules.pop()


def knockouts(shapes):
    """Shapes painted on top of a shape of another colour whose fill covers them: a badge or knock-out lockup."""
    found = []
    for j, top in enumerate(shapes):
        for i in range(j):
            under = shapes[i]
            if under["fill"] == top["fill"] or not (under["fill"] or "").startswith("#") or not (top["fill"] or "").startswith("#"):
                continue
            b, t = under["box"], top["box"]
            if not (b[0] <= t[0] and b[1] <= t[1] and t[2] <= b[2] and t[3] <= b[3]):
                continue
            pts = [p for poly in top["polys"] for p in poly]
            if pts and sum(filled(under, p) for p in pts) > 0.5 * len(pts):
                found.append((under, top))
                break
    return found


# ------------------------------------------------------------------------------------------------ main


def num(v):
    v = round(v, 4) + 0.0
    return int(v) if v == int(v) else v


def nums(vals):
    return [num(v) for v in vals]


def dumps(obj):
    text = json.dumps(obj, indent=2, ensure_ascii=False)
    return re.sub(r"\[\s+([-0-9.eE+,\s]+?)\s+\]", lambda m: "[" + ", ".join(x.strip() for x in m.group(1).split(",")) + "]", text)


# grouping check only: distinct hues per hit, never brand colours
PREVIEW_COLOURS = ["#E6194B", "#3CB44B", "#4363D8", "#F58231", "#911EB4", "#42D4F4"]


def preview_svg(spec):
    """A quick-look SVG of the grouping: mark strokes in distinct colours numbered in hit order, the word in grey."""
    x0, y0, x1, y1 = spec["logoBox"]
    pad = 0.08 * max(x1 - x0, y1 - y0)
    w, h = x1 - x0 + 2 * pad, y1 - y0 + 2 * pad
    fs = 0.16 * (y1 - y0)
    px = 1200 / max(w, h)
    vb = f"{num(x0 - pad)} {num(y0 - pad)} {num(w)} {num(h)}"
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{round(w * px)}" height="{round(h * px)}">',
           f'<rect x="{num(x0 - pad)}" y="{num(y0 - pad)}" width="{num(w)}" height="{num(h)}" fill="#000000"/>']
    for e in spec["word"]:
        out.append(f'<path d={quoteattr(e["d"])} fill="#8C8C8C" fill-rule="{e.get("rule", "nonzero")}"/>')
    for i, e in enumerate(spec["mark"]):
        out.append(f'<path d={quoteattr(e["d"])} fill="{PREVIEW_COLOURS[i % len(PREVIEW_COLOURS)]}" '
                   f'fill-rule="{e.get("rule", "nonzero")}"/>')
    for i, e in enumerate(spec["mark"]):
        cx, cy = e.get("c") or [(e["box"][0] + e["box"][2]) / 2, (e["box"][1] + e["box"][3]) / 2]
        out.append(f'<text x="{num(cx)}" y="{num(cy)}" font-size="{num(fs)}" font-family="sans-serif" font-weight="700" '
                   f'text-anchor="middle" dominant-baseline="central" fill="#FFFFFF" stroke="#000000" '
                   f'stroke-width="{num(fs * 0.12)}" paint-order="stroke">{i + 1}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def build(args):
    path = Path(args.svg)
    raw = path.read_bytes()
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        fail(f"{path.name} is not well-formed XML: {e}")
    if local(root) != "svg":
        fail(f"{path.name}: the root element is not <svg>")
    css = parse_css(root)
    vb = [float(x) for x in NUM.findall(root.get("viewBox") or "")]
    if len(vb) != 4:
        w, h = (re.fullmatch(r"\s*([-+]?(?:\d+\.?\d*|\.\d+))(?:px)?\s*", root.get(k) or "") for k in ("width", "height"))
        vb = [0.0, 0.0, float(w.group(1)), float(h.group(1))] if w and h else None

    shapes = collect(root, css)
    dropped = []
    if vb:
        inside = lambda b: b[2] >= vb[0] and b[0] <= vb[0] + vb[2] and b[3] >= vb[1] and b[1] <= vb[1] + vb[3]
        dropped = [s for s in shapes if not inside(s["box"])]
        shapes = [s for s in shapes if inside(s["box"])]
    if not shapes:
        fail(f"{path.name}: no visible <path> shapes inside the viewBox")
    for s in shapes:
        s["polys"] = flatten(s["cmds"])

    ko = knockouts(shapes)
    if ko:
        lines = [f"{t['where']} ({t['fill']}) sits on {u['where']} ({u['fill']})" for u, t in ko]
        fail(f"{path.name} is a badge / knock-out lockup: shapes of one colour are drawn on a shape of another colour "
             f"({'; '.join(lines)}). The sting paints every shape in one colour (colors.final), so they would merge "
             "into a solid block. Use the single-colour version of the logo (shapes only, no badge or background).")
    fills = sorted({s["fill"] for s in shapes if s["fill"] and s["fill"].startswith("#")})
    if len(fills) > 1:
        warn(f"the logo uses {len(fills)} fill colours ({', '.join(fills)}); the sting paints every shape in colors.final")

    if args.mark == "auto":
        mark, word, note = split_auto(shapes)
    else:
        try:
            n = int(args.mark)
        except ValueError:
            fail(f"--mark must be 'auto' or a number, got {args.mark!r}")
        if not 1 <= n <= len(shapes):
            fail(f"--mark {n}: the SVG has {len(shapes)} visible paths")
        mark, word, note = list(range(n)), list(range(n, len(shapes))), f"--mark {n}: first {n} paths in document order"

    if args.order:
        groups = parse_order(args.order, mark)
        gnote = f"--order {args.order}"
    elif len(mark) > MAX_STROKES:
        groups = group_overlapping(mark, shapes)
        gnote = f"{len(mark)} mark paths > {MAX_STROKES}: grouped by overlapping boxes into {len(groups)} strokes"
        if len(groups) > MAX_STROKES:
            warn(f"{len(groups)} strokes is a long build (one beat each); pick fewer with --mark N or join with --order")
    else:
        groups = [[i] for i in mark]
        gnote = "one stroke per mark path"

    mark_out = []
    for g in groups:
        d, rule = joined(g, shapes)
        b = union([shapes[i]["box"] for i in g])
        e = {"d": d, "box": nums(b), "c": nums([(b[0] + b[2]) / 2, (b[1] + b[3]) / 2])}
        if rule == "evenodd":
            e["rule"] = "evenodd"
        mark_out.append(e)
    word_out = []
    for i in word:
        e = {"d": shapes[i]["d"], "box": nums(shapes[i]["box"])}
        if shapes[i]["rule"] == "evenodd":
            e["rule"] = "evenodd"
        word_out.append(e)

    accent, accent_src = None, None
    if args.accent:
        accent, accent_src = flag_color(args.accent, "accent"), "--accent"
    else:
        cands = [(s["fill"], f"fill of {s['where']}") for s in shapes] + doc_fills(root, css)
        accent, accent_src = next(((c, src) for c, src in cands if chromatic(c)), (None, None))
        if not accent:
            fail(f"{path.name} has no coloured (non-white/black/grey) fill to take the accent from: pass --accent "
                 "'#RRGGBB' with the brand's accent colour (it drives the glows, flares, sparks and rings)")
        if not accent_src.startswith("fill of"):
            accent_src += ", not on any visible shape: check it is the brand accent or pass --accent"
    if args.hot:
        hot, hot_src = flag_color(args.hot, "hot"), "--hot"
    else:
        hot = "#" + "".join("%02X" % int(c + HOT_MIX * (255 - c) + 0.5) for c in rgb(accent))
        hot_src = f"accent mixed {100 * HOT_MIX:.0f} % toward white"
    colors = {"final": flag_color(args.final, "final"), "accent": accent, "hot": hot,
              "background": flag_color(args.background, "background")}

    mb = union([shapes[i]["box"] for i in mark])
    wb = union([shapes[i]["box"] for i in word]) if word else None
    lb = union([mb] + ([wb] if wb else []))
    spec = {
        "schema": SCHEMA,
        "source": path.name,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "viewBox": nums(vb if vb else [lb[0], lb[1], lb[2] - lb[0], lb[3] - lb[1]]),
        "mark": mark_out,
        "word": word_out,
        "markBox": nums(mb),
        "wordBox": nums(wb) if wb else None,
        "logoBox": nums(lb),
        "colors": colors,
    }

    log = [f"logo_spec: {path.name}  viewBox {spec['viewBox']}  {len(shapes)} paths"
           + (f" ({len(dropped)} outside the viewBox dropped)" if dropped else "")]
    if not vb:
        log.append("  no viewBox/width/height: viewBox set to the logo box")
    log.append(f"  split: {note} -> mark {len(mark)} paths, word {len(word)} paths")
    log.append(f"  strokes: {gnote}")
    for k, e in enumerate(mark_out):
        log.append(f"  stroke {k + 1}: box {e['box']}  c {e['c']}")
    log.append(f"  markBox {spec['markBox']}  wordBox {spec['wordBox']}  logoBox {spec['logoBox']}")
    log.append(f"  colors: final {colors['final']}, accent {accent} ({accent_src}), hot {hot} ({hot_src}), "
               f"background {colors['background']}")
    return spec, "\n".join(log)


def main():
    ap = argparse.ArgumentParser(description="Official logo SVG -> logo spec JSON (logo-sting-spec/v1).")
    ap.add_argument("--svg", required=True, help="the official logo SVG (single-colour lockup, shapes as <path>)")
    ap.add_argument("--out", help="spec JSON to write (default: stdout)")
    ap.add_argument("--mark", default="auto", help="'auto' (split at the widest horizontal gap) or N: first N paths")
    ap.add_argument("--order", help="hit order of the mark paths, 0-based, '+' joins paths into one stroke: 2,0+1")
    ap.add_argument("--final", default="#FFFFFF", help="resting logo colour (default #FFFFFF)")
    ap.add_argument("--accent", help="glow/flare/spark colour (default: first coloured fill in the SVG)")
    ap.add_argument("--hot", help=f"hottest light (default: accent mixed {100 * HOT_MIX:.0f} %% toward white)")
    ap.add_argument("--background", default="#000000", help="background colour (default #000000)")
    ap.add_argument("--preview", help="also write a quick-look SVG of the grouping: strokes numbered in hit order, "
                    "word in grey (rasterise with rsvg-convert, qlmanage or a browser)")
    args = ap.parse_args()
    try:
        spec, log = build(args)
    except SpecError as e:
        print(f"logo_spec: error: {e}", file=sys.stderr)
        return 2
    text = dumps(spec) + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
        log += f"\n  wrote {args.out}"
    else:
        sys.stdout.write(text)
    if args.preview:
        Path(args.preview).parent.mkdir(parents=True, exist_ok=True)
        Path(args.preview).write_text(preview_svg(spec), encoding="utf-8")
        log += f"\n  wrote preview {args.preview}"
    print(log, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
