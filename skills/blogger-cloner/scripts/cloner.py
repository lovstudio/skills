#!/usr/bin/env python3
"""Blogger cloner pipeline: corpus -> frozen split -> evidence-backed style pack -> holdout -> package.

Every command prints JSON (except `show`, which prints numbered blocks for reading)
and exits non-zero on failure. Standard library only; Python 3.9+.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import random
import re
import shutil
import sys
import tempfile
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stylometry as sm  # noqa: E402

TOOL_VERSION = "0.1.0"
SKILL_ROOT = Path(__file__).resolve().parent.parent
DIMENSIONS = ["voice", "structure", "argument", "rhythm", "lexicon", "rhetoric", "layout", "packaging"]
DIMENSION_LABELS = {
    "voice": "叙事视角与人设", "structure": "篇章结构", "argument": "论证方式", "rhythm": "句式与节奏",
    "lexicon": "词汇与口头禅", "rhetoric": "修辞与情绪", "layout": "版式与公众号元素", "packaging": "标题、选题与品牌位",
}
STRENGTHS = {"required", "preferred", "optional"}
CONFIDENCE = {"high", "medium", "low"}
RESULTS = {"hit", "partial", "miss", "not_applicable"}
TRIAL_LABELS = {"pack", "control"}
QUOTE_MIN, QUOTE_MAX = 4, 60
LISTING_RE = re.compile(r"一览|合集|目录|周报|月报|招聘|抽奖|福利|直播预告|活动报名|勘误|声明")
SLUG_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,40}")
METRIC_LABELS = {
    "units_total": "篇幅（字词单位）", "title_units": "标题长度", "para_units_median": "段落长度中位",
    "para_units_p90": "长段落（P90）", "one_sentence_para_ratio": "一句成段占比", "short_para_ratio": "短段（≤20）占比",
    "sent_units_median": "句长中位", "sent_units_p90": "长句（P90）", "short_sent_ratio": "短句（≤8）占比",
    "long_sent_ratio": "长句（≥35）占比", "question_sent_ratio": "问句占比", "exclaim_sent_ratio": "感叹句占比",
    "punct_comma_per1k": "逗号/千字", "punct_period_per1k": "句号/千字", "punct_exclaim_per1k": "感叹号/千字",
    "punct_question_per1k": "问号/千字", "punct_ellipsis_per1k": "省略号/千字", "punct_dots_per1k": "连续句号“。。”/千字", "punct_dash_per1k": "破折号/千字",
    "punct_colon_per1k": "冒号/千字", "punct_quote_per1k": "引号/千字", "pron_wo_per1k": "“我”/千字",
    "pron_women_per1k": "“我们”/千字", "pron_ni_per1k": "“你/您”/千字", "pron_dajia_per1k": "“大家”/千字",
    "latin_per1k": "英文词/千字", "digit_per1k": "数字/千字", "bold_per1k": "加粗/千字", "images_per1k": "配图/千字",
    "headings_per1k": "小标题/千字", "list_block_ratio": "列表段占比",
}


class CliError(Exception):
    pass


# ---------------------------------------------------------------- io helpers

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise CliError(f"missing file: {path}")
    except json.JSONDecodeError as exc:
        raise CliError(f"invalid JSON in {path}: {exc}")


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    os.replace(tmp, path)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def digest_obj(obj) -> str:
    return sha256_bytes(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8"))


def sanitize_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-")[:48]


# ---------------------------------------------------------------- project model

class Project:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.file = self.root / "project.json"
        if not self.file.is_file():
            raise CliError(f"not a blogger-cloner project (no project.json): {self.root}")
        self.data = load_json(self.file)
        self.research = self.root / "research"

    def save(self) -> None:
        write_json(self.file, self.data)

    def mark(self, state: str) -> None:
        self.data.setdefault("states", {})[state] = now()
        self.save()

    def has(self, state: str) -> bool:
        return state in self.data.get("states", {})

    @property
    def index_path(self) -> Path:
        return self.research / "corpus" / "index.json"

    @property
    def sources_path(self) -> Path:
        return self.research / "sources.json"

    def index(self, role: str = "sample") -> dict:
        path = self.index_path if role == "sample" else self.research / "baseline" / "index.json"
        if not path.is_file():
            return {"schema": "blogger-cloner-corpus/v1", "role": role, "items": []}
        return load_json(path)

    def sources(self) -> dict:
        return load_json(self.sources_path)

    def require_split(self) -> dict:
        src = self.sources()
        if not src.get("split_frozen_at"):
            raise CliError("split is not frozen; run freeze-split first")
        for item in src["items"]:
            path = self.research / item["path"]
            if not path.is_file() or sha256_file(path) != item["sha256"]:
                raise CliError(f"sample changed after the split was frozen: {item['sample_id']}; start a new project version")
        if split_digest(src["items"]) != src["split_digest"]:
            raise CliError("sources.json partitions changed after freezing")
        return src

    def holdout_open(self) -> bool:
        return bool(self.data.get("holdout_opened_at"))


def split_digest(items: list[dict]) -> str:
    return digest_obj(sorted((i["sample_id"], i["partition"], i["sha256"]) for i in items))


def items_by(src: dict, partition: str) -> list[dict]:
    return [i for i in src["items"] if i["partition"] == partition]


def read_item(project: Project, item: dict) -> str:
    return (project.research / item["path"]).read_text(encoding="utf-8")


def guard_readable(project: Project, item: dict) -> None:
    if item["partition"] == "holdout" and not project.holdout_open():
        raise CliError(f"{item['sample_id']} is a sealed holdout sample; freeze the pack, register blind trials, then run holdout-open")


# ---------------------------------------------------------------- commands: setup and corpus

def cmd_doctor(args) -> dict:
    checks = {"python": sys.version.split()[0], "python_ok": sys.version_info >= (3, 9),
              "stylometry": (SKILL_ROOT / "scripts" / "stylometry.py").is_file(),
              "writer_templates": (SKILL_ROOT / "assets" / "writer-skill").is_dir()}
    if args.root:
        root = Path(args.root).expanduser()
        checks["root"] = str(root)
        checks["root_writable"] = root.is_dir() and os.access(root, os.W_OK)
    checks["ready"] = all(v for k, v in checks.items() if k.endswith("_ok") or k in ("stylometry", "writer_templates"))
    checks["corpus_sources"] = ["wxmp-export (lov-wxmp-cli export directory)", "files (Markdown/TXT directory)"]
    return checks


def cmd_init(args) -> dict:
    if not SLUG_RE.fullmatch(args.slug):
        raise CliError("slug must be lowercase ASCII letters, digits or hyphens")
    root = Path(args.root).expanduser().resolve() / args.slug
    if (root / "project.json").exists():
        raise CliError(f"project already exists: {root}")
    for sub in ("research/corpus/raw", "research/baseline/raw", "research/brand", "research/metrics",
                "style-pack", "trials", "deliverables"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    data = {"schema": "blogger-cloner-project/v1", "slug": args.slug, "creator": args.creator,
            "platform": args.platform, "profile_url": args.profile_url or "", "created_at": now(),
            "tool_version": TOOL_VERSION, "states": {}, "trials": []}
    write_json(root / "project.json", data)
    return {"project": str(root), "next": "ingest the creator's articles"}


def _front_matter(meta: dict) -> str:
    lines = ["---"]
    for key in ("title", "date", "link", "digest", "author"):
        value = str(meta.get(key) or "").replace("\n", " ").replace('"', "'")
        lines.append(f'{key}: "{value}"')
    lines.append("---\n")
    return "\n".join(lines)


def _ingest_wxmp(path: Path) -> tuple[list[dict], dict]:
    manifest = path / "manifest.json"
    if manifest.is_file() and load_json(manifest).get("schema") != "lov-wxmp-export/v1":
        raise CliError("unrecognized export manifest; expected lov-wxmp-export/v1")
    index = load_json(path / "index.json")
    docs = []
    for a in index.get("articles", []):
        created = a.get("create_time")
        date = dt.datetime.fromtimestamp(created).date().isoformat() if created else ""
        docs.append({"sample_id": sanitize_id(str(a.get("aid") or "")) or f"doc-{sha256_bytes(a['title'].encode())[:10]}",
                     "title": a.get("title") or "", "date": date, "link": a.get("link") or "",
                     "digest": a.get("digest") or "", "author": a.get("author") or "",
                     "copyright_type": a.get("copyright_type"), "article_type": a.get("article_type"),
                     "body": a.get("content_md") or ""})
    account = index.get("account") or {}
    account = {k: account.get(k) for k in ("nickname", "alias", "signature", "round_head_img") if account.get(k)}
    return docs, account


def _ingest_files(path: Path) -> list[dict]:
    docs = []
    for f in sorted(p for p in path.rglob("*") if p.suffix.lower() in (".md", ".markdown", ".txt") and p.is_file()):
        raw = f.read_text(encoding="utf-8", errors="replace")
        meta, body = sm.strip_front_matter(raw)
        title = meta.get("title") or next((b["text"] for b in sm.parse_markdown(body) if b["kind"] == "heading"), "") or f.stem
        sid = sanitize_id(meta.get("id", "")) or f"doc-{sha256_bytes(raw.encode())[:10]}"
        docs.append({"sample_id": sid, "title": title, "date": meta.get("date", ""),
                     "link": meta.get("link") or meta.get("url", ""), "digest": meta.get("digest", ""),
                     "author": meta.get("author", ""), "copyright_type": None, "article_type": None, "body": body})
    return docs


def cmd_ingest(args) -> dict:
    project = Project(Path(args.project))
    role = args.role
    if role == "sample" and project.sources_path.is_file() and project.sources().get("split_frozen_at"):
        raise CliError("split already frozen; new samples need a new project version")
    src = Path(args.path).expanduser().resolve()
    if not src.is_dir():
        raise CliError(f"not a directory: {src}")
    account = {}
    if args.source == "wxmp-export":
        docs, account = _ingest_wxmp(src)
    else:
        docs = _ingest_files(src)
    base = project.research / ("corpus" if role == "sample" else "baseline")
    index = project.index(role)
    known = {i["sample_id"]: i for i in index["items"]}
    added = skipped = missing = 0
    for d in docs:
        body = d.pop("body").strip()
        has_body = sm.units(body) >= 200
        entry = {**d, "platform": args.platform, "label": args.label or project.data["creator"],
                 "has_body": has_body, "units": sm.units(body), "path": None, "sha256": None}
        if has_body:
            rel = f"{'corpus' if role == 'sample' else 'baseline'}/raw/{d['sample_id']}.md"
            content = _front_matter(d) + body + "\n"
            target = project.research / rel
            if target.is_file() and target.read_text(encoding="utf-8") == content:
                skipped += 1
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                added += 1
            entry["path"], entry["sha256"] = rel, sha256_bytes(content.encode("utf-8"))
        else:
            missing += 1
        known[d["sample_id"]] = entry
    index["items"] = sorted(known.values(), key=lambda i: i.get("date") or "", reverse=True)
    index["updated_at"] = now()
    write_json(base / "index.json", index)
    if role == "sample" and account:
        write_json(project.research / "brand" / "account.json", {**account, "platform": args.platform})
    if role == "sample":
        project.mark("ingested")
    return {"role": role, "articles": len(docs), "written": added, "unchanged": skipped,
            "without_body": missing, "index": str(base / "index.json"), "account": account or None}


def cmd_candidates(args) -> dict:
    project = Project(Path(args.project))
    rows = []
    for i in project.index()["items"]:
        flags = []
        if not i["has_body"]:
            flags.append("no_body")
        elif i["units"] < 600:
            flags.append("short")
        if LISTING_RE.search(i["title"]):
            flags.append("listing_or_notice")
        if i.get("author") and i["author"] not in (project.data["creator"],):
            flags.append(f"author:{i['author']}")
        rows.append({"sample_id": i["sample_id"], "date": i["date"], "title": i["title"],
                     "units": i["units"], "flags": flags})
    write_json(project.research / "candidates.json", {"schema": "blogger-cloner-candidates/v1",
                                                      "generated_at": now(), "items": rows})
    eligible = [r for r in rows if not r["flags"]]
    return {"total": len(rows), "eligible_without_flags": len(eligible), "items": rows}


def cmd_select(args) -> dict:
    project = Project(Path(args.project))
    if project.sources_path.is_file() and project.sources().get("split_frozen_at"):
        raise CliError("split already frozen")
    items = {i["sample_id"]: i for i in project.index()["items"]}
    exclude = set(filter(None, (args.exclude or "").split(",")))
    unknown = [s for s in exclude if s not in items]
    if unknown:
        raise CliError(f"unknown sample ids in --exclude: {unknown}")
    pool = [i for i in items.values() if i["has_body"] and i["sample_id"] not in exclude
            and (not args.era_from or i["date"] >= args.era_from) and (not args.era_to or i["date"] <= args.era_to)]
    pool.sort(key=lambda i: i["date"])
    if args.holdout:
        holdout = [s.strip() for s in args.holdout.split(",") if s.strip()]
        bad = [s for s in holdout if s not in {i["sample_id"] for i in pool}]
        if bad:
            raise CliError(f"holdout ids not in the eligible pool: {bad}")
        method = "explicit holdout ids"
    else:
        k = args.holdout_count
        if k < 1 or k >= len(pool):
            raise CliError("--holdout-count must leave at least one holdout and three training samples")
        holdout = [pool[min(len(pool) - 1, int((n + 0.5) * len(pool) / k))]["sample_id"] for n in range(k)]
        method = f"{k} holdout(s) evenly spaced by publish date"
    train = [i for i in pool if i["sample_id"] not in holdout]
    if len(train) < 3 or not holdout:
        raise CliError("need at least three training samples and one holdout sample")
    chosen = []
    for i in pool:
        chosen.append({"sample_id": i["sample_id"], "title": i["title"], "date": i["date"], "link": i["link"],
                       "path": i["path"], "sha256": i["sha256"], "units": i["units"],
                       "partition": "holdout" if i["sample_id"] in holdout else "train"})
    dates = [i["date"] for i in pool if i["date"]]
    sources = {"schema": "blogger-cloner-sources/v1", "creator": project.data["creator"],
               "platform": project.data["platform"],
               "era_scope": {"from": args.era_from or (min(dates) if dates else ""),
                             "to": args.era_to or (max(dates) if dates else ""),
                             "note": args.era_note or "latest cached period"},
               "selection": {"method": method, "note": args.note or "", "excluded": sorted(exclude),
                             "selected_at": now()},
               "items": chosen}
    write_json(project.sources_path, sources)
    project.mark("sampled")
    return {"train": len(train), "holdout": len(holdout), "holdout_ids": holdout,
            "sources": str(project.sources_path), "next": "freeze-split before reading any article"}


def cmd_freeze_split(args) -> dict:
    project = Project(Path(args.project))
    src = project.sources()
    if src.get("split_frozen_at"):
        raise CliError("split already frozen")
    for item in src["items"]:
        actual = sha256_file(project.research / item["path"])
        if actual != item["sha256"]:
            raise CliError(f"file changed since ingest: {item['sample_id']}")
    src["split_frozen_at"] = now()
    src["split_digest"] = split_digest(src["items"])
    write_json(project.sources_path, src)
    project.mark("split_frozen")
    return {"split_digest": src["split_digest"], "train": len(items_by(src, "train")),
            "holdout": len(items_by(src, "holdout"))}


# ---------------------------------------------------------------- commands: measurement and reading

def _texts(md: str) -> list[str]:
    return [b["text"] for b in sm.text_blocks(sm.parse_markdown(md))]


def cmd_metrics(args) -> dict:
    project = Project(Path(args.project))
    src = project.require_split()
    train = items_by(src, "train")
    blocks = {i["sample_id"]: sm.parse_markdown(read_item(project, i)) for i in train}
    repeated = sm.boilerplate(blocks)
    repeated_keys = {r["key"] for r in repeated}
    per_doc = {i["sample_id"]: sm.doc_metrics(read_item(project, i), i["title"], repeated_keys) for i in train}
    # Sign-offs and CTAs are reported as boilerplate, not as voice phrases.
    texts = {sid: [b["text"] for b in sm.text_blocks(bl) if sm.match_key(b["text"]) not in repeated_keys]
             for sid, bl in blocks.items()}
    baseline_docs = None
    base_index = project.index("baseline")
    base_items = [i for i in base_index["items"] if i["has_body"]]
    if base_items:
        baseline_docs = [_texts((project.research / i["path"]).read_text(encoding="utf-8")) for i in base_items]
    data = {"schema": "blogger-cloner-train-metrics/v1", "generated_at": now(), "partition": "train",
            "split_digest": src["split_digest"], "n": len(train),
            "units": "units = CJK characters + Latin/digit tokens; per1k = per 1000 units",
            "distributions": sm.distributions(per_doc), "per_doc": per_doc,
            "signature_ngrams": sm.signature_ngrams(texts, baseline_docs),
            "boilerplate": repeated,
            "baseline": {"docs": len(base_items), "labels": sorted({i["label"] for i in base_items})}}
    out = project.research / "metrics" / "train.json"
    write_json(out, data)
    project.mark("measured")
    sig = data["signature_ngrams"]
    top = [r["gram"] for r in (sig.get("distinctive") or sig["frequent"])[:15]]
    return {"metrics": str(out), "n_train": len(train), "baseline_docs": len(base_items),
            "top_signature": top, "boilerplate_blocks": len(data["boilerplate"])}


def cmd_show(args) -> int:
    project = Project(Path(args.project))
    src = project.require_split()
    if args.list:
        for item in src["items"]:
            sealed = item["partition"] == "holdout" and not project.holdout_open()
            print(f"{item['sample_id']}\t{item['partition']}{' (sealed)' if sealed else ''}\t{item['date']}\t{item['units']}\t{item['title']}")
        return 0
    item = next((i for i in src["items"] if i["sample_id"] == args.id), None)
    if not item:
        raise CliError(f"unknown sample id: {args.id}")
    guard_readable(project, item)
    blocks = sm.parse_markdown(read_item(project, item))
    print(f"# {item['title']}  [{item['sample_id']} | {item['partition']} | {item['date']}]")
    for b in blocks[args.start:args.end]:
        text = b["text"] if b["kind"] != "image" else "<image>"
        tag = b["kind"] + (str(b["level"]) if b["kind"] == "heading" else "") + ("*" if b["bold_line"] else "")
        print(f"[{b['i']}|{tag}] {text}")
    return 0


# ---------------------------------------------------------------- build / verify / freeze

def locate_quote(q: str, blocks: list[dict], hint) -> dict:
    qk = sm.match_key(q)
    if len(qk) < QUOTE_MIN:
        return {"error": f"quote too short (<{QUOTE_MIN} characters after normalization): {q}"}
    if len(qk) > QUOTE_MAX:
        return {"error": f"quote too long (>{QUOTE_MAX} characters); cite a shorter fragment: {q[:40]}..."}
    candidates = sm.text_blocks(blocks)
    if isinstance(hint, int):
        candidates = sorted(candidates, key=lambda b: abs(b["i"] - hint))
    for b in candidates:
        key, index = sm.key_with_map(b["text"])
        pos = key.find(qk)
        if pos >= 0:
            start, end = index[pos], index[pos + len(qk) - 1] + 1
            return {"block": b["i"], "quote": b["text"][start:end],
                    "excerpt": b["text"][max(0, start - 30):end + 30]}
    scored = []
    for b in sm.text_blocks(blocks):
        key = sm.match_key(b["text"])
        size = SequenceMatcher(None, qk, key).find_longest_match(0, len(qk), 0, len(key)).size
        scored.append((size, b))
    scored.sort(key=lambda x: -x[0])
    return {"error": f"quote not found: {q}",
            "nearest": [{"block": b["i"], "text": b["text"][:90]} for _, b in scored[:3]]}


def resolve_path(data, dotted: str):
    cur = data
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            raise KeyError(dotted)
    return cur


def validate_draft_shape(draft: dict, errors: list[str]) -> None:
    if draft.get("schema") != "blogger-cloner-draft/v1":
        errors.append("draft.schema must be blogger-cloner-draft/v1")
    for key in ("style_id", "display_name", "version", "essence"):
        if not str(draft.get(key) or "").strip():
            errors.append(f"draft.{key} is required")
    dims = {d.get("id"): d for d in draft.get("dimensions", [])}
    for d in DIMENSIONS:
        if d not in dims or not str(dims[d].get("summary") or "").strip():
            errors.append(f"dimension {d} needs a summary")
    ids = set()
    for r in draft.get("rules", []):
        rid = r.get("id", "?")
        if rid in ids:
            errors.append(f"duplicate rule id {rid}")
        ids.add(rid)
        if r.get("dimension") not in DIMENSIONS:
            errors.append(f"{rid}: dimension must be one of {DIMENSIONS}")
        for key in ("observation", "instruction", "scope"):
            if not str(r.get(key) or "").strip():
                errors.append(f"{rid}: {key} is required")
        if r.get("strength") not in STRENGTHS:
            errors.append(f"{rid}: strength must be one of {sorted(STRENGTHS)}")
        if r.get("confidence") not in CONFIDENCE:
            errors.append(f"{rid}: confidence must be one of {sorted(CONFIDENCE)}")
        if not isinstance(r.get("eligible_sample_count"), int):
            errors.append(f"{rid}: eligible_sample_count must be an integer")
        if not r.get("evidence"):
            errors.append(f"{rid}: at least one evidence item is required")
    covered = {r.get("dimension") for r in draft.get("rules", [])}
    for d in DIMENSIONS:
        if d not in covered:
            errors.append(f"dimension {d} has no rule")
    brand = draft.get("brand") or {}
    if not isinstance(brand.get("identity_tokens", []), list):
        errors.append("brand.identity_tokens must be a list")
    if not draft.get("guardrails"):
        errors.append("guardrails must list what may not transfer (identity, brand, text, opinions)")


def build_evidence(project: Project, src: dict, draft: dict, metrics: dict) -> tuple[list[dict], list[dict], list[str]]:
    train = {i["sample_id"]: i for i in items_by(src, "train")}
    holdout_ids = {i["sample_id"] for i in items_by(src, "holdout")}
    block_cache: dict[str, list[dict]] = {}
    evidence: list[dict] = []
    keyed: dict[str, str] = {}
    errors: list[str] = []
    rules_out = []
    n_train = len(train)
    for rule in draft["rules"]:
        rid = rule["id"]
        ev_ids, samples, measured = [], set(), False
        for raw in rule["evidence"]:
            if "use" in raw:
                eid = keyed.get(raw["use"])
                if not eid:
                    errors.append(f"{rid}: unknown evidence key {raw['use']}")
                    continue
                row = next(e for e in evidence if e["id"] == eid)
                row["rule_ids"].append(rid)
                ev_ids.append(eid)
                if row.get("sample_id"):
                    samples.add(row["sample_id"])
                measured = measured or row["kind"] == "measurement"
                continue
            kind = raw.get("kind")
            sid = raw.get("sample_id")
            row = {"id": f"E{len(evidence) + 1:03d}", "kind": kind, "rule_ids": [rid]}
            if kind in ("quote", "title", "observation"):
                if sid in holdout_ids:
                    errors.append(f"{rid}: evidence cites holdout sample {sid}; holdout stays sealed until after freeze")
                    continue
                if sid not in train:
                    errors.append(f"{rid}: unknown training sample {sid}")
                    continue
                if sid not in block_cache:
                    block_cache[sid] = sm.parse_markdown(read_item(project, train[sid]))
                row["sample_id"] = sid
            if kind == "quote":
                found = locate_quote(raw.get("q", ""), block_cache[sid], raw.get("block"))
                if "error" in found:
                    errors.append(f"{rid}: {found['error']}" + (
                        "; nearest: " + json.dumps(found.get("nearest"), ensure_ascii=False) if found.get("nearest") else ""))
                    continue
                row.update(found)
            elif kind == "title":
                row["quote"] = train[sid]["title"]
            elif kind == "observation":
                span = raw.get("blocks")
                count = len(block_cache[sid])
                if not (isinstance(span, list) and len(span) == 2 and 0 <= span[0] <= span[1] < count):
                    errors.append(f"{rid}: observation blocks must be [start, end] within 0..{count - 1}")
                    continue
                if not str(raw.get("description") or "").strip():
                    errors.append(f"{rid}: observation needs a description")
                    continue
                row.update({"blocks": span, "description": raw["description"]})
            elif kind == "measurement":
                try:
                    value = resolve_path(metrics, raw.get("field", ""))
                except KeyError:
                    errors.append(f"{rid}: measurement field not found in metrics/train.json: {raw.get('field')}")
                    continue
                row.update({"file": "metrics.train.json", "field": raw["field"], "value": value,
                            "note": raw.get("note", "")})
                measured = True
            else:
                errors.append(f"{rid}: unknown evidence kind {kind}")
                continue
            if raw.get("key"):
                keyed[raw["key"]] = row["id"]
            if row.get("sample_id"):
                samples.add(row["sample_id"])
            evidence.append(row)
            ev_ids.append(row["id"])
        eligible = rule.get("eligible_sample_count", 0)
        if samples and not (len(samples) <= eligible <= n_train):
            errors.append(f"{rid}: eligible_sample_count {eligible} must be between support {len(samples)} and {n_train}")
        rules_out.append({**{k: v for k, v in rule.items() if k != "evidence"},
                          "evidence_ids": ev_ids, "support_samples": sorted(samples),
                          "support_count": len(samples), "measured": measured})
    return rules_out, evidence, errors


def cmd_build(args) -> dict:
    project = Project(Path(args.project))
    src = project.require_split()
    metrics_path = project.research / "metrics" / "train.json"
    metrics = load_json(metrics_path)
    if metrics.get("split_digest") != src["split_digest"]:
        raise CliError("metrics/train.json was computed for another split; rerun metrics")
    out = Path(args.out).resolve()
    if (out / "FROZEN.json").exists():
        raise CliError("pack is frozen; build a new version directory instead")
    draft_path = Path(args.draft).resolve()
    draft = load_json(draft_path)
    errors: list[str] = []
    validate_draft_shape(draft, errors)
    rules, evidence, ev_errors = ([], [], []) if errors else build_evidence(project, src, draft, metrics)
    errors += ev_errors
    report = {"schema": "blogger-cloner-build-report/v1", "built_at": now(), "ok": not errors,
              "errors": errors, "rules": len(draft.get("rules", [])), "evidence": len(evidence)}
    write_json(draft_path.with_suffix(".build-report.json"), report)
    if errors:
        raise CliError(f"{len(errors)} build error(s); see {draft_path.with_suffix('.build-report.json')}")
    account = load_json(project.research / "brand" / "account.json") if (project.research / "brand" / "account.json").is_file() else {}
    authors = sorted({i.get("author") for i in project.index()["items"] if i.get("author")})
    tokens = set(draft.get("brand", {}).get("identity_tokens", []))
    tokens.update(t for t in (account.get("nickname"), account.get("alias"), project.data["creator"]) if t)
    tokens.update(authors)
    out.mkdir(parents=True, exist_ok=True)
    holdout = items_by(src, "holdout")
    train = items_by(src, "train")
    profile = {
        "schema": "blogger-cloner-profile/v1", "style_id": draft["style_id"], "display_name": draft["display_name"],
        "version": draft["version"], "creator": project.data["creator"], "platform": project.data["platform"],
        "essence": draft["essence"], "era_scope": src["era_scope"],
        "split": {"train": [i["sample_id"] for i in train], "holdout": [i["sample_id"] for i in holdout],
                  "digest": src["split_digest"]},
        "dimensions": [{"id": d, "label": DIMENSION_LABELS[d],
                        "summary": next(x["summary"] for x in draft["dimensions"] if x["id"] == d)} for d in DIMENSIONS],
        "rules": rules, "templates": draft.get("templates", []), "guardrails": draft["guardrails"],
        "limits": draft.get("limits", []), "unknowns": draft.get("unknowns", []),
        "provenance": {"built_at": now(), "tool_version": TOOL_VERSION, "sources_digest": src["split_digest"],
                       "holdout_opened_before_build": project.holdout_open(),
                       "selection": src["selection"], **draft.get("provenance", {})},
    }
    brand = {"schema": "blogger-cloner-brand/v1", "account": account, "authors": authors,
             "identity_tokens": sorted(t for t in tokens if t),
             "positioning": draft.get("brand", {}).get("positioning", ""),
             "audience": draft.get("brand", {}).get("audience", ""),
             "topics": draft.get("brand", {}).get("topics", []),
             "brand_slots": draft.get("brand", {}).get("brand_slots", []),
             "boilerplate": metrics.get("boilerplate", []),
             "note": "Identity tokens describe the cloned creator; new writing fills brand slots with the user's own brand."}
    corpus_texts = []
    for item in src["items"]:
        corpus_texts.extend(_texts(read_item(project, item)))
    write_json(out / "style-profile.json", profile)
    with (out / "evidence.jsonl").open("w", encoding="utf-8") as fh:
        for row in evidence:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    shutil.copyfile(metrics_path, out / "metrics.train.json")
    write_json(out / "brand.json", brand)
    write_json(out / "corpus-shingles.json", sm.encode_shingles(sm.shingles(corpus_texts)))
    write_json(out / "build-report.json", report)
    project.mark("drafted")
    return {"pack": str(out), "rules": len(rules), "evidence": len(evidence),
            "contaminated": project.holdout_open(), "next": "verify, then freeze"}


PACK_FILES = ["style-profile.json", "evidence.jsonl", "metrics.train.json", "brand.json", "corpus-shingles.json"]


def load_evidence(pack: Path) -> list[dict]:
    return [json.loads(line) for line in (pack / "evidence.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def verify_pack(project: Project, pack: Path) -> dict:
    errors, warnings = [], []
    for name in PACK_FILES:
        if not (pack / name).is_file():
            errors.append(f"missing {name}")
    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings}
    src = project.require_split()
    profile = load_json(pack / "style-profile.json")
    evidence = {e["id"]: e for e in load_evidence(pack)}
    train = {i["sample_id"]: i for i in items_by(src, "train")}
    if profile["split"]["digest"] != src["split_digest"]:
        errors.append("profile split digest differs from sources.json")
    if set(profile["split"]["train"]) & set(profile["split"]["holdout"]):
        errors.append("train and holdout overlap")
    blocks = {}
    for e in evidence.values():
        sid = e.get("sample_id")
        if not sid:
            continue
        if sid not in train:
            errors.append(f"{e['id']}: cites non-training sample {sid}")
            continue
        blocks.setdefault(sid, sm.parse_markdown(read_item(project, train[sid])))
        if e["kind"] == "quote":
            b = next((x for x in blocks[sid] if x["i"] == e["block"]), None)
            if not b or e["quote"] not in b["text"] or e["quote"] not in e["excerpt"]:
                errors.append(f"{e['id']}: quote is not an exact substring of block {e['block']} in {sid}")
        if e["kind"] == "title" and e["quote"] != train[sid]["title"]:
            errors.append(f"{e['id']}: title evidence differs from the registered title")
    dims = {d["id"] for d in profile["dimensions"]}
    for d in DIMENSIONS:
        if d not in dims:
            errors.append(f"missing dimension {d}")
    for r in profile["rules"]:
        samples = {evidence[i]["sample_id"] for i in r["evidence_ids"] if i in evidence and evidence[i].get("sample_id")}
        if len(samples) != r["support_count"]:
            errors.append(f"{r['id']}: support_count does not match its evidence")
        if r["support_count"] and not (r["support_count"] <= r["eligible_sample_count"] <= len(train)):
            errors.append(f"{r['id']}: eligible_sample_count out of range")
        if r["strength"] == "required" and not r["measured"] and r["support_count"] * 2 < r["eligible_sample_count"]:
            warnings.append(f"{r['id']}: required but cited in fewer than half of eligible samples")
    frozen = pack / "FROZEN.json"
    if frozen.is_file():
        record = load_json(frozen)
        for name, digest in record["files"].items():
            if sha256_file(pack / name) != digest:
                errors.append(f"{name} changed after freeze")
    if profile["provenance"].get("holdout_opened_before_build"):
        warnings.append("pack was built after the holdout was opened; holdout results cannot count as independent")
    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "rules": len(profile["rules"]), "evidence": len(evidence), "frozen": frozen.is_file()}


def cmd_verify(args) -> dict:
    project = Project(Path(args.project))
    result = verify_pack(project, Path(args.pack).resolve())
    if result["ok"]:
        project.mark("verified")
    else:
        raise CliError("verify failed: " + "; ".join(result["errors"][:8]))
    return result


def cmd_freeze(args) -> dict:
    project = Project(Path(args.project))
    pack = Path(args.pack).resolve()
    if (pack / "FROZEN.json").exists():
        raise CliError("already frozen")
    result = verify_pack(project, pack)
    if not result["ok"]:
        raise CliError("verify failed: " + "; ".join(result["errors"][:8]))
    record = {"schema": "blogger-cloner-frozen/v1", "frozen_at": now(),
              "split_digest": project.sources()["split_digest"],
              "files": {name: sha256_file(pack / name) for name in PACK_FILES}}
    write_json(pack / "FROZEN.json", record)
    project.data.setdefault("packs", {})[pack.name] = {"path": str(pack.relative_to(project.root)), "frozen_at": record["frozen_at"]}
    project.mark("frozen")
    return {"frozen": str(pack / "FROZEN.json"), "warnings": result["warnings"],
            "next": "holdout-brief, write blind trials, trial-register, then holdout-open"}


def require_frozen(pack: Path) -> dict:
    if not (pack / "FROZEN.json").is_file():
        raise CliError("pack is not frozen")
    record = load_json(pack / "FROZEN.json")
    for name, digest in record["files"].items():
        if sha256_file(pack / name) != digest:
            raise CliError(f"{name} changed after freeze")
    return record


# ---------------------------------------------------------------- holdout and trials

def cmd_holdout_brief(args) -> dict:
    project = Project(Path(args.project))
    pack = Path(args.pack).resolve()
    require_frozen(pack)
    src = project.require_split()
    index = {i["sample_id"]: i for i in project.index()["items"]}
    briefs = []
    for item in items_by(src, "holdout"):
        meta = index.get(item["sample_id"], {})
        briefs.append({"sample_id": item["sample_id"], "title": item["title"], "digest": meta.get("digest", ""),
                       "date": item["date"], "target_units": item["units"],
                       "instruction": "Write a style probe from the title and digest only. Do not invent concrete numbers, "
                                      "test results or personal experiences; frame unknowns as open questions or general observation."})
    out = project.root / "trials" / "briefs.json"
    write_json(out, {"schema": "blogger-cloner-briefs/v1", "issued_at": now(), "pack": pack.name,
                     "holdout_opened": project.holdout_open(), "briefs": briefs})
    project.data["briefs_issued_at"] = project.data.get("briefs_issued_at") or now()
    project.save()
    return {"briefs": str(out), "items": briefs}


def cmd_trial_register(args) -> dict:
    project = Project(Path(args.project))
    pack = Path(args.pack).resolve()
    require_frozen(pack)
    src = project.require_split()
    if args.holdout not in {i["sample_id"] for i in items_by(src, "holdout")}:
        raise CliError(f"not a holdout sample: {args.holdout}")
    if args.label not in TRIAL_LABELS:
        raise CliError(f"label must be one of {sorted(TRIAL_LABELS)}")
    draft = Path(args.draft).resolve()
    target = project.root / "trials" / args.holdout / f"{args.label}.md"
    if target.exists():
        raise CliError(f"trial already registered: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(draft, target)
    row = {"sample_id": args.holdout, "label": args.label, "pack": pack.name,
           "path": str(target.relative_to(project.root)), "sha256": sha256_file(target),
           "registered_at": now(), "blind": not project.holdout_open()}
    project.data.setdefault("trials", []).append(row)
    project.save()
    project.mark("trial_registered")
    return row


def cmd_holdout_open(args) -> dict:
    project = Project(Path(args.project))
    pack = Path(args.pack).resolve()
    require_frozen(pack)
    src = project.require_split()
    if not project.holdout_open():
        project.data["holdout_opened_at"] = now()
        project.save()
        project.mark("holdout_opened")
    skip = {r["key"] for r in load_json(pack / "metrics.train.json").get("boilerplate", []) if r.get("key")}
    per_doc = {i["sample_id"]: sm.doc_metrics(read_item(project, i), i["title"], skip) for i in items_by(src, "holdout")}
    write_json(project.research / "metrics" / "holdout.json",
               {"schema": "blogger-cloner-holdout-metrics/v1", "generated_at": now(), "per_doc": per_doc})
    report_path = pack / "holdout-report.json"
    if not report_path.exists():
        profile = load_json(pack / "style-profile.json")
        items = [{"rule_id": r["id"], "sample_id": h["sample_id"], "result": None, "evidence": [], "note": ""}
                 for r in profile["rules"] for h in items_by(src, "holdout")]
        write_json(report_path, {"schema": "blogger-cloner-holdout/v1", "pack": pack.name,
                                 "opened_at": project.data["holdout_opened_at"],
                                 "holdout": [h["sample_id"] for h in items_by(src, "holdout")],
                                 "items": items, "suggested_revisions": []})
    trials = project.data.get("trials", [])
    return {"opened_at": project.data["holdout_opened_at"], "report": str(report_path),
            "blind_trials": sum(1 for t in trials if t["blind"]),
            "next": "read each holdout with show, fill every rule x holdout result, then holdout-check"}


def cmd_holdout_fill(args) -> dict:
    """Merge reader annotations {rule_id: {sample_id: [result, [[q, block], ...], note]}} into the report."""
    project = Project(Path(args.project))
    pack = Path(args.pack).resolve()
    require_frozen(pack)
    if not project.holdout_open():
        raise CliError("holdout is still sealed; run holdout-open first")
    report_path = pack / "holdout-report.json"
    report = load_json(report_path)
    notes = load_json(Path(args.annotations))
    index = {(i["rule_id"], i["sample_id"]): i for i in report["items"]}
    filled, unknown = 0, []
    for rule_id, per_sample in notes.get("items", {}).items():
        for sid, (result, quotes, note) in per_sample.items():
            item = index.get((rule_id, sid))
            if not item:
                unknown.append(f"{rule_id}/{sid}")
                continue
            item["result"] = result
            item["evidence"] = [{"kind": "title"} if q == "TITLE" else {"q": q, "block": b} for q, b in quotes]
            item["note"] = note
            filled += 1
    if notes.get("suggested_revisions"):
        report["suggested_revisions"] = notes["suggested_revisions"]
    write_json(report_path, report)
    return {"filled": filled, "unknown": unknown, "next": "holdout-check --write-summary"}


def audit_file(pack: Path, path: Path, title: str) -> dict:
    report = sm.audit(pack, path, title)
    return {"status": report["status"], "band_fit": {k: report["band_fit"][k] for k in ("checked", "in_band", "ratio")},
            "out_of_band": [o["metric"] for o in report["band_fit"]["out_of_band"]],
            "overlap_longest": report["overlap"]["longest"], "overlap_runs": len(report["overlap"]["runs"]),
            "identity_hits": report["identity_hits"], "overuse": [o["gram"] for o in report["overuse"]]}


def cmd_holdout_check(args) -> dict:
    project = Project(Path(args.project))
    pack = Path(args.pack).resolve()
    require_frozen(pack)
    if not project.holdout_open():
        raise CliError("holdout is still sealed; run holdout-open first")
    src = project.require_split()
    holdout = {i["sample_id"]: i for i in items_by(src, "holdout")}
    profile = load_json(pack / "style-profile.json")
    report_path = pack / "holdout-report.json"
    report = load_json(report_path)
    expected = {(r["id"], h) for r in profile["rules"] for h in holdout}
    seen, errors, counts = set(), [], {k: 0 for k in RESULTS}
    contaminated_pack = bool(profile["provenance"].get("holdout_opened_before_build"))
    blocks = {sid: sm.parse_markdown(read_item(project, it)) for sid, it in holdout.items()}
    independent_hits = 0
    for item in report["items"]:
        key = (item["rule_id"], item["sample_id"])
        seen.add(key)
        result = item.get("result")
        if result is None:
            continue
        if result not in RESULTS:
            errors.append(f"{key}: result must be one of {sorted(RESULTS)}")
            continue
        counts[result] += 1
        if result in ("hit", "partial"):
            if not item.get("evidence"):
                errors.append(f"{key}: {result} needs at least one quote from the holdout article")
            for ev in item.get("evidence", []):
                if ev.get("kind") == "title":
                    ev["quote"] = holdout[item["sample_id"]]["title"]
                    continue
                found = locate_quote(ev.get("q", ""), blocks[item["sample_id"]], ev.get("block"))
                if "error" in found:
                    errors.append(f"{key}: {found['error']}")
                else:
                    ev.update(found)
            if result == "hit" and not item.get("contaminated") and not contaminated_pack:
                independent_hits += 1
        elif not str(item.get("note") or "").strip():
            errors.append(f"{key}: {result} needs a note")
    missing = sorted(expected - seen)
    filled = sum(counts.values())
    holdout_metrics = load_json(project.research / "metrics" / "holdout.json")["per_doc"]
    dist = load_json(pack / "metrics.train.json")["distributions"]
    real_fit = {sid: sm.band_fit(m, dist) for sid, m in holdout_metrics.items()}
    trials = []
    for t in project.data.get("trials", []):
        if t["pack"] != pack.name:
            continue
        path = project.root / t["path"]
        trials.append({**{k: t[k] for k in ("sample_id", "label", "blind", "path")},
                       "audit": audit_file(pack, path, holdout[t["sample_id"]]["title"])})

    def mean_ratio(rows):
        vals = [r for r in rows if r is not None]
        return round(sum(vals) / len(vals), 3) if vals else None

    summary = {
        "checked_at": now(), "total": len(expected), "filled": filled,
        "coverage": round(filled / len(expected), 3) if expected else None,
        "results": counts, "independent_hits": independent_hits, "contaminated_pack": contaminated_pack,
        "contaminated_items": sum(1 for i in report["items"] if i.get("contaminated")),
        "holdout_band_fit": {sid: {"ratio": f["ratio"], "out_of_band": [o["metric"] for o in f["out_of_band"]]}
                             for sid, f in real_fit.items()},
        "trials": trials,
        "mean_band_fit": {"holdout_real": mean_ratio([f["ratio"] for f in real_fit.values()]),
                          "pack_trials": mean_ratio([t["audit"]["band_fit"]["ratio"] for t in trials if t["label"] == "pack"]),
                          "control_trials": mean_ratio([t["audit"]["band_fit"]["ratio"] for t in trials if t["label"] == "control"])},
        "note": "Band fit compares surface metrics with the training P10-P90 range. Rule results are the reader's annotations. Neither is a quality score.",
    }
    report["summary"] = summary
    if args.write_summary and not errors:
        write_json(report_path, report)
    if not errors and not missing:
        project.mark("holdout_checked")
    return {"ok": not errors and not missing, "errors": errors[:20], "missing": [list(m) for m in missing[:20]],
            "missing_count": len(missing), "summary": summary}


def cmd_blind(args) -> dict:
    project = Project(Path(args.project))
    pack = Path(args.pack).resolve()
    require_frozen(pack)
    if not project.holdout_open():
        raise CliError("open the holdout first")
    src = project.require_split()
    holdout = {i["sample_id"]: i for i in items_by(src, "holdout")}
    out = project.root / "trials" / "blind"
    if out.exists():
        raise CliError(f"blind set already exists: {out}")
    out.mkdir(parents=True)
    rng = random.Random(args.seed)
    key = {}
    n = 0
    for t in project.data.get("trials", []):
        if t["label"] != "pack" or t["pack"] != pack.name:
            continue
        n += 1
        item = holdout[t["sample_id"]]
        real = "\n\n".join(_texts(read_item(project, item)))
        trial = "\n\n".join(_texts((project.root / t["path"]).read_text(encoding="utf-8")))
        real_slot = rng.choice("AB")
        for slot in "AB":
            body = real if slot == real_slot else trial
            (out / f"pair-{n}-{slot}.md").write_text(f"# {item['title']}\n\n{body}\n", encoding="utf-8")
        key[str(n)] = {"real": real_slot, "sample_id": t["sample_id"]}
    if not n:
        raise CliError("no registered pack trials")
    write_json(out / ".key.json", {"schema": "blogger-cloner-blind-key/v1", "created_at": now(), "pairs": key})
    return {"pairs": n, "dir": str(out),
            "instruction": "A human reader picks the real article in each pair, then run blind-score --answers 1=A,2=B. Do not open .key.json first."}


def cmd_blind_score(args) -> dict:
    project = Project(Path(args.project))
    out = project.root / "trials" / "blind"
    key = load_json(out / ".key.json")["pairs"]
    answers = dict(a.split("=", 1) for a in args.answers.split(",") if "=" in a)
    if set(answers) != set(key):
        raise CliError(f"answer every pair: {sorted(key)}")
    rows = [{"pair": p, "picked": answers[p].upper(), "real": key[p]["real"],
             "fooled": answers[p].upper() != key[p]["real"]} for p in sorted(key)]
    result = {"schema": "blogger-cloner-blind-result/v1", "scored_at": now(), "reader": args.reader,
              "pairs": rows, "fooled": sum(r["fooled"] for r in rows), "total": len(rows)}
    write_json(out / "result.json", result)
    return result


# ---------------------------------------------------------------- render and package

def render_guide(pack: Path, include_holdout: bool = True) -> str:
    profile = load_json(pack / "style-profile.json")
    evidence = {e["id"]: e for e in load_evidence(pack)}
    metrics = load_json(pack / "metrics.train.json")
    brand = load_json(pack / "brand.json")
    dist = metrics["distributions"]
    n = len(profile["split"]["train"])
    lines = [f"# {profile['display_name']} · 风格画像 v{profile['version']}", "",
             f"> {profile['essence']}", "",
             "## 样本与方法", "",
             f"- 来源：{profile['platform']} 公开文章，格式期 {profile['era_scope'].get('from', '')} 至 {profile['era_scope'].get('to', '')}。",
             f"- 拆分：训练 {n} 篇，留出 {len(profile['split']['holdout'])} 篇；拆分在阅读前冻结（digest `{profile['split']['digest'][:12]}`）。",
             "- 规则来自训练集逐篇通读；每条原话都可在训练原文中逐字找到，支持数由证据推出。",
             "- 迁移的是写法与结构，不是作者身份、原文句子或其观点。", ""]
    for d in profile["dimensions"]:
        lines += [f"## {d['label']}（{d['id']}）", "", d["summary"], ""]
        for r in [x for x in profile["rules"] if x["dimension"] == d["id"]]:
            support = f"{r['support_count']}/{r['eligible_sample_count']}" if r["support_count"] else "测量"
            lines.append(f"### `{r['id']}` · {r['strength']} · 支持 {support} · 置信 {r['confidence']}")
            lines += ["", f"- 观察：{r['observation']}", f"- 写法：{r['instruction']}", f"- 适用：{r['scope']}"]
            if r.get("exceptions"):
                lines.append("- 例外：" + "；".join(r["exceptions"]))
            if r.get("check"):
                lines.append(f"- 验收：{r['check']}")
            shown = 0
            for eid in r["evidence_ids"]:
                e = evidence.get(eid)
                if not e:
                    continue
                if e["kind"] in ("quote", "title") and shown < 3:
                    lines.append(f"- 例（{eid}）：「{e['quote']}」")
                    shown += 1
                elif e["kind"] == "measurement":
                    value = e["value"] if not isinstance(e["value"], dict) else e["value"].get("median", e["value"])
                    lines.append(f"- 测量（{eid}）：`{e['field']}` = {value} {e.get('note', '')}".rstrip())
                elif e["kind"] == "observation" and shown < 3:
                    lines.append(f"- 观察（{eid}）：{e['description']}")
                    shown += 1
            lines.append("")
    if profile.get("templates"):
        lines += ["## 文章模板", "", "比例是编辑建议，不是硬性配额。", ""]
        for t in profile["templates"]:
            lines += [f"### {t.get('name', t.get('id'))}", "", t.get("notes", ""), ""]
            for s in t.get("stages", []):
                lines.append(f"1. **{s.get('role', '')}**（{s.get('share', '')}）：{s.get('notes', '')}")
            lines.append("")
    lines += ["## 度量带（训练集 P10 / 中位 / P90）", "", "| 指标 | P10 | 中位 | P90 |", "| --- | --- | --- | --- |"]
    for key in sm.FIT_KEYS:
        d = dist.get(key)
        if d and "p10" in d:
            lines.append(f"| {METRIC_LABELS.get(key, key)} | {d['p10']} | {d['median']} | {d['p90']} |")
    lines.append("")
    sig = metrics.get("signature_ngrams", {})
    rows = (sig.get("distinctive") or sig.get("frequent") or [])[:20]
    if rows:
        kind = "相对基线语料的高倍率短语" if sig.get("distinctive") else "跨篇高频短语（无基线语料）"
        lines += [f"## 标志短语（{kind}）", "", "只作识别线索，按训练集密度使用；超过最密一篇的 1.5 倍会被审计标为过量模仿。", ""]
        lines.append("、".join(f"{r['gram']}（{r['df']}/{sig['n_docs']} 篇）" for r in rows))
        lines.append("")
    lines += ["## 品牌位", "", f"- 定位：{brand.get('positioning') or '未记录'}", f"- 读者：{brand.get('audience') or '未记录'}"]
    if brand.get("topics"):
        lines.append("- 选题：" + "、".join(brand["topics"]))
    for slot in brand.get("brand_slots", []):
        lines.append(f"- {slot.get('position', '')}：{slot.get('function', '')}——{slot.get('pattern', '')}，新文章填入使用者自己的品牌。")
    lines += ["", "## 禁用与边界", ""] + [f"- {g}" for g in profile["guardrails"]]
    lines.append("- 不出现原作者的身份标识：" + "、".join(brand.get("identity_tokens", [])))
    lines.append("")
    report_path = pack / "holdout-report.json"
    if include_holdout and report_path.is_file() and load_json(report_path).get("summary"):
        s = load_json(report_path)["summary"]
        r = s["results"]
        lines += ["## 留出检验", "",
                  f"- 覆盖 {s['filled']}/{s['total']}；命中 {r['hit']}、部分 {r['partial']}、未中 {r['miss']}、不适用 {r['not_applicable']}；独立命中 {s['independent_hits']}。",
                  f"- 度量带吻合（均值）：留出原文 {s['mean_band_fit']['holdout_real']}，按画像写的盲测稿 {s['mean_band_fit']['pack_trials']}，不用画像的对照稿 {s['mean_band_fit']['control_trials']}。",
                  "- 这些是表层度量与规则标注，不是质量分。", ""]
        revisions = load_json(report_path).get("suggested_revisions", [])
        if revisions:
            lines += ["待下一版修订：", ""] + [f"- {x}" for x in revisions] + [""]
    if profile.get("limits"):
        lines += ["## 局限", ""] + [f"- {x}" for x in profile["limits"]] + [""]
    if profile.get("unknowns"):
        lines += ["## 未知项", ""] + [f"- {x}" for x in profile["unknowns"]] + [""]
    return "\n".join(lines).rstrip() + "\n"


def cmd_render(args) -> dict:
    pack = Path(args.pack).resolve()
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_guide(pack), encoding="utf-8")
    if args.project:
        Project(Path(args.project)).mark("guide_rendered")
    return {"guide": str(out)}


def fill(template: str, values: dict, quoted: bool = False) -> str:
    """quoted: the template places values inside JSON or YAML double-quoted strings."""
    for key, value in values.items():
        text = json.dumps(str(value), ensure_ascii=False)[1:-1] if quoted else str(value)
        template = template.replace(f"<<{key}>>", text)
    left = re.findall(r"<<[A-Z_]+>>", template)
    if left:
        raise CliError(f"unfilled template keys: {sorted(set(left))}")
    return template


def sanitize_boilerplate(row: dict) -> dict:
    out = {k: v for k, v in row.items() if k not in ("key", "text")}
    if row.get("key"):
        out["key_sha1"] = sm.key_hash(row["key"])
    text = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "[邮箱]", row.get("text", ""))
    out["text"] = re.sub(r"https?://\S+", "[链接]", text)
    return out


def cmd_package(args) -> dict:
    project = Project(Path(args.project))
    pack = Path(args.pack).resolve()
    require_frozen(pack)
    if not project.has("holdout_checked") and not args.allow_unchecked:
        raise CliError("holdout not checked; finish holdout-check or pass --allow-unchecked (the card will say so)")
    target = Path(args.into).resolve()
    manifest = target / "skill.yaml"
    profile = load_json(pack / "style-profile.json")
    if not manifest.is_file() or f"id: {profile['style_id']}" not in manifest.read_text(encoding="utf-8"):
        raise CliError(f"{target} is not a lov-skill-creator source for {profile['style_id']}; initialize it first")
    templates = SKILL_ROOT / "assets" / "writer-skill"
    brand = load_json(pack / "brand.json")
    report = load_json(pack / "holdout-report.json") if (pack / "holdout-report.json").is_file() else {}
    summary = report.get("summary") or {}
    results = summary.get("results") or {}
    pack_trials = [t for t in summary.get("trials", []) if t["label"] == "pack"]
    case_trial = pack_trials[0] if pack_trials else None
    holdout_line = ("未完成留出检验" if not summary else
                    f"留出覆盖 {summary['filled']}/{summary['total']}，命中 {results.get('hit', 0)}、部分 {results.get('partial', 0)}、"
                    f"未中 {results.get('miss', 0)}；度量带吻合均值：留出原文 {summary['mean_band_fit']['holdout_real']}、"
                    f"盲测稿 {summary['mean_band_fit']['pack_trials']}、对照稿 {summary['mean_band_fit']['control_trials']}")
    values = {
        "STYLE_ID": profile["style_id"], "DISPLAY_NAME": profile["display_name"],
        "ENGLISH_NAME": args.english_name, "CREATOR": profile["creator"], "PLATFORM": profile["platform"],
        "VERSION": "0.1.0", "PACK_VERSION": profile["version"], "ESSENCE": profile["essence"],
        "TRAIN_N": len(profile["split"]["train"]), "HOLDOUT_N": len(profile["split"]["holdout"]),
        "RULE_N": len(profile["rules"]), "EVIDENCE_N": len(load_evidence(pack)),
        "ERA_FROM": profile["era_scope"].get("from", ""), "ERA_TO": profile["era_scope"].get("to", ""),
        "HOLDOUT_LINE": holdout_line,
        "IDENTITY_TOKENS": "、".join(brand.get("identity_tokens", [])),
        "DESCRIPTION": args.description,
        "CASE_TITLE": (f"留出盲测：按画像写「{next((i['title'] for i in project.sources()['items'] if case_trial and i['sample_id'] == case_trial['sample_id']), '')}」"
                       if case_trial else "风格包构建"),
        "CASE_OUTPUT": (f"assets/style-pack/holdout-report.json 中 {case_trial['sample_id']} 的盲测审计：状态 {case_trial['audit']['status']}，"
                        f"度量带 {case_trial['audit']['band_fit']['in_band']}/{case_trial['audit']['band_fit']['checked']}，"
                        f"原文重合最长 {case_trial['audit']['overlap_longest']} 字" if case_trial else "assets/style-pack/style-profile.json"),
        "OVERLAP_LINE": (f"{len(pack_trials)} 篇盲测稿与语料连续重合最长 {max(t['audit']['overlap_longest'] for t in pack_trials)} 字"
                         if pack_trials else "尚无盲测稿"),
    }
    files_written = []
    for rel in ["SKILL.md", "README.md", "references/writing-protocol.md", "references/skill-composition.md",
                "skill-card.yaml", "skill-card.md", "cases/cases.json", "pricing-card.yaml"]:
        text = fill((templates / (rel + ".tmpl")).read_text(encoding="utf-8"), values,
                    quoted=rel.endswith((".json", ".yaml")))
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        files_written.append(rel)
    (target / "references" / "style-profile.md").write_text(render_guide(pack), encoding="utf-8")
    files_written.append("references/style-profile.md")
    asset_dir = target / "assets" / "style-pack"
    asset_dir.mkdir(parents=True, exist_ok=True)
    for name in PACK_FILES + ["FROZEN.json", "holdout-report.json"]:
        if (pack / name).is_file():
            shutil.copyfile(pack / name, asset_dir / name)
            files_written.append(f"assets/style-pack/{name}")
    for name in ("metrics.train.json", "brand.json"):
        doc = load_json(asset_dir / name)
        doc["boilerplate"] = [sanitize_boilerplate(r) for r in doc.get("boilerplate", [])]
        if name == "brand.json":
            doc["account"] = {k: v for k, v in doc.get("account", {}).items() if k != "round_head_img"}
        write_json(asset_dir / name, doc)
    write_json(asset_dir / "PACKAGED.json", {
        "schema": "blogger-cloner-packaged/v1", "packaged_at": now(), "source_pack": pack.name,
        "source_frozen": load_json(pack / "FROZEN.json"),
        "transforms": ["metrics.train.json and brand.json: boilerplate keys replaced by SHA-1, emails and URLs redacted",
                       "brand.json: avatar URL removed"],
        "note": "Files other than metrics.train.json and brand.json are byte-identical to the frozen pack."})
    files_written.append("assets/style-pack/PACKAGED.json")
    shutil.copyfile(SKILL_ROOT / "scripts" / "stylometry.py", target / "scripts" / "stylometry.py")
    files_written.append("scripts/stylometry.py")
    project.mark("packaged")
    return {"skill_source": str(target), "files": files_written,
            "next": "run the creator validator in the new source, then exercise one writing request"}


def cmd_status(args) -> dict:
    project = Project(Path(args.project))
    order = ["ingested", "sampled", "split_frozen", "measured", "drafted", "verified", "frozen",
             "trial_registered", "holdout_opened", "holdout_checked", "guide_rendered", "packaged"]
    states = project.data.get("states", {})
    pending = next((s for s in order if s not in states), None)
    return {"project": str(project.root), "creator": project.data["creator"], "states": states,
            "next_state": pending, "holdout_opened_at": project.data.get("holdout_opened_at"),
            "trials": project.data.get("trials", [])}


# ---------------------------------------------------------------- CLI

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, help_text, project=True, pack=False):
        sp = sub.add_parser(name, help=help_text)
        if project:
            sp.add_argument("--project", required=True, help="project directory containing project.json")
        if pack:
            sp.add_argument("--pack", required=True, help="style pack directory")
        return sp

    sp = add("doctor", "check runtime", project=False)
    sp.add_argument("--root")
    sp = add("init", "create a project workspace", project=False)
    sp.add_argument("--slug", required=True)
    sp.add_argument("--creator", required=True, help="creator display name")
    sp.add_argument("--platform", default="wechat")
    sp.add_argument("--profile-url", default="")
    sp.add_argument("--root", required=True)
    sp = add("ingest", "import articles from an export or a Markdown directory")
    sp.add_argument("--source", choices=["wxmp-export", "files"], required=True)
    sp.add_argument("--path", required=True)
    sp.add_argument("--role", choices=["sample", "baseline"], default="sample")
    sp.add_argument("--platform", default="wechat")
    sp.add_argument("--label", default="")
    add("candidates", "list ingested articles with selection flags")
    sp = add("select", "choose the sample frame and the holdout")
    sp.add_argument("--holdout", default="")
    sp.add_argument("--holdout-count", type=int, default=3)
    sp.add_argument("--exclude", default="")
    sp.add_argument("--era-from", default="")
    sp.add_argument("--era-to", default="")
    sp.add_argument("--era-note", default="")
    sp.add_argument("--note", default="")
    add("freeze-split", "hash samples and freeze the split")
    add("metrics", "measure the training set")
    sp = add("show", "print an article as numbered blocks (holdout sealed until holdout-open)")
    sp.add_argument("--id")
    sp.add_argument("--list", action="store_true")
    sp.add_argument("--start", type=int, default=0)
    sp.add_argument("--end", type=int, default=None)
    sp = add("build", "resolve a rules draft into a style pack")
    sp.add_argument("--draft", required=True)
    sp.add_argument("--out", required=True)
    add("verify", "re-check a style pack", pack=True)
    add("freeze", "freeze a verified pack", pack=True)
    add("holdout-brief", "issue title/digest-only briefs for blind trials", pack=True)
    sp = add("trial-register", "register a blind trial draft before the holdout opens", pack=True)
    sp.add_argument("--holdout", required=True)
    sp.add_argument("--draft", required=True)
    sp.add_argument("--label", default="pack")
    add("holdout-open", "unseal the holdout after freezing", pack=True)
    sp = add("holdout-fill", "merge compact reader annotations into the holdout report", pack=True)
    sp.add_argument("--annotations", required=True)
    sp = add("holdout-check", "validate rule x holdout results and audit trials", pack=True)
    sp.add_argument("--write-summary", action="store_true")
    sp = add("blind", "make real-vs-trial pairs for a human reader", pack=True)
    sp.add_argument("--seed", type=int, default=None)
    sp = add("blind-score", "score a human reader's answers")
    sp.add_argument("--answers", required=True)
    sp.add_argument("--reader", default="human")
    sp = sub.add_parser("render", help="render a pack as a Markdown style guide")
    sp.add_argument("--pack", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--project")
    sp = add("package", "write a creator writing Skill into a lov-skill-creator source", pack=True)
    sp.add_argument("--into", required=True)
    sp.add_argument("--english-name", required=True)
    sp.add_argument("--description", required=True, help="50-200 character routing description")
    sp.add_argument("--allow-unchecked", action="store_true")
    add("status", "show project states")
    return p


COMMANDS = {
    "doctor": cmd_doctor, "init": cmd_init, "ingest": cmd_ingest, "candidates": cmd_candidates,
    "select": cmd_select, "freeze-split": cmd_freeze_split, "metrics": cmd_metrics, "build": cmd_build,
    "verify": cmd_verify, "freeze": cmd_freeze, "holdout-brief": cmd_holdout_brief,
    "trial-register": cmd_trial_register, "holdout-open": cmd_holdout_open, "holdout-fill": cmd_holdout_fill,
    "holdout-check": cmd_holdout_check,
    "blind": cmd_blind, "blind-score": cmd_blind_score, "render": cmd_render, "package": cmd_package,
    "status": cmd_status,
}


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "show":
            return cmd_show(args)
        result = COMMANDS[args.cmd](args)
        ok = result.get("ok", True) if isinstance(result, dict) else True
        print(json.dumps({"ok": ok, "command": args.cmd, "data": result}, ensure_ascii=False, indent=2))
        return 0 if ok else 1
    except CliError as exc:
        print(json.dumps({"ok": False, "command": args.cmd, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
