#!/usr/bin/env python3
"""find_project.py — 分层定位本机项目 / 源码目录。

四层递进搜索（默认自动执行到有结果为止，可用 --scope 限定）：
  1. roots   项目根目录集合（~/projects、~/Documents、~/lovstudio 等 + Profile 配置）
  2. cwd     当前工作目录及子目录
  3. chat    AI 聊天记录（~/.claude/projects 等 *.jsonl）中出现的项目路径
  4. full    全盘兜底（Spotlight mdfind + find 慢扫）

输入：项目名、关键词、或特征描述（如 "claude code 泄露源码"）。
输出：候选绝对路径 + 命中层 + 每层证据。供宿主 agent 做最终判断。
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# 默认项目根（按重要度排序）；Profile 中 workspace.projects 会追加
DEFAULT_ROOTS = [
    Path.home() / "projects",
    Path.home() / "Documents",
    Path.home() / "lovstudio",
    Path.home() / "yoda",
    Path.home() / "Desktop",
]
# 聊天记录目录（默认）
DEFAULT_CHAT_DIRS = [
    Path.home() / ".claude" / "projects",
    Path.home() / ".gemini",
]
# 扫描时总是排除的目录（大小写不敏感）
EXCLUDE_DIRS = {
    "node_modules", ".git", ".worktrees", "Library", "cache", "caches",
    "venv", ".venv", "dist", "build", ".next", "target", "Pods", ".bun",
    ".trash", "__pycache__", ".pnpm-store", ".yarn", ".DS_Store",
}

_QUERY = None  # 归一化后的查询词列表


def log(msg):
    sys.stderr.write(msg + "\n")


def norm(name):
    """归一化：小写、去空格与标点，用于匹配。"""
    return re.sub(r"[^a-z0-9一-鿿]", "", name.lower())


def query_tokens():
    """把查询词切成可匹配的 token：整体归一 + 单词拆分。"""
    global _QUERY
    if _QUERY is None:
        whole = norm(_QUERY_raw)
        words = set()
        for part in re.split(r"[\s\-_/]+", _QUERY_raw.lower()):
            p = norm(part)
            if len(p) >= 2:
                words.add(p)
        _QUERY = [whole] + sorted(words, key=len, reverse=True)
    return _QUERY


def name_matches(name):
    """目录/文件名是否匹配查询。取最高分匹配的 token。"""
    if not name:
        return False
    n = norm(name)
    if not n:
        return False
    for tok in query_tokens():
        if tok and (tok in n or n in tok):
            return True
    return False


def score_name(name, depth_penalty=0.0):
    """匹配强度：整体命中 > 长 token > 短 token。返回 float 分数，0 表示不匹配。

    整体归一化词命中才算强匹配（≥0.8）；仅拆分 token 命中打 5 折，避免
    “project” 这类通用词把无关目录抬成强候选。
    """
    n = norm(name)
    if not n:
        return 0.0
    toks = query_tokens()
    whole = toks[0] if toks else ""
    strong = False
    best_strong = 0.0
    best_weak = 0.0
    for tok in toks:
        if not tok:
            continue
        if tok == n:
            s = 1.0
        elif tok in n:
            s = 0.8 + 0.2 * (len(tok) / max(len(n), 1))
        elif n in tok:
            s = 0.5
        else:
            continue
        if tok == whole:
            best_strong = max(best_strong, s)
            strong = True
        elif tok and whole and whole in n:
            # 整体词命中过；此处只计数
            best_strong = max(best_strong, s)
            strong = True
        else:
            best_weak = max(best_weak, s)
    score = max(best_strong, best_weak * 0.5)
    if score <= 0:
        return 0.0
    return score * (1.0 - min(depth_penalty, 0.6))


def ok_dir(d):
    """是否该进入/收录此目录。排除任何隐藏路径段（如 .claude/.local）与构建产物。"""
    if not os.path.isdir(d):
        return False
    parts = [p.lower() for p in Path(d).parts]
    if any(p.startswith(".") for p in parts):
        return False
    if set(parts) & EXCLUDE_DIRS:
        return False
    return True


def find_roots():
    """默认根 + Profile workspace.projects。"""
    roots = list(DEFAULT_ROOTS)
    prof = profile_path()
    if prof and prof.exists():
        try:
            data = json.loads(prof.read_text(encoding="utf-8"))
            projs = (data.get("workspace") or {}).get("projects") or []
            for p in projs:
                if isinstance(p, str) and os.path.isdir(p):
                    roots.append(Path(p))
        except Exception as e:
            log(f"[warn] profile 解析失败: {e}")
    return roots


def profile_path():
    return Path(os.environ.get("SKILL_PROFILE_PATH", "")) if os.environ.get("SKILL_PROFILE_PATH") else None


def scan_roots(query):
    """Layer 1: 项目根目录集合。只扫顶层子目录 + 直接包含仓库的根。"""
    hits = []
    seen = set()
    for root in find_roots():
        if not root.exists():
            continue
        # 根本身匹配（如 $HOME/yoda）
        if ok_dir(root) and score_name(root.name):
            hits.append({"path": str(root), "layer": "roots", "match": "root-name", "score": round(score_name(root.name), 2)})
            seen.add(str(root))
        # 顶层子目录
        try:
            for child in root.iterdir():
                if not ok_dir(child):
                    continue
                sc = score_name(child.name)
                if sc > 0:
                    hits.append({"path": str(child), "layer": "roots", "match": "subdir-name", "score": round(sc, 2)})
                    seen.add(str(child))
        except PermissionError:
            continue
    hits.sort(key=lambda h: h["score"], reverse=True)
    return hits, seen


def scan_cwd(query, base="."):
    """Layer 2: 当前目录向下 BFS，限制深度，收集名字命中的目录。"""
    hits = []
    base_p = Path(base).resolve()
    if not base_p.is_dir():
        return hits
    # BFS
    queue = [(base_p, 0)]
    while queue:
        cur, depth = queue.pop(0)
        if depth > 4:
            continue
        try:
            children = sorted(cur.iterdir())
        except (PermissionError, OSError):
            continue
        for child in children:
            if not ok_dir(child):
                continue
            sc = score_name(child.name)
            if sc > 0:
                hits.append({"path": str(child), "layer": "cwd", "match": "name", "score": round(sc, 2)})
            if depth < 3:
                queue.append((child, depth + 1))
    hits.sort(key=lambda h: h["score"], reverse=True)
    return hits


def scan_chat(query, dirs=None):
    """Layer 3: 在 AI 聊天记录里找提到的项目路径。

    策略：rg/grep 搜出含查询词的 jsonl 行，提取其中形如
    $HOME/.../... 或 ~/... 的绝对路径，过滤出与查询相关的。
    """
    hits = []
    dirs = dirs or DEFAULT_CHAT_DIRS
    rg = shutil.which("rg")
    pat = "|".join(re.escape(t) for t in query_tokens() if t)
    if not pat:
        return hits
    home_re = os.path.expanduser("~").replace("/", r"\/") if os.name != "nt" else r"[A-Za-z]:"
    path_re = re.compile(
        rf"((?:{home_re})/[^\s\"',;)\]}}]+|~/[^\s\"',;)\]}}+]+|/Volumes/[^\s\"',;)\]}}+]+)"
    )
    seen = set()
    for d in dirs:
        d = Path(d)
        if not d.is_dir():
            continue
        files = []
        if rg:
            try:
                out = subprocess.run(
                    [rg, "-l", "-i", pat, "--glob", "*.jsonl", str(d)],
                    capture_output=True, text=True, timeout=60,
                ).stdout.splitlines()
                files = [Path(f) for f in out if f]
            except (subprocess.TimeoutExpired, OSError):
                files = []
        else:
            for f in d.rglob("*.jsonl"):
                files.append(f)
        for f in files[:400]:  # 防超时，最多看 400 个文件
            try:
                for line in f.open(encoding="utf-8", errors="ignore"):
                    if not any(t in line.lower() for t in query_tokens()):
                        continue
                    for m in path_re.findall(line):
                        p = m if not m.startswith("~") else os.path.expanduser(m)
                        p = p.rstrip("/")
                        if p in seen or not ok_dir(p):
                            continue
                        seen.add(p)
                        name = Path(p).name
                        if score_name(name):
                            hits.append({
                                "path": p, "layer": "chat", "match": "chat-path",
                                "evidence": f"提及于 {f.name}",
                                "score": round(score_name(name), 2),
                            })
            except (OSError, UnicodeDecodeError):
                continue
    hits.sort(key=lambda h: h["score"], reverse=True)
    return hits


def scan_full(query):
    """Layer 4: 全盘兜底。先 mdfind 快扫，再 find 慢扫（限制深度）。"""
    hits = []
    seen = set()
    # mdfind
    mdfind = shutil.which("mdfind")
    if mdfind:
        for kw in query_tokens():
            if not kw or len(kw) < 2:
                continue
            try:
                out = subprocess.run(
                    [mdfind, f"kMDItemFSName == '*{kw}*'c"],
                    capture_output=True, text=True, timeout=90,
                ).stdout.splitlines()
            except (subprocess.TimeoutExpired, OSError):
                continue
            for p in out:
                if not ok_dir(p) or p in seen:
                    continue
                seen.add(p)
                name = Path(p).name
                sc = score_name(name)
                if sc > 0:
                    hits.append({"path": p, "layer": "full", "match": "spotlight", "score": round(sc, 2)})
    # find 兜底：从常用根深度有限慢扫
    find = shutil.which("find")
    if find:
        roots = find_roots()
        for root in roots:
            if not root.exists():
                continue
            for kw in query_tokens():
                if not kw or len(kw) < 2:
                    continue
                try:
                    out = subprocess.run(
                        [find, str(root), "-maxdepth", "4", "-iname", f"*{kw}*", "-type", "d"],
                        capture_output=True, text=True, timeout=90,
                    ).stdout.splitlines()
                except (subprocess.TimeoutExpired, OSError):
                    continue
                for p in out:
                    if not ok_dir(p) or p in seen:
                        continue
                    seen.add(p)
                    sc = score_name(Path(p).name)
                    if sc > 0:
                        hits.append({"path": p, "layer": "full", "match": "find", "score": round(sc, 2)})
    hits.sort(key=lambda h: h["score"], reverse=True)
    return hits


def main():
    global _QUERY_raw
    ap = argparse.ArgumentParser(description="分层定位本机项目/源码目录")
    ap.add_argument("query", help="项目名、关键词或特征描述")
    ap.add_argument("--scope", choices=["auto", "roots", "cwd", "chat", "full"],
                    default="auto", help="限定搜索层（默认 auto 逐层推进）")
    ap.add_argument("--cwd", default=".", help="Layer2 起始目录")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--limit", type=int, default=15, help="每层最多输出条数")
    args = ap.parse_args()

    _QUERY_raw = args.query
    if not query_tokens()[0]:
        print(json.dumps({"error": "查询词无效"}, ensure_ascii=False))
        sys.exit(2)

    layers = ["roots", "cwd", "chat", "full"]
    if args.scope != "auto":
        layers = [args.scope]

    all_hits = []
    for layer in layers:
        log(f"[layer:{layer}] 搜索 “{args.query}”…")
        if layer == "roots":
            h, _ = scan_roots(args.query)
        elif layer == "cwd":
            h = scan_cwd(args.query, args.cwd)
        elif layer == "chat":
            h = scan_chat(args.query)
        else:
            h = scan_full(args.query)
        all_hits.extend(h[: args.limit])
        # auto 模式：roots 无命中才继续；其余层一旦有命中即停
        if args.scope == "auto":
            if layer == "roots" and h:
                log(f"[layer:{layer}] 命中 {len(h)} 条，停止更深层搜索")
                break
            if h:
                log(f"[layer:{layer}] 命中 {len(h)} 条，停止更深层搜索")
                break

    result = {
        "query": args.query,
        "scope": args.scope,
        "hits": all_hits,
        "total": len(all_hits),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if not all_hits:
            print("未找到匹配项目。可尝试扩大范围: --scope full")
        else:
            print(f"共 {len(all_hits)} 条候选：")
            for i, h in enumerate(all_hits, 1):
                ev = h.get("evidence", h.get("match", ""))
                print(f"{i:>2}. [{h['layer']:>5}] {h['path']}  (score={h['score']}, {ev})")


if __name__ == "__main__":
    main()
