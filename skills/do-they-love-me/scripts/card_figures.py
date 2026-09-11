#!/usr/bin/env python3
"""Emit the card figures as inline-SVG fragments plus the copy that goes with them.

Designed for a 1080-wide card whose content width is 904 (see the mobile
infographic standard). Colours are referenced through CSS custom properties so
the host card keeps its own palette:

  --primary --accent --accent-ink --ink --muted --paper --soft-line --tint

Outputs: figure-matrix.svg, figure-composition.svg, figure-weekly.svg, card-data.json
"""

import argparse
import json
from pathlib import Path

WD = ["一", "二", "三", "四", "五", "六", "日"]
SEGMENTS = [
    ("cp-work", "工作", "work"),
    ("cp-love", "情感", "love"),
    ("cp-life", "生活", "life"),
    ("cp-none", "无内容", "other"),
]


def week_of(iso, start_date):
    from datetime import date

    y, m, d = (int(p) for p in iso.split("-"))
    return (date(y, m, d) - date.fromisoformat(start_date)).days // 7


def matrix_svg(matrix, content, partner, owner):
    days = matrix["days"]
    start = days[0]["d"]
    label_w, gap = 44, 8
    cols = max(week_of(d["d"], start) for d in days) + 1
    cell = max(20, min(56, (content - label_w - gap * (cols - 1)) // cols))
    grid_y = 44
    height = grid_y + 7 * cell + 6 * gap + 8
    max_other = max(1, matrix["totals"]["max_other"])
    max_me = max(1, matrix["totals"]["max_me"])

    out = [f'<svg viewBox="0 0 {content} {height}" role="img" '
           f'aria-label="按日期的对话矩阵">']
    months = {}
    for d in days:
        months.setdefault(d["d"][5:7], week_of(d["d"], start))
    for month, col in months.items():
        out.append(
            f'<text class="mx-strong" x="{label_w + col * (cell + gap)}" y="30">{int(month)}月</text>'
        )
    for row, name in enumerate(WD):
        out.append(
            f'<text x="{label_w - 12}" y="{grid_y + row * (cell + gap) + cell // 2 + 9}" '
            f'text-anchor="end">{name}</text>'
        )
    for d in days:
        x = label_w + week_of(d["d"], start) * (cell + gap)
        y = grid_y + d["wd"] * (cell + gap)
        out.append(
            f'<rect class="mx-empty" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="8"/>'
        )
        if d["other"]:
            op = 0.18 + 0.82 * d["other"] / max_other
            out.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell // 2 - 1}" rx="7" '
                f'fill="var(--accent)" fill-opacity="{op:.2f}"/>'
            )
        if d["me"]:
            op = 0.18 + 0.82 * d["me"] / max_me
            out.append(
                f'<rect x="{x}" y="{y + cell // 2 + 1}" width="{cell}" '
                f'height="{cell // 2 - 1}" rx="7" fill="var(--primary)" '
                f'fill-opacity="{op:.2f}"/>'
            )
    lx = label_w + cols * cell + (cols - 1) * gap + 28
    for i, (fill, text) in enumerate(
        (("var(--accent)", f'{partner} {matrix["totals"]["other"]} 条'),
         ("var(--primary)", f'{owner} {matrix["totals"]["me"]} 条'))
    ):
        y = 60 + i * 44
        out.append(f'<rect x="{lx}" y="{y - 15}" width="26" height="18" rx="4" fill="{fill}"/>')
        out.append(f'<text class="mx-strong" x="{lx + 36}" y="{y}">{text}</text>')
    for i, line in enumerate(["颜色越深", "消息越多", "空格子＝那天", "没有聊天"]):
        out.append(f'<text x="{lx}" y="{168 + i * 38}">{line}</text>')
    out.append("</svg>")
    return "\n".join(out)


def composition_svg(data, content, partner, owner):
    bar_x, row_h, bar_h = 62 + 12, 132, 48
    bar_w = content - bar_x
    # colour swatches are part of the figure: without them the two bars only show
    # numbers and the reader cannot tell 工作 from 生活.
    legend_h = 46
    height = row_h * 2 + 10 + legend_h
    out = [f'<svg viewBox="0 0 {content} {height}" role="img" '
           f'aria-label="两个人的话题构成">']
    for row, (side, name) in enumerate((("other", partner), ("me", owner))):
        entry = data["sides"][side]
        y = row * row_h
        out.append(f'<text class="mx-strong" x="0" y="{y + bar_h // 2 + 9}">{name}</text>')
        x = bar_x
        for cls, _, key in SEGMENTS:
            pct = entry["pct"][key]
            w = bar_w * pct / 100
            out.append(
                f'<rect class="{cls}" x="{x:.1f}" y="{y}" width="{w:.1f}" '
                f'height="{bar_h}" rx="4"/>'
            )
            if pct >= 8:
                out.append(
                    f'<text class="mx-strong" x="{x + w / 2:.1f}" y="{y + bar_h + 28}" '
                    f'text-anchor="middle">{pct:.0f}%</text>'
                )
            x += w
    love_line = "、".join(
        f'{partner if s == "other" else owner} {data["sides"][s]["pct"]["love"]:.0f}%'
        for s in ("other", "me")
    )
    out.append(
        f'<text class="mx-accent" x="{bar_x}" y="{row_h * 2 + 2}">'
        f'情感类只占 {love_line}，色段很短</text>'
    )
    lx, ly = bar_x, height - 12
    for cls, label, _ in SEGMENTS:
        out.append(f'<rect class="{cls}" x="{lx:.1f}" y="{ly - 19}" width="20" height="20" rx="4"/>')
        out.append(f'<text x="{lx + 30:.1f}" y="{ly}">{label}</text>')
        lx += 30 + len(label) * 26 + 30
    out.append("</svg>")
    return "\n".join(out)


def weekly_svg(data, content):
    weeks = data["weeks"]
    height = 162
    x0, x1 = 76, content - 24
    y_top, y_base = 30, 118
    step = (x1 - x0) / max(1, len(weeks) - 1)
    top = max(40.0, max(w["pct"]["work"] for w in weeks) * 1.2)

    def px(i):
        return x0 + i * step

    def py(v):
        return y_base - (v / top) * (y_base - y_top)

    out = [f'<svg viewBox="0 0 {content} {height}" role="img" '
           f'aria-label="每周话题构成变化">']
    out.append(
        f'<line x1="{x0}" y1="{y_base}" x2="{x1}" y2="{y_base}" '
        f'stroke="var(--soft-line)" stroke-width="3"/>'
    )
    for v in (0, top / 2, top):
        out.append(
            f'<line x1="{x0}" y1="{py(v):.1f}" x2="{x1}" y2="{py(v):.1f}" '
            f'stroke="var(--soft-line)" stroke-width="1" stroke-opacity="0.5"/>'
        )
        out.append(f'<text x="{x0 - 12}" y="{py(v) + 9:.1f}" text-anchor="end">{v:.0f}%</text>')
    for key, stroke in (("work", "var(--primary)"), ("love", "var(--accent)")):
        points = " ".join(f'{px(i):.1f},{py(w["pct"][key]):.1f}' for i, w in enumerate(weeks))
        out.append(
            f'<polyline points="{points}" fill="none" stroke="{stroke}" '
            f'stroke-width="5" stroke-linejoin="round"/>'
        )
    for i, _ in enumerate(weeks):
        if i == 0:
            out.append(f'<text x="{px(i):.1f}" y="{y_base + 30}" text-anchor="start">第 1 周</text>')
        elif i == len(weeks) - 1:
            # 末周刻度若按中线对齐，文字会越过 SVG 视口右边界被裁掉；
            # 改为右对齐到内容右缘，和「工作／情感」两条末周标注同一基准。
            out.append(
                f'<text x="{content}" y="{y_base + 30}" text-anchor="end">第 {i + 1} 周</text>'
            )
        elif i % 2 == 0:
            out.append(
                f'<text x="{px(i):.1f}" y="{y_base + 30}" text-anchor="middle">第 {i + 1} 周</text>'
            )
    last = weeks[-1]
    out.append(
        f'<text class="mx-strong" x="{x1}" y="{py(last["pct"]["work"]) - 16:.1f}" '
        f'text-anchor="end">工作 {last["pct"]["work"]:.0f}%</text>'
    )
    out.append(
        f'<text class="mx-accent" x="{x1}" y="{py(last["pct"]["love"]) - 16:.1f}" '
        f'text-anchor="end">情感 {last["pct"]["love"]:.0f}%</text>'
    )
    first = weeks[0]["pct"]["work"]
    out.append(
        f'<text class="mx-strong" x="{px(0):.1f}" y="{py(first) - 16:.1f}" '
        f'text-anchor="start">第一周工作只有 {first:.0f}%</text>'
    )
    out.append("</svg>")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--composition", required=True)
    ap.add_argument("--metrics", default="")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--content-width", type=int, default=904)
    ap.add_argument("--partner-label", default="她")
    ap.add_argument("--owner-label", default="你")
    args = ap.parse_args()

    matrix = json.loads(Path(args.matrix).read_text(encoding="utf-8"))
    comp = json.loads(Path(args.composition).read_text(encoding="utf-8"))
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    figures = {
        "figure-matrix.svg": matrix_svg(matrix, args.content_width, args.partner_label, args.owner_label),
        "figure-composition.svg": composition_svg(comp, args.content_width, args.partner_label, args.owner_label),
        "figure-weekly.svg": weekly_svg(comp, args.content_width),
    }
    for name, svg in figures.items():
        (outdir / name).write_text(svg, encoding="utf-8")

    acc = comp.get("accuracy", {}).get("accuracy", {})
    card_data = {
        "span_days": matrix["range"],
        "totals": matrix["totals"],
        "sides": comp["sides"],
        "weeks": comp["weeks"],
        "index_weights": matrix["index_weights"],
        "accuracy": acc,
        "captions": {
            "matrix": "每格一天，上半个色块是对方、下半个是你，颜色越深消息越多；空格子就是那天谁都没说话。",
            "composition": "语义标注用本地模型完成，与手工校准集的一致率见口径行；媒体消息不计入分母。",
        },
    }
    if args.metrics:
        metrics = json.loads(Path(args.metrics).read_text(encoding="utf-8"))
        card_data["reply_gap"] = metrics.get("reply_gap")
        card_data["late_night"] = metrics.get("late_night")
        card_data["day_openers"] = metrics.get("day_openers")
        card_data["day_closers"] = metrics.get("day_closers")
        card_data["streak"] = metrics.get("streak")
        card_data["keywords"] = metrics.get("keywords")
    (outdir / "card-data.json").write_text(
        json.dumps(card_data, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(json.dumps({"figures": sorted(figures), "outdir": str(outdir)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
