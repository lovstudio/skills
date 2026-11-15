#!/usr/bin/env python3
"""Collect reproducible evidence for open-source competitor research.

Subcommands (all print JSON to stdout, progress to stderr):

  facts    GitHub metadata, community counts, contributor concentration and
           derived traction ratios for one or more OWNER/REPO slugs (needs gh).
  history  Commit-history profile of a local full clone: root commits, monthly
           cadence, quiet months, author concentration, fork/rewrite signals.
  loc      Line counts by directory, test footprint and dependency manifests
           of a local clone.
  lineage  Derivation scan: does a TARGET clone contain blobs, distinctive
           identifiers or name mentions of a SOURCE clone anywhere in history?

The script reports evidence; it never decides a verdict on its own.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


class CommandError(RuntimeError):
    def __init__(self, cmd: list[str], code: int, message: str):
        super().__init__(f"{' '.join(cmd[:3])} exited {code}: {message[:300]}")
        self.cmd = cmd
        self.code = code
        self.message = message


def log(message: str) -> None:
    print(f"[repo_evidence] {message}", file=sys.stderr)


def run(cmd: list[str], cwd: Path | None = None, check: bool = True, timeout: int = 900) -> str:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if check and proc.returncode != 0:
        raise CommandError(cmd, proc.returncode, (proc.stderr or proc.stdout).strip())
    return proc.stdout


def emit(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------- GitHub facts

def gh(path: str, fields: list[tuple[str, str]] | None = None, jq: str | None = None,
       paginate: bool = False, headers: list[str] | None = None, retries: int = 3) -> str:
    cmd = ["gh", "api"]
    for header in headers or []:
        cmd += ["-H", header]
    if fields:
        cmd += ["-X", "GET"]
        for key, value in fields:
            cmd += ["-f", f"{key}={value}"]
    if paginate:
        cmd.append("--paginate")
    if jq:
        cmd += ["--jq", jq]
    cmd.append(path)
    last: CommandError | None = None
    for attempt in range(retries):
        try:
            return run(cmd, timeout=300)
        except CommandError as exc:
            last = exc
            # 404/401/403 are answers, not transient failures; the search API
            # sometimes drops the connection with a bare "EOF", which is.
            if re.search(r"HTTP 40[134]|Not Found|Bad credentials", exc.message):
                break
            time.sleep(2 * (attempt + 1))
    assert last is not None
    raise last


def ratio(numerator: float | None, denominator: float | None, scale: float = 1.0, digits: int = 3):
    if numerator is None or not denominator:
        return None
    return round(numerator / denominator * scale, digits)


def star_sample(slug: str, size: int, errors: list[dict]) -> dict:
    owner, name = slug.split("/", 1)
    query = (
        "query($owner:String!,$name:String!,$n:Int!){repository(owner:$owner,name:$name){"
        "stargazerCount stargazers(last:$n){totalCount edges{starredAt node{createdAt "
        "followers{totalCount} repositories{totalCount}}}}}}"
    )
    try:
        raw = run(["gh", "api", "graphql", "-f", f"owner={owner}", "-f", f"name={name}",
                   "-F", f"n={size}", "-f", f"query={query}"], timeout=300)
        repo = json.loads(raw)["data"]["repository"]
    except (CommandError, KeyError, TypeError, json.JSONDecodeError) as exc:
        errors.append({"repo": slug, "endpoint": "graphql stargazers", "error": str(exc)[:300]})
        return {"available": False}
    edges = repo["stargazers"]["edges"]
    if not edges:
        return {
            "available": False,
            "note": "GraphQL returned no stargazer edges although stargazerCount is "
                    f"{repo['stargazerCount']}; star quality cannot be sampled.",
        }
    low_signal = 0
    for edge in edges:
        node = edge.get("node") or {}
        starred = datetime.fromisoformat(edge["starredAt"].replace("Z", "+00:00"))
        created = datetime.fromisoformat(node.get("createdAt", edge["starredAt"]).replace("Z", "+00:00"))
        if ((starred - created).days < 30 and node.get("followers", {}).get("totalCount", 0) == 0
                and node.get("repositories", {}).get("totalCount", 0) == 0):
            low_signal += 1
    return {
        "available": True,
        "sampled": len(edges),
        "window": [edges[0]["starredAt"], edges[-1]["starredAt"]],
        "low_signal_accounts": low_signal,
        "low_signal_share": ratio(low_signal, len(edges)),
        "definition": "account created <30 days before starring, 0 followers, 0 public repos",
    }


def repo_facts(slug: str, star_n: int, errors: list[dict]) -> dict:
    log(f"facts {slug}")
    out: dict = {"repo": slug}
    try:
        meta = json.loads(gh(f"repos/{slug}"))
    except (CommandError, json.JSONDecodeError) as exc:
        errors.append({"repo": slug, "endpoint": f"repos/{slug}", "error": str(exc)[:300]})
        return out
    stars = meta.get("stargazers_count") or 0
    forks = meta.get("forks_count") or 0
    out.update({
        "full_name": meta.get("full_name"),
        "description": meta.get("description"),
        "homepage": meta.get("homepage") or None,
        "fork": meta.get("fork"),
        "parent": (meta.get("parent") or {}).get("full_name"),
        "source": (meta.get("source") or {}).get("full_name"),
        "archived": meta.get("archived"),
        "created_at": meta.get("created_at"),
        "pushed_at": meta.get("pushed_at"),
        "default_branch": meta.get("default_branch"),
        "language": meta.get("language"),
        "license": (meta.get("license") or {}).get("spdx_id"),
        "topics": meta.get("topics") or [],
        "stars": stars,
        "forks": forks,
        "watchers": meta.get("subscribers_count"),
        "size_kb": meta.get("size"),
    })

    counts: dict = {}
    for key, qualifier in (("issues", "type:issue"), ("open_issues", "type:issue state:open"),
                           ("prs", "type:pr"), ("merged_prs", "type:pr is:merged")):
        try:
            counts[key] = int(gh("search/issues", fields=[("q", f"repo:{slug} {qualifier}")],
                                 jq=".total_count").strip())
        except (CommandError, ValueError) as exc:
            counts[key] = None
            errors.append({"repo": slug, "endpoint": f"search/issues {qualifier}", "error": str(exc)[:300]})
        time.sleep(2)  # search API allows about 30 requests per minute
    out["counts"] = counts

    try:
        raw = gh(f"repos/{slug}/contributors?per_page=100&anon=1", paginate=True,
                 jq='.[] | [(.login // .name // "anonymous"), (.contributions|tostring)] | @tsv')
        rows = [line.split("\t") for line in raw.splitlines() if "\t" in line]
        contributions = [(who, int(n)) for who, n in rows]
        total = sum(n for _, n in contributions)
        out["contributors"] = {
            "count": len(contributions),
            "top": [{"name": who, "contributions": n} for who, n in contributions[:5]],
            "top1_share": ratio(contributions[0][1], total) if contributions else None,
            "note": "GitHub attributes commits per account; one person with several "
                    "accounts or emails is split. Cross-check with `history`.",
        }
    except (CommandError, ValueError) as exc:
        out["contributors"] = None
        errors.append({"repo": slug, "endpoint": "contributors", "error": str(exc)[:300]})

    created = datetime.fromisoformat(meta["created_at"].replace("Z", "+00:00"))
    months = max((datetime.now(timezone.utc) - created).days / 30.44, 1 / 30.44)
    out["derived"] = {
        "age_months": round(months, 1),
        "stars_per_month": round(stars / months),
        "fork_to_star_pct": ratio(forks, stars, 100, 1),
        "issues_per_1k_stars": ratio(counts.get("issues"), stars, 1000, 1),
        "merged_pr_share": ratio(counts.get("merged_prs"), counts.get("prs")),
        "caveat": "Heuristics for engagement depth, not proof of fake or real stars.",
    }
    if star_n:
        out["star_sample"] = star_sample(slug, star_n, errors)
    return out


def cmd_facts(args: argparse.Namespace) -> int:
    errors: list[dict] = []
    repos = [repo_facts(slug.strip("/"), args.star_sample, errors) for slug in args.repos]
    emit({"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
          "repos": repos, "errors": errors})
    return 0


# ---------------------------------------------------------------- local clone

def git(clone: Path, *args: str, check: bool = True, timeout: int = 900) -> str:
    return run(["git", "-C", str(clone), *args], check=check, timeout=timeout)


def clone_state(clone: Path) -> dict:
    if not (clone / ".git").exists() and git(clone, "rev-parse", "--git-dir", check=False).strip() == "":
        raise SystemExit(f"not a git clone: {clone}")
    partial = git(clone, "config", "--get", "remote.origin.partialclonefilter", check=False).strip()
    shallow = git(clone, "rev-parse", "--is-shallow-repository").strip() == "true"
    remote = git(clone, "remote", "get-url", "origin", check=False).strip()
    match = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?/?$", remote)
    return {
        "path_name": clone.name,
        "remote_slug": f"{match.group(1)}/{match.group(2)}" if match else None,
        "partial_filter": partial or None,
        "shallow": shallow,
        "head": git(clone, "rev-parse", "--short", "HEAD").strip(),
    }


def require_full(state: dict, purpose: str) -> None:
    if state["partial_filter"] or state["shallow"]:
        raise SystemExit(
            f"{state['path_name']} is a {'partial' if state['partial_filter'] else 'shallow'} clone; "
            f"{purpose} needs full history. Re-clone without --filter/--depth."
        )


def cmd_history(args: argparse.Namespace) -> int:
    clone = Path(args.clone).resolve()
    state = clone_state(clone)
    require_full(state, "history")
    total = int(git(clone, "rev-list", "--count", "HEAD").strip())
    roots = []
    for sha in git(clone, "rev-list", "--max-parents=0", "HEAD").split():
        line = git(clone, "show", "-s", "--date=short", "--format=%h%x09%ad%x09%an%x09%s", sha).strip()
        short, date, author, subject = (line.split("\t", 3) + ["", "", ""])[:4]
        roots.append({"commit": short, "date": date, "author": author, "subject": subject})

    months = Counter(git(clone, "log", "--date=format:%Y-%m", "--format=%ad", "HEAD").split())
    span = sorted(months)
    cadence = {}
    if span:
        year, month = map(int, span[0].split("-"))
        end = tuple(map(int, span[-1].split("-")))
        while (year, month) <= end:
            key = f"{year:04d}-{month:02d}"
            cadence[key] = months.get(key, 0)
            month += 1
            if month > 12:
                year, month = year + 1, 1
    quiet = [m for m, n in cadence.items() if n <= args.quiet_threshold]

    aliases = {}
    for spec in args.alias:
        alias, _, canonical = spec.partition("=")
        if alias.strip() and canonical.strip():
            aliases[alias.strip()] = canonical.strip()
    merged: Counter = Counter()
    for line in git(clone, "shortlog", "-sn", "HEAD").splitlines():
        count, _, name = line.strip().partition("\t")
        if count.strip().isdigit():
            merged[aliases.get(name.strip(), name.strip())] += int(count)
    authors = [{"name": n, "commits": c} for n, c in merged.most_common()]
    author_total = sum(a["commits"] for a in authors)

    signals = []
    raw = git(clone, "log", "-i", "-E", "--date=short", "--format=%h%x09%ad%x09%s",
              "--grep", args.signal_regex, "HEAD")
    for line in raw.splitlines()[: args.max_signals]:
        short, date, subject = (line.split("\t", 2) + ["", ""])[:3]
        signals.append({"commit": short, "date": date, "subject": subject})

    emit({
        "clone": state,
        "commits": total,
        "root_commits": roots,
        "cadence_by_month": cadence,
        "quiet_months": quiet,
        "quiet_threshold": args.quiet_threshold,
        "authors": authors[:10],
        "author_count": len(authors),
        "top1_author_share": ratio(authors[0]["commits"], author_total) if authors else None,
        "aliases_applied": aliases,
        "top_authors_note": "Git author names incl. merge commits; pass --alias OLD=NEW for one person's accounts.",
        "message_signals": signals,
        "signal_regex": args.signal_regex,
    })
    return 0


SOURCE_EXTS = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java",
               ".kt", ".swift", ".rb", ".php", ".c", ".cc", ".cpp", ".h", ".hpp", ".cs", ".vue"}
TEST_FN = re.compile(r"^\s*(?:async\s+)?def\s+test_|^\s*(?:it|test)\s*\(|^func\s+Test|^\s*#\[test\]|@Test\b",
                     re.M)


def is_test_path(path: str) -> bool:
    parts = path.lower().split("/")
    name = parts[-1]
    return (any(p in {"test", "tests", "__tests__", "spec", "testing"} for p in parts[:-1])
            or name.startswith("test_") or re.search(r"(_test|\.test|\.spec)\.[a-z]+$", name) is not None)


def manifest_deps(clone: Path, rel: str) -> int | None:
    path = clone / rel
    text = path.read_text(encoding="utf-8", errors="replace")
    name = path.name
    try:
        if name == "package.json":
            data = json.loads(text)
            return len(data.get("dependencies") or {})
        if name.startswith("requirements") and name.endswith(".txt"):
            return sum(1 for line in text.splitlines() if line.strip() and not line.lstrip().startswith(("#", "-")))
        if name in {"pyproject.toml", "Cargo.toml"}:
            try:
                import tomllib  # Python 3.11+
            except ImportError:
                if name != "pyproject.toml":
                    return None
                section = re.search(r"^\[project\]\s*$(.*?)(?=^\[[^\]]+\]\s*$|\Z)", text, re.S | re.M)
                block = section and re.search(r"^dependencies\s*=\s*\[(.*?)\]\s*$", section.group(1), re.S | re.M)
                return len(re.findall(r"[\"']([^\"']+)[\"']", block.group(1))) if block else None
            data = tomllib.loads(text)
            if name == "pyproject.toml":
                deps = (data.get("project") or {}).get("dependencies")
                if deps is None:
                    deps = ((data.get("tool") or {}).get("poetry") or {}).get("dependencies") or {}
                return len(deps)
            return len(data.get("dependencies") or {})
        if name == "go.mod":
            block = re.findall(r"require\s*\((.*?)\)", text, re.S)
            lines = [l for b in block for l in b.splitlines() if l.strip() and "// indirect" not in l]
            return len(lines) + len(re.findall(r"^require\s+\S+\s+\S+\s*$", text, re.M))
    except (ValueError, TypeError):
        return None
    return None


def cmd_loc(args: argparse.Namespace) -> int:
    clone = Path(args.clone).resolve()
    state = clone_state(clone)
    exts = {e if e.startswith(".") else f".{e}" for e in args.ext} if args.ext else SOURCE_EXTS
    files = [f for f in git(clone, "ls-files", "-z").split("\0") if f]
    by_dir: Counter = Counter()
    largest = []
    src_lines = test_lines = test_functions = 0
    for rel in files:
        if Path(rel).suffix.lower() not in exts:
            continue
        path = clone / rel
        if not path.is_file():
            continue
        data = path.read_bytes()
        lines = data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
        if is_test_path(rel):
            test_lines += lines
            test_functions += len(TEST_FN.findall(data.decode("utf-8", errors="replace")))
            continue
        src_lines += lines
        key = "/".join(rel.split("/")[: args.depth]) if rel.count("/") >= args.depth else (
            rel.rsplit("/", 1)[0] if "/" in rel else "(root)")
        by_dir[key] += lines
        largest.append((lines, rel))
    manifests = {}
    for rel in files:
        if Path(rel).name in {"package.json", "pyproject.toml", "go.mod", "Cargo.toml"} or re.match(
                r"(.*/)?requirements[^/]*\.txt$", rel):
            if rel.count("/") <= 1:
                manifests[rel] = manifest_deps(clone, rel)
    emit({
        "clone": state,
        "extensions": sorted(exts),
        "source_lines": src_lines,
        "test_lines": test_lines,
        "test_to_source": ratio(test_lines, src_lines),
        "test_functions": test_functions,
        "by_directory": [{"dir": d, "lines": n, "share": ratio(n, src_lines)} for d, n in by_dir.most_common(args.top)],
        "largest_files": [{"file": f, "lines": n} for n, f in sorted(largest, reverse=True)[: args.top]],
        "dependency_manifests": manifests,
        "note": "Lines include blanks and comments; compare repositories with the same counter.",
    })
    return 0


# ---------------------------------------------------------------- lineage

ID_PATTERNS = {
    ".py": [r"^\s*class\s+([A-Za-z_]\w+)", r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w+)"],
    ".js": [r"\bclass\s+([A-Za-z_$][\w$]+)", r"\bfunction\s+([A-Za-z_$][\w$]+)"],
    ".go": [r"^func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w+)", r"^type\s+([A-Za-z_]\w+)"],
    ".rs": [r"\bfn\s+([A-Za-z_]\w+)", r"\b(?:struct|enum|trait)\s+([A-Za-z_]\w+)"],
    ".java": [r"\b(?:class|interface|enum)\s+([A-Za-z_]\w+)"],
}
for alias in (".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".vue"):
    ID_PATTERNS[alias] = ID_PATTERNS[".js"]
ID_PATTERNS[".kt"] = ID_PATTERNS[".java"]
GENERIC_PARTS = {"get", "set", "init", "test", "main", "run", "load", "save", "update", "create",
                 "delete", "handle", "process", "parse", "config", "setup", "helper", "utils", "util",
                 "data", "list", "item", "value", "result", "response", "request", "error", "base",
                 "default", "async", "sync", "file", "path", "name", "info", "type", "make", "build"}
SKIP_BLOB_NAMES = re.compile(r"^(license|licence|copying|notice|\.gitignore|\.gitattributes|"
                             r"\.editorconfig|__init__\.py|py\.typed|\.npmignore)$", re.I)


def is_vendored(path: str) -> bool:
    parts = path.lower().split("/")
    return (any(p in {"vendor", "vendors", "third_party", "thirdparty", "node_modules", "dist", "build"}
                for p in parts[:-1]) or parts[-1].endswith((".min.js", ".bundle.js")))


def split_parts(identifier: str) -> list[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", identifier)
    return [p.lower() for p in spaced.split("_") if p]


def distinctive_identifiers(clone: Path, limit: int) -> list[str]:
    seen: Counter = Counter()
    for rel in git(clone, "ls-files", "-z").split("\0"):
        suffix = Path(rel).suffix.lower()
        if suffix not in ID_PATTERNS or is_test_path(rel) or is_vendored(rel):
            continue
        path = clone / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in ID_PATTERNS[suffix]:
            for name in re.findall(pattern, text, re.M):
                seen[name] += 1
    picked = []
    for name in seen:
        parts = split_parts(name.strip("_$"))
        specific = [p for p in parts if p not in GENERIC_PARTS and not p.isdigit()]
        if (len(name) < 10 or name.startswith("__") or name.lower().startswith("test")
                or len(parts) < 2 or len(specific) < 2):
            continue
        picked.append(name)
    # Longer, rarer names carry the strongest signal; sort deterministically.
    picked.sort(key=lambda n: (seen[n], -len(n), n))
    return picked[:limit]


def pickaxe(clone: Path, terms: list[str], ignore_case: bool, batch: int, max_commits: int) -> list[dict]:
    hits: dict[str, dict] = {}
    for start in range(0, len(terms), batch):
        chunk = terms[start:start + batch]
        pattern = "|".join(re.escape(t) for t in chunk)
        log(f"pickaxe {len(chunk)} terms in {clone.name}")
        args = ["log", "--all", "--date=short", "--format=%h%x09%ad%x09%s", f"-G{pattern}"]
        if ignore_case:
            args.insert(1, "-i")
        for line in git(clone, *args, timeout=3600).splitlines():
            short, date, subject = (line.split("\t", 2) + ["", ""])[:3]
            entry = hits.setdefault(short, {"commit": short, "date": date, "subject": subject, "matched": set()})
            if len(hits) > max_commits:
                continue
            diff = git(clone, "show", "--format=", short, check=False)
            flags = re.I if ignore_case else 0
            for term in chunk:
                if re.search(re.escape(term), diff, flags):
                    entry["matched"].add(term)
    result = []
    for entry in sorted(hits.values(), key=lambda e: e["date"]):
        entry["matched"] = sorted(entry["matched"])
        result.append(entry)
    return result


def source_blobs(source: Path, state: dict, all_history: bool, min_bytes: int) -> dict[str, str]:
    """Map blob sha -> path for source files worth comparing."""
    eligible: dict[str, str] = {}
    if not all_history:
        for line in git(source, "ls-tree", "-r", "-l", "HEAD").splitlines():
            meta, _, rel = line.partition("\t")
            fields = meta.split()
            if (len(fields) >= 4 and fields[1] == "blob" and fields[3].isdigit()
                    and int(fields[3]) >= min_bytes and not SKIP_BLOB_NAMES.match(Path(rel).name)):
                eligible[fields[2]] = rel
        return eligible
    require_full(state, "--source-all-history")
    paths: dict[str, str] = {}
    for line in git(source, "rev-list", "--all", "--objects", timeout=3600).splitlines():
        sha, _, rel = line.partition(" ")
        if rel and sha not in paths and not SKIP_BLOB_NAMES.match(Path(rel).name):
            paths[sha] = rel
    proc = subprocess.run(["git", "-C", str(source), "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
                          input="\n".join(paths) + "\n", capture_output=True, text=True, timeout=3600)
    for line in proc.stdout.splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[1] == "blob" and int(fields[2]) >= min_bytes:
            eligible[fields[0]] = paths[fields[0]]
    return eligible


def cmd_lineage(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    source = Path(args.source).resolve()
    t_state, s_state = clone_state(target), clone_state(source)
    require_full(t_state, "lineage scanning of the target")

    terms = list(dict.fromkeys(args.term))
    if s_state["remote_slug"] and not args.no_auto_terms:
        owner, name = s_state["remote_slug"].split("/", 1)
        for candidate in (name, owner, name.replace("-", "_"), name.replace("-", "")):
            if len(candidate) >= 4 and candidate.lower() not in {t.lower() for t in terms}:
                terms.append(candidate)
    identifiers = list(dict.fromkeys(args.identifier + distinctive_identifiers(source, args.max_identifiers)))

    mention_hits = pickaxe(target, terms, True, args.batch, args.max_commits) if terms else []
    identifier_hits = pickaxe(target, identifiers, False, args.batch, args.max_commits) if identifiers else []
    current_mentions = []
    if terms:
        pattern = "|".join(re.escape(t) for t in terms)
        raw = git(target, "grep", "-I", "-i", "-n", "-E", pattern, "HEAD", "--", ".", check=False)
        for line in raw.splitlines()[:20]:
            current_mentions.append(line.split(":", 1)[1][:200] if ":" in line else line[:200])

    eligible = source_blobs(source, s_state, args.source_all_history, args.min_blob_bytes)
    target_objects = {}
    for line in git(target, "rev-list", "--all", "--objects", timeout=3600).splitlines():
        sha, _, rel = line.partition(" ")
        if sha in eligible and sha not in target_objects:
            target_objects[sha] = rel
    shared = [{"source_path": eligible[sha], "target_path": target_objects[sha], "blob": sha[:12]}
              for sha in sorted(target_objects, key=lambda s: eligible[s])]

    if shared or identifier_hits:
        hint = "shared-code-found"
    elif mention_hits or current_mentions:
        hint = "mentions-only"
    else:
        hint = "no-overlap-found"
    emit({
        "target": t_state,
        "source": s_state,
        "mention_terms": terms,
        "mention_commits": mention_hits[: args.max_commits],
        "mention_commit_count": len(mention_hits),
        "current_tree_mentions": current_mentions,
        "identifiers_checked": identifiers,
        "identifier_commits": identifier_hits[: args.max_commits],
        "identifier_commit_count": len(identifier_hits),
        "shared_blobs": shared[: args.max_commits],
        "shared_blob_count": len(shared),
        "source_eligible_blobs": len(eligible),
        "source_blob_scope": "all history" if args.source_all_history else "HEAD",
        "shared_blob_share": ratio(len(shared), len(eligible)),
        "hint": hint,
        "hint_note": "A hint, not a verdict: read matched commits and identifiers before "
                     "concluding; mentions may be acknowledgements, common names may collide.",
    })
    return 0


# ---------------------------------------------------------------- CLI

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    facts = sub.add_parser("facts", help="GitHub metadata and traction ratios (needs gh)")
    facts.add_argument("repos", nargs="+", help="OWNER/REPO slugs")
    facts.add_argument("--star-sample", type=int, default=0,
                       help="Sample the latest N stargazers via GraphQL (0 = skip, max 100)")
    facts.set_defaults(func=cmd_facts)

    history = sub.add_parser("history", help="Commit history profile of a full clone")
    history.add_argument("clone")
    history.add_argument("--quiet-threshold", type=int, default=3,
                         help="Months with at most this many commits count as quiet")
    history.add_argument("--signal-regex", default=r"forked|fork of|ported? from|based on|derived from|"
                         r"copied from|zero copied|from scratch|vendored",
                         help="Commit-message regex for derivation signals")
    history.add_argument("--max-signals", type=int, default=30)
    history.add_argument("--alias", action="append", default=[],
                         help="Merge author name OLD into NEW, as OLD=NEW; repeatable")
    history.set_defaults(func=cmd_history)

    loc = sub.add_parser("loc", help="Line counts, test footprint and manifests")
    loc.add_argument("clone")
    loc.add_argument("--ext", action="append", default=[], help="Limit to extension; repeatable")
    loc.add_argument("--depth", type=int, default=2, help="Directory depth for grouping")
    loc.add_argument("--top", type=int, default=12)
    loc.set_defaults(func=cmd_loc)

    lineage = sub.add_parser("lineage", help="Does TARGET contain SOURCE code or mentions?")
    lineage.add_argument("target", help="Full clone of the suspected derivative")
    lineage.add_argument("--source", required=True, help="Clone of the suspected origin (shallow is fine)")
    lineage.add_argument("--term", action="append", default=[],
                         help="Case-insensitive mention term, e.g. author handle; repeatable")
    lineage.add_argument("--identifier", action="append", default=[],
                         help="Case-sensitive code identifier to add; repeatable")
    lineage.add_argument("--no-auto-terms", action="store_true",
                         help="Do not add the source owner and repository name as terms")
    lineage.add_argument("--max-identifiers", type=int, default=40)
    lineage.add_argument("--min-blob-bytes", type=int, default=400)
    lineage.add_argument("--source-all-history", action="store_true",
                         help="Compare blobs from every source commit, not only HEAD (needs a full source clone)")
    lineage.add_argument("--batch", type=int, default=25)
    lineage.add_argument("--max-commits", type=int, default=30)
    lineage.set_defaults(func=cmd_lineage)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if getattr(args, "star_sample", 0) > 100:
        args.star_sample = 100
    try:
        return args.func(args)
    except CommandError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"error: required executable missing: {exc.filename}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
