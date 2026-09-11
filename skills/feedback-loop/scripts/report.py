#!/usr/bin/env python3
"""生成满意度复盘报告：Markdown、自包含 HTML 与 JSON 摘要。"""

from __future__ import annotations

import argparse
import html
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from feedback_store import (
    compute_stats,
    iso,
    load_events,
    load_outcomes,
    parse_since,
    resolve_store,
    utc_now,
)

POSITIVE_COLOR = "#2f9e6e"
NEGATIVE_COLOR = "#d4553f"
MIXED_COLOR = "#c9973b"
NEUTRAL_COLOR = "#8a8f98"


def format_rate(value: Optional[float]) -> str:
    return "n/a" if value is None else "{:.0%}".format(value)


def format_median(value: Optional[float]) -> str:
    return "n/a" if value is None else "{:.2f} 天".format(value)


def bar_chart(stats: Dict[str, Any]) -> str:
    daily: List[Dict[str, Any]] = stats.get("daily") or []
    if not daily:
        return '<p class="empty">窗口内没有可绘制的数据。</p>'
    width, height = 760, 240
    pad_left, pad_bottom, pad_top = 44, 34, 16
    plot_h = height - pad_bottom - pad_top
    max_total = max(sum(item["counts"].values()) for item in daily) or 1
    bar_slot = (width - pad_left - 16) / max(len(daily), 1)
    bar_width = max(6.0, min(38.0, bar_slot * 0.6))
    parts = ['<svg viewBox="0 0 {} {}" role="img" aria-label="每日反馈趋势">'.format(width, height)]
    for step in range(0, max_total + 1):
        y = pad_top + plot_h - (step / max_total) * plot_h
        parts.append('<line x1="{}" y1="{:.1f}" x2="{}" y2="{:.1f}" stroke="#e5e7eb" stroke-width="1"/>'.format(pad_left, y, width - 16, y))
        parts.append('<text x="{}" y="{:.1f}" font-size="10" fill="#8a8f98" text-anchor="end">{}</text>'.format(pad_left - 6, y + 3, step))
    for index, item in enumerate(daily):
        counts = item["counts"]
        x = pad_left + index * bar_slot + (bar_slot - bar_width) / 2
        y_cursor = pad_top + plot_h
        stack = [
            (int(counts.get("positive", 0)), POSITIVE_COLOR),
            (int(counts.get("mixed", 0)), MIXED_COLOR),
            (int(counts.get("neutral", 0)), NEUTRAL_COLOR),
            (int(counts.get("negative", 0)), NEGATIVE_COLOR),
        ]
        for value, color in stack:
            if value <= 0:
                continue
            segment = (value / max_total) * plot_h
            y_cursor -= segment
            parts.append('<rect x="{:.1f}" y="{:.1f}" width="{:.1f}" height="{:.1f}" fill="{}" rx="2"/>'.format(x, y_cursor, bar_width, segment, color))
        parts.append('<text x="{:.1f}" y="{}" font-size="10" fill="#5b616e" text-anchor="middle">{}</text>'.format(x + bar_width / 2, height - 12, html.escape(item["date"][5:])))
    parts.append("</svg>")
    legend = (
        '<div class="legend">'
        '<span><i style="background:{positive}"></i>正向</span>'
        '<span><i style="background:{mixed}"></i>混合</span>'
        '<span><i style="background:{neutral}"></i>中性</span>'
        '<span><i style="background:{negative}"></i>负向</span>'
        "</div>"
    ).format(positive=POSITIVE_COLOR, mixed=MIXED_COLOR, neutral=NEUTRAL_COLOR, negative=NEGATIVE_COLOR)
    return "".join(parts) + legend


def render_markdown(stats: Dict[str, Any], title: str) -> str:
    lines = ["# {}".format(title), "", "- 生成时间：{}".format(stats["generated_at"]), "- 窗口起点：{}".format(stats["window_since"] or "全部历史"), ""]
    lines += [
        "## 总览",
        "",
        "| 指标 | 数值 |",
        "| --- | --- |",
        "| 反馈事件 | {} |".format(stats["total"]),
        "| 满意率 | {} |".format(format_rate(stats["satisfaction_rate"])),
        "| 未闭环 | {} |".format(stats["unresolved_count"]),
        "| 修复时长中位数 | {} |".format(format_median(stats["median_time_to_verified_days"])),
        "| 极性分布 | {} |".format(json.dumps(stats["by_polarity"], ensure_ascii=False)),
        "",
    ]
    if stats["daily"]:
        lines += ["## 每日趋势", "", "| 日期 | 正向 | 混合 | 中性 | 负向 |", "| --- | --- | --- | --- | --- |"]
        for item in stats["daily"]:
            counts = item["counts"]
            lines.append("| {} | {} | {} | {} | {} |".format(item["date"], counts.get("positive", 0), counts.get("mixed", 0), counts.get("neutral", 0), counts.get("negative", 0)))
        lines.append("")
    lines += ["## 未闭环清单", ""]
    if stats["unresolved"]:
        lines += ["| 日期 | 极性 | 类型 | 强度 | 状态 | 停留天数 | 证据 |", "| --- | --- | --- | --- | --- | --- | --- |"]
        for item in stats["unresolved"]:
            evidence = item["evidence"].replace("|", "\\|")
            lines.append("| {} | {} | {} | {} | {} | {} | {} |".format(item["local_date"], item["polarity"], item["kind"], item.get("intensity", ""), item["status"], item["age_days"], evidence))
        lines.append("")
    else:
        lines += ["没有未闭环事件。", ""]
    if stats["by_kind"]:
        lines += ["## 类型分布", "", "| 类型 | 次数 |", "| --- | --- |"]
        for kind, count in stats["by_kind"].items():
            lines.append("| {} | {} |".format(kind, count))
        lines.append("")
    lines += [
        "## 口径",
        "",
        "- 满意率 = 正向事件 / 全部有效事件；混合单独统计，不计入分子。",
        "- 修复时长 = 事件时间到第一条 verified 结果的中位数。",
        "- 未闭环 = 状态不在 verified 或 declined 的事件，按时间从早到晚排列。",
        "",
        "原始数据：`events.jsonl`、`outcomes.jsonl`。",
    ]
    return "\n".join(lines) + "\n"


def render_html(stats: Dict[str, Any], title: str) -> str:
    rows = []
    for item in stats["unresolved"]:
        rows.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(str(item["local_date"])),
                html.escape(str(item["polarity"])),
                html.escape(str(item["kind"])),
                html.escape(str(item.get("intensity", ""))),
                html.escape(str(item["status"])),
                html.escape(str(item["age_days"])),
                html.escape(str(item["evidence"])),
            )
        )
    unresolved_table = (
        "<table><thead><tr><th>日期</th><th>极性</th><th>类型</th><th>强度</th><th>状态</th><th>停留天数</th><th>证据</th></tr></thead><tbody>{}</tbody></table>".format("".join(rows))
        if rows
        else '<p class="empty">没有未闭环事件。</p>'
    )
    kind_rows = "".join(
        "<tr><td>{}</td><td>{}</td></tr>".format(html.escape(kind), count)
        for kind, count in list(stats["by_kind"].items())[:12]
    )
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ margin: 0; padding: 40px 24px 64px; background: #f7f7f5; color: #23262b;
    font-family: -apple-system, "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif; }}
  main {{ max-width: 880px; margin: 0 auto; }}
  h1 {{ font-size: 26px; margin: 0 0 6px; }}
  .meta {{ color: #767b83; font-size: 13px; margin-bottom: 28px; }}
  .cards {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 28px; }}
  .card {{ background: #fff; border: 1px solid #e4e4e0; border-radius: 12px; padding: 16px; }}
  .card .label {{ font-size: 12px; color: #767b83; }}
  .card .value {{ font-size: 24px; font-weight: 600; margin-top: 6px; }}
  section {{ background: #fff; border: 1px solid #e4e4e0; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
  h2 {{ font-size: 16px; margin: 0 0 14px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid #eee; vertical-align: top; }}
  th {{ color: #767b83; font-weight: 500; }}
  .legend {{ display: flex; gap: 16px; font-size: 12px; color: #5b616e; margin-top: 8px; }}
  .legend i {{ display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; }}
  .empty {{ color: #767b83; font-size: 13px; }}
  footer {{ color: #767b83; font-size: 12px; margin-top: 8px; }}
</style>
</head>
<body>
<main>
  <h1>{title}</h1>
  <div class="meta">生成时间 {generated} · 窗口起点 {since}</div>
  <div class="cards">
    <div class="card"><div class="label">反馈事件</div><div class="value">{total}</div></div>
    <div class="card"><div class="label">满意率</div><div class="value">{rate}</div></div>
    <div class="card"><div class="label">未闭环</div><div class="value">{unresolved}</div></div>
    <div class="card"><div class="label">修复时长中位数</div><div class="value">{median}</div></div>
  </div>
  <section>
    <h2>每日趋势</h2>
    {chart}
  </section>
  <section>
    <h2>未闭环清单</h2>
    {unresolved_table}
  </section>
  <section>
    <h2>类型分布</h2>
    <table><thead><tr><th>类型</th><th>次数</th></tr></thead><tbody>{kinds}</tbody></table>
  </section>
  <footer>口径：满意率 = 正向 / 全部；修复时长 = 事件到第一条 verified 的中位数；未闭环按时间从早到晚排列。</footer>
</main>
</body>
</html>
""".format(
        title=html.escape(title),
        generated=html.escape(stats["generated_at"]),
        since=html.escape(stats["window_since"] or "全部历史"),
        total=stats["total"],
        rate=format_rate(stats["satisfaction_rate"]),
        unresolved=stats["unresolved_count"],
        median=format_median(stats["median_time_to_verified_days"]),
        chart=bar_chart(stats),
        unresolved_table=unresolved_table,
        kinds=kind_rows or '<tr><td colspan="2" class="empty">暂无数据</td></tr>',
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", default=None, help="账本目录，默认 ~/.feedback-loop")
    parser.add_argument("--since", default="30d", help="窗口，例如 7d、30d、2026-09-01；all 表示全部")
    parser.add_argument("--out", default=None, help="输出目录，默认 <store>/reports")
    parser.add_argument("--name", default="feedback-report", help="文件名前缀")
    parser.add_argument("--title", default="反馈飞轮 · 满意度复盘", help="报告标题")
    parser.add_argument("--open", action="store_true", help="生成后用后台方式打开 HTML")
    parser.add_argument("--json", action="store_true", help="在标准输出打印 JSON 摘要")
    args = parser.parse_args(argv)

    store = resolve_store(args.store)
    since = None if str(args.since).lower() == "all" else parse_since(args.since)
    stats = compute_stats(load_events(store), load_outcomes(store), since)
    out_dir = Path(args.out).expanduser().resolve() if args.out else store / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")
    base = "{}-{}".format(args.name, stamp)
    md_path = out_dir / (base + ".md")
    html_path = out_dir / (base + ".html")
    json_path = out_dir / (base + ".json")
    md_path.write_text(render_markdown(stats, args.title), encoding="utf-8")
    html_path.write_text(render_html(stats, args.title), encoding="utf-8")
    summary = dict(stats)
    summary["artifacts"] = {
        "markdown": str(md_path),
        "html": str(html_path),
        "json": str(json_path),
        "store": str(store),
    }
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.open:
        os.system('open -g "{}"'.format(html_path))
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("markdown={}".format(md_path))
        print("html={}".format(html_path))
        print("json={}".format(json_path))
        print("total={} unresolved={} satisfaction={}".format(stats["total"], stats["unresolved_count"], format_rate(stats["satisfaction_rate"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
