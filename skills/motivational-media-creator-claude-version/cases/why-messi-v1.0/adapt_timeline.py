"""One-off adapter: why-messi/v10-timeline -> motivational-timeline/v1 (read-only on the project)."""
import json, sys
src, out_tl, out_vtt = sys.argv[1:4]
d = json.load(open(src))
dur = float(d["duration"])
beats = [  # from brief.md 结构与情绪弧线 (estimated section times)
    ("b1", "hook", 0.0, 10.0, "开场：告别夜"), ("b2", "setup", 10.0, 48.0, "天才"),
    ("b3", "setup", 48.0, 62.0, "同一条路线"), ("b4", "wound", 62.0, 104.0, "输"),
    ("b5", "abyss", 104.0, 111.0, "结束了"), ("b6", "turn", 111.0, 167.0, "回来"),
    ("b7", "peak", 167.0, 201.0, "这一次没有"), ("b8", "coda", 201.0, 224.0, "回望"),
    ("b9", "end-card", 224.0, dur, "数据卡与 Logo"),
]
kind = {"s35b": "own-words", "cuatro": "own-words", "retire": "own-words", "arenga": "own-words",
        "unity": "own-words", "vhm": "commentary", "ser": "commentary", "maradona": "dialogue"}
src_of = {"s35b": "S35b", "cuatro": "S-cuatro", "retire": "S-retire", "arenga": "S30", "unity": "S25",
          "vhm": "S33", "ser": "S34", "maradona": "S-maradona"}
voice = []
for v in d["voices"]:
    if v["id"].startswith("crowd"):
        continue
    k = "narration" if v["id"].startswith("n") and v["id"][1:].isdigit() else kind[v["id"]]
    item = {"id": v["id"], "kind": k, "start": round(v["at"], 3), "end": round(v["until"], 3)}
    if k != "narration":
        item["source"] = src_of[v["id"]]
    voice.append(item)
shots = [{"id": s["id"], "source": s["src"], "start": s["t0"], "end": s["t1"]}
         for s in d["segments"] if s.get("kind") == "shot"]
cue = d["cues"][0]
music = [{"id": cue["id"], "source": "M-song1", "start": cue["at"], "end": round(cue["at"] + cue["dur"], 3)}]
used = sorted({x["source"] for x in shots + voice + music if x.get("source")})
sources = []
for sid in used:
    s = {"id": sid, "verified": True}
    if sid == "M-song1":
        s.update(kind="music", rights="risk-accepted", origin="third-party song, no licence")
    else:
        s.update(kind="third-party-footage", rights="risk-accepted", origin="third-party match/interview footage, no licence")
    sources.append(s)
titles = [{"id": f"t{i+1:02d}", "kind": "end-card" if c.get("style") in ("end", "credit") else "caption",
           "start": c["t0"], "end": c["t1"], "text": c["text"], "over": "picture"} for i, c in enumerate(d["captions"])]
tl = {"schema": "motivational-timeline/v1", "title": "为什么是梅西 v1.0（改写自项目时间线）",
      "archetype": "single-arc", "status": "review", "duration_s": dur,
      "beats": [{"id": i, "role": r, "start": a, "end": b, "note": n} for i, r, a, b, n in beats],
      "voice": voice, "music": music, "shots": shots, "titles": titles, "sources": sources,
      "claims": [], "sensitive": {"suicide_or_self_harm": False}}
json.dump(tl, open(out_tl, "w"), ensure_ascii=False, indent=1)
def ts(x):
    return f"{int(x//3600):02d}:{int(x%3600//60):02d}:{x%60:06.3f}"
with open(out_vtt, "w") as f:
    f.write("WEBVTT\n\n")
    for v in voice:
        f.write(f"{ts(v['start'])} --> {ts(v['end'])}\n[{v['kind']}] {v['id']}\n\n")
print(len(voice), "voices", len(shots), "shots", len(sources), "sources")
