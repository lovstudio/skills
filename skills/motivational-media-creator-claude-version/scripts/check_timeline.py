#!/usr/bin/env python3
"""Check a motivational film timeline before it is rendered.

Validates a motivational-timeline/v1 JSON file against the beat order, voice,
music, rights, claim and safe-messaging rules of this Skill, and against the
rhythm bands of a reference envelope. Prints a JSON report and exits 1 when
any error is found. Standard library only.
"""
import argparse
import json
import sys
from pathlib import Path

ARCHETYPES = {
    "single-arc": {"required": ["hook", "wound", "turn", "peak", "coda"]},
    "chorus": {"required": ["hook", "wound", "climb", "peak", "coda"]},
}
ROLES = {"cold-open", "hook", "title", "setup", "wound", "abyss", "turn", "climb",
         "peak", "echo", "address", "coda", "end-card"}
VOICE_KINDS = {"narration", "own-words", "commentary", "dialogue"}
CLEARED = {"owned", "licensed", "permitted", "public-domain"}
RIGHTS = CLEARED | {"unclear", "risk-accepted"}
STATUSES = {"draft", "review", "publishable"}
BREATH_MIN_S = 2.0
LONG_BREATH_S = 8.0
MUSIC_CROSSFADE_MAX_S = 4.0
VOICE_OVERLAP_TOLERANCE_S = 0.15


class Report:
    def __init__(self):
        self.errors, self.warnings, self.metrics = [], [], {}

    def error(self, code, message):
        self.errors.append({"code": code, "message": message})

    def warn(self, code, message):
        self.warnings.append({"code": code, "message": message})


def span(item):
    return float(item["end"]) - float(item["start"])


def check_times(items, label, duration, report):
    for item in items:
        ident = item.get("id", "?")
        try:
            start, end = float(item["start"]), float(item["end"])
        except (KeyError, TypeError, ValueError):
            report.error("time", f"{label} {ident} needs numeric start and end")
            continue
        if start < 0 or end > duration + 0.05 or end <= start:
            report.error("time", f"{label} {ident} [{start}, {end}] is outside 0..{duration} or empty")


def check_beats(tl, duration, report):
    beats = sorted(tl.get("beats", []), key=lambda b: float(b["start"]))
    if not beats:
        report.error("beats", "timeline has no beats")
        return beats
    for b in beats:
        if b.get("role") not in ROLES:
            report.error("beats", f"beat {b.get('id')} has unknown role {b.get('role')!r}")
    for a, b in zip(beats, beats[1:]):
        gap = float(b["start"]) - float(a["end"])
        if gap < -0.05:
            report.error("beats", f"beats {a.get('id')} and {b.get('id')} overlap")
        elif gap > 1.0:
            report.warn("beats", f"{gap:.1f}s uncovered between {a.get('id')} and {b.get('id')}")
    roles = [b.get("role") for b in beats]
    required = ARCHETYPES[tl["archetype"]]["required"]
    for role in required:
        if role not in roles:
            report.error("beats", f"{tl['archetype']} needs a {role} beat")
    story = [r for r in roles if r not in {"cold-open", "title", "end-card"}]
    if story and story[0] != "hook":
        report.error("order", "the first story beat must be the hook")
    if story and story[-1] != "coda":
        report.error("order", "the last story beat must be the coda")
    if "peak" in roles:
        peak_i = roles.index("peak")
        for role in ("wound", "turn", "climb"):
            if role in roles and roles.index(role) > peak_i:
                report.error("order", f"{role} must come before the peak")
        if "wound" in roles and roles.index("wound") > roles.index("turn" if "turn" in roles else "peak"):
            report.error("order", "the wound must come before the turn")
    if "echo" in roles and "peak" in roles and roles.index("echo") < roles.index("peak"):
        report.warn("order", "an echo usually returns to the peak moment after it, not before")
    return beats


def merged(intervals):
    out = []
    for a, b in sorted(intervals):
        if out and a <= out[-1][1] + 0.05:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def check_voice(tl, duration, sources, claims, report):
    voice = sorted(tl.get("voice", []), key=lambda v: float(v["start"]))
    for v in voice:
        if v.get("kind") not in VOICE_KINDS:
            report.error("voice", f"voice {v.get('id')} has unknown kind {v.get('kind')!r}")
        if v.get("kind") in {"own-words", "commentary", "dialogue"}:
            src = v.get("source")
            if src not in sources:
                report.error("voice", f"voice {v.get('id')} is recorded speech but source {src!r} is not in sources")
            elif not sources[src].get("verified"):
                report.warn("voice", f"voice {v.get('id')} uses source {src} that is not verified against the original")
        for cid in v.get("claims", []):
            claim = claims.get(cid)
            if claim is None:
                report.error("claims", f"voice {v.get('id')} cites unknown claim {cid}")
            elif claim.get("status") == "disputed":
                report.error("claims", f"voice {v.get('id')} states disputed claim {cid}")
            elif claim.get("status") == "single-source":
                report.warn("claims", f"voice {v.get('id')} states single-source claim {cid}; soften the wording")
    latest = None  # the voice item that ends last so far, so nested items are caught too
    for b in voice:
        a = latest
        if a is None or float(b["end"]) > float(a["end"]):
            latest = b
        if a is None:
            continue
        overlap = min(float(a["end"]), float(b["end"])) - float(b["start"])
        if overlap <= VOICE_OVERLAP_TOLERANCE_S:
            continue
        if "narration" in (a.get("kind"), b.get("kind")):
            report.error("voice", f"voice {a.get('id')} and {b.get('id')} overlap {overlap:.2f}s; never stack narration on recorded speech")
        else:
            report.warn("voice", f"recorded voices {a.get('id')} and {b.get('id')} overlap {overlap:.2f}s; keep it a crossfade")
    spans = merged([(float(v["start"]), float(v["end"])) for v in voice])
    covered = sum(b - a for a, b in spans)
    edges = [0.0] + [x for s in spans for x in s] + [duration]
    breaths = [(edges[k], edges[k + 1] - edges[k]) for k in range(0, len(edges), 2)
               if edges[k + 1] - edges[k] >= BREATH_MIN_S]
    report.metrics.update({
        "speech.coverage": round(covered / duration, 3) if duration else None,
        "speech.coda_s": round(duration - spans[-1][1], 2) if spans else None,
        "speech.long_breaths": sum(1 for _, g in breaths if g >= LONG_BREATH_S),
        "breathing_windows": [{"start": round(a, 2), "length": round(g, 2)} for a, g in breaths],
    })
    return breaths


def check_music(tl, sources, report):
    music = sorted(tl.get("music", []), key=lambda m: float(m["start"]))
    seen = {}
    for m in music:
        src = m.get("source")
        if src not in sources:
            report.error("music", f"music {m.get('id')} source {src!r} is not in sources")
        seen.setdefault(src, []).append(m.get("id"))
    for src, ids in seen.items():
        if len(ids) > 1:
            report.error("music", f"music source {src} is mounted {len(ids)} times ({', '.join(map(str, ids))}); build one continuous bed")
    if len(seen) > 2:
        report.warn("music", f"{len(seen)} music sources; the references change songs at most once")
    for a, b in zip(music, music[1:]):
        overlap = float(a["end"]) - float(b["start"])
        if overlap > MUSIC_CROSSFADE_MAX_S:
            report.error("music", f"music {a.get('id')} and {b.get('id')} overlap {overlap:.1f}s; crossfade at most {MUSIC_CROSSFADE_MAX_S}s")
    report.metrics["music.sources"] = len(seen)


def check_titles(tl, forbid_black, report):
    for t in tl.get("titles", []):
        if t.get("over") == "black" and t.get("kind") not in {"end-card"}:
            msg = f"title {t.get('id')} sits on black ({span(t):.1f}s)"
            if forbid_black:
                report.error("titles", msg + "; this profile forbids black text cards, put it over picture")
            elif span(t) > 4.0:
                report.warn("titles", msg + "; long black cards stop the film")


def check_rights(tl, sources, report):
    status = tl.get("status", "draft")
    if status not in STATUSES:
        report.error("status", f"unknown status {status!r}")
    uncleared = []
    for sid, s in sources.items():
        if s.get("rights") not in RIGHTS:
            report.error("rights", f"source {sid} has unknown rights value {s.get('rights')!r}")
        elif s.get("rights") not in CLEARED:
            uncleared.append(sid)
    used = {x.get("source") for key in ("shots", "voice", "music") for x in tl.get(key, []) if x.get("source")}
    for sid in sorted(used - set(sources)):
        report.error("rights", f"{sid} is used on the timeline but missing from sources")
    for sid in sorted(set(sources) - used):
        report.warn("rights", f"source {sid} is listed but unused")
    if uncleared and status == "publishable":
        report.error("rights", "publishable needs every source cleared; uncleared: " + ", ".join(sorted(uncleared)))
    elif uncleared:
        report.warn("rights", "review-only: uncleared sources " + ", ".join(sorted(uncleared)))
    report.metrics["rights.uncleared"] = sorted(uncleared)


def check_sensitive(tl, report):
    sens = tl.get("sensitive") or {}
    if sens.get("suicide_or_self_harm"):
        if not sens.get("safe_messaging_reviewed"):
            report.error("sensitive", "story touches suicide or self-harm; run the safe-messaging review first")
        if not sens.get("help_card"):
            report.error("sensitive", "story touches suicide or self-harm; add a help card with a local support line")


def check_bands(tl, beats, envelope, report):
    duration = float(tl["duration_s"])
    peak = next((b for b in beats if b.get("role") == "peak"), None)
    if peak:
        report.metrics["arc.peak_position"] = round((float(peak["start"]) + float(peak["end"])) / 2 / duration, 3)
    shots = tl.get("shots", [])
    if shots:
        lengths = sorted(span(s) for s in shots)
        report.metrics["shots.median_s"] = round(lengths[len(lengths) // 2], 2)
    report.metrics["duration_s"] = duration
    if not envelope:
        return
    bands = envelope["archetypes"].get(tl["archetype"], {}).get("bands", {})
    for key, value in report.metrics.items():
        band = bands.get(key)
        if band is None or value is None or isinstance(value, (list, dict)):
            continue
        if not band["min"] <= value <= band["max"]:
            report.warn("rhythm", f"{key}={value} is outside the reference band {band['min']}..{band['max']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("timeline", help="motivational-timeline/v1 JSON file")
    parser.add_argument("--envelope", help="Reference envelope JSON (assets/reference-envelope.json)")
    parser.add_argument("--forbid-black-cards", action="store_true",
                        help="Treat text cards over black as errors (profile preference)")
    parser.add_argument("--out", help="Write the report JSON here as well as stdout")
    args = parser.parse_args()

    tl = json.loads(Path(args.timeline).read_text(encoding="utf-8"))
    report = Report()
    if tl.get("schema") != "motivational-timeline/v1":
        report.error("schema", "schema must be motivational-timeline/v1")
    if tl.get("archetype") not in ARCHETYPES:
        report.error("schema", f"archetype must be one of {sorted(ARCHETYPES)}")
    try:
        duration = float(tl["duration_s"])
    except (KeyError, TypeError, ValueError):
        report.error("schema", "duration_s is required")
        duration = 0.0
    if report.errors:
        print(json.dumps({"valid": False, "errors": report.errors}, ensure_ascii=False, indent=2))
        return 1

    sources = {s["id"]: s for s in tl.get("sources", [])}
    claims = {c["id"]: c for c in tl.get("claims", [])}
    for key in ("beats", "voice", "music", "shots", "titles"):
        check_times(tl.get(key, []), key, duration, report)
    if report.errors:
        print(json.dumps({"valid": False, "errors": report.errors}, ensure_ascii=False, indent=2))
        return 1
    beats = check_beats(tl, duration, report)
    check_voice(tl, duration, sources, claims, report)
    check_music(tl, sources, report)
    check_titles(tl, args.forbid_black_cards, report)
    check_rights(tl, sources, report)
    check_sensitive(tl, report)
    envelope = json.loads(Path(args.envelope).read_text(encoding="utf-8")) if args.envelope else None
    check_bands(tl, beats, envelope, report)

    result = {
        "valid": not report.errors,
        "status": tl.get("status", "draft"),
        "archetype": tl["archetype"],
        "errors": report.errors,
        "warnings": report.warnings,
        "metrics": report.metrics,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
