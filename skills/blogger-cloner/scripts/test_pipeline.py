#!/usr/bin/env python3
"""End-to-end regression for cloner.py and stylometry.py on a synthetic corpus.

Run: python3 -I scripts/test_pipeline.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLONER = HERE / "cloner.py"
STYLO = HERE / "stylometry.py"
DIMS = ["voice", "structure", "argument", "rhythm", "lexicon", "rhetoric", "layout", "packaging"]

PARAS = [
    "昨天，新的模型正式上线了。",
    "说实话，我第一时间就去试了一下，感觉非常的快。",
    "这玩意翻译成人话就是，一个能帮你自动整理资料的助手。",
    "我自己在团队里用了一周，发现它最适合处理那些又碎又急的小活儿，比如会议纪要、周报和资料汇总啥的。",
    "原因很简单，三个字。",
    "省时间。",
    "当然，它也有缺点，遇到很长的文档时偶尔会漏掉一些细节，需要自己再过一眼。",
    "就像以前大家刚开始用搜索引擎一样，工具本身不难，难的是改掉旧习惯。",
    "所以我的建议是，先找一个最小的场景试起来。",
]


def article(i: int, title: str) -> str:
    body = "\n\n".join(f"{p}这是第{i}篇里的第{n}段补充说明，用来让篇幅足够长。" if n % 3 == 0 else p
                       for n, p in enumerate(PARAS * 4))
    tail = "以上，如果觉得有用，点个赞再走吧，我们下次见。"
    return f"---\nid: art{i}\ntitle: \"{title}\"\ndate: 2026-05-{i + 10:02d}\n---\n\n{body}\n\n{tail}\n"


def run(*args, expect_ok=True):
    proc = subprocess.run([sys.executable, "-I", str(CLONER), *map(str, args)], capture_output=True, text=True)
    out = json.loads(proc.stdout) if proc.stdout.strip().startswith("{") else {"raw": proc.stdout}
    if expect_ok and proc.returncode != 0:
        raise AssertionError(f"{args[0]} failed: {proc.stdout}{proc.stderr}")
    if not expect_ok and proc.returncode == 0:
        raise AssertionError(f"{args[0]} should have failed: {proc.stdout}")
    return out


def audit(pack: Path, draft: Path):
    proc = subprocess.run([sys.executable, "-I", str(STYLO), "audit", "--pack", str(pack), "--draft", str(draft)],
                          capture_output=True, text=True)
    return proc.returncode, json.loads(proc.stdout)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        corpus, base = tmp / "corpus", tmp / "baseline"
        corpus.mkdir()
        base.mkdir()
        for i in range(6):
            (corpus / f"a{i}.md").write_text(article(i, f"第{i}篇，所有人都该试试这个AI工具了。"), encoding="utf-8")
        for i in range(2):
            (base / f"b{i}.md").write_text("---\nid: base%d\ntitle: \"基线\"\n---\n\n" % i
                                           + "\n\n".join(["行业动态持续更新，相关企业发布了新的产品与服务。"] * 30), encoding="utf-8")
        root = tmp / "projects"
        root.mkdir()
        run("init", "--slug", "demo", "--creator", "示例博主", "--platform", "markdown", "--root", root)
        proj = root / "demo"
        run("ingest", "--project", proj, "--source", "files", "--path", corpus, "--platform", "markdown")
        run("ingest", "--project", proj, "--source", "files", "--path", base, "--role", "baseline", "--label", "基线号")
        cands = run("candidates", "--project", proj)["data"]
        assert cands["total"] == 6, cands
        run("select", "--project", proj, "--holdout", "art5")
        run("show", "--project", proj, "--id", "art5", expect_ok=False)  # split not frozen yet
        run("freeze-split", "--project", proj)
        sealed = run("show", "--project", proj, "--id", "art5", expect_ok=False)
        assert "sealed" in sealed["error"], sealed
        run("metrics", "--project", proj)

        def rule(dim, sid="art0", q="说实话，我第一时间就去试了一下"):
            return {"id": f"{dim}.r", "dimension": dim, "observation": "观察", "instruction": "写法", "scope": "全部",
                    "strength": "preferred", "confidence": "medium", "eligible_sample_count": 5,
                    "evidence": [{"kind": "quote", "sample_id": sid, "q": q, "block": 1},
                                 {"kind": "measurement", "field": "distributions.one_sentence_para_ratio", "note": "n"}]}

        draft = {"schema": "blogger-cloner-draft/v1", "style_id": "lov-demo-style-writer", "display_name": "示例风格写作",
                 "version": "0.1.0", "essence": "示例", "dimensions": [{"id": d, "summary": "摘要"} for d in DIMS],
                 "rules": [rule(d) for d in DIMS],
                 "brand": {"identity_tokens": ["示例博主"]}, "guardrails": ["不冒充"]}
        draft["rules"][0] = rule("voice", sid="art5")
        dpath = proj / "research" / "rules-draft.json"
        dpath.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")
        pack = proj / "style-pack" / "demo-v0.1"
        run("build", "--project", proj, "--draft", dpath, "--out", pack, expect_ok=False)
        report = json.loads(dpath.with_suffix(".build-report.json").read_text(encoding="utf-8"))
        assert any("holdout" in e for e in report["errors"]), report
        draft["rules"][0] = rule("voice", q="根本不存在的句子片段")
        dpath.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")
        run("build", "--project", proj, "--draft", dpath, "--out", pack, expect_ok=False)
        report = json.loads(dpath.with_suffix(".build-report.json").read_text(encoding="utf-8"))
        assert any("nearest" in e for e in report["errors"]), report
        draft["rules"][0] = rule("voice")
        dpath.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")
        run("build", "--project", proj, "--draft", dpath, "--out", pack)
        run("verify", "--project", proj, "--pack", pack)
        run("freeze", "--project", proj, "--pack", pack)
        run("build", "--project", proj, "--draft", dpath, "--out", pack, expect_ok=False)

        run("holdout-brief", "--project", proj, "--pack", pack)
        trial = tmp / "trial.md"
        trial.write_text("---\ntitle: \"试稿\"\n---\n\n今天，我想聊一个很小的变化。\n\n它让很多人的工作方式悄悄变了。\n", encoding="utf-8")
        row = run("trial-register", "--project", proj, "--pack", pack, "--holdout", "art5", "--draft", trial)["data"]
        assert row["blind"] is True, row
        run("holdout-check", "--project", proj, "--pack", pack, expect_ok=False)  # still sealed
        run("holdout-open", "--project", proj, "--pack", pack)
        notes = {"items": {f"{d}.r": {"art5": ["hit", [["说实话，我第一时间就去试了一下", 1]], ""]} for d in DIMS}}
        npath = proj / "research" / "holdout-annotations.json"
        npath.write_text(json.dumps(notes, ensure_ascii=False), encoding="utf-8")
        run("holdout-fill", "--project", proj, "--pack", pack, "--annotations", npath)
        check = run("holdout-check", "--project", proj, "--pack", pack, "--write-summary")["data"]
        assert check["summary"]["coverage"] == 1.0 and check["summary"]["independent_hits"] == 8, check["summary"]

        copied = tmp / "copied.md"
        copied.write_text("---\ntitle: \"抄\"\n---\n\n" + PARAS[3] + "\n", encoding="utf-8")
        code, res = audit(pack, copied)
        assert code == 2 and res["overlap"]["runs"], res["overlap"]
        named = tmp / "named.md"
        named.write_text("---\ntitle: \"冒充\"\n---\n\n大家好，我是示例博主，今天聊聊新工具。\n", encoding="utf-8")
        code, res = audit(pack, named)
        assert code == 2 and res["identity_hits"] == ["示例博主"], res

        target = tmp / "demo-style-writer-skill"
        (target / "scripts").mkdir(parents=True)
        (target / "skill.yaml").write_text("schema: skill-manifest/v1\nid: lov-demo-style-writer\n", encoding="utf-8")
        run("package", "--project", proj, "--pack", pack, "--into", target, "--english-name", "Demo Writer",
            "--description", "示例描述")
        packaged = json.loads((target / "assets" / "style-pack" / "metrics.train.json").read_text(encoding="utf-8"))
        assert all("key" not in r and "key_sha1" in r for r in packaged["boilerplate"]), packaged["boilerplate"]
        assert (target / "assets" / "style-pack" / "PACKAGED.json").is_file()
        code, res = audit(target / "assets" / "style-pack", trial)
        assert code == 0, res

        raw = proj / "research" / "corpus" / "raw" / "art0.md"
        raw.write_text(raw.read_text(encoding="utf-8") + "\n篡改。\n", encoding="utf-8")
        tampered = run("metrics", "--project", proj, expect_ok=False)
        assert "changed" in tampered["error"], tampered
    print("test_pipeline: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
