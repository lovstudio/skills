#!/usr/bin/env python3
"""把反馈飞轮接入宿主：托管块写入指令文件，技能链接入技能目录。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

BEGIN_RE = re.compile(r"<!--\s*feedback-loop:begin[^>]*-->")
END_MARKER = "<!-- feedback-loop:end -->"
SKILL_NAME = "lov-feedback-loop"

# 脚本单文件运行时（例如被复制到别处或经 exec 执行）读不到 assets/。
# 这里是同一份托管块的内嵌副本；assets/system-prompt-block.md 仍是真源，
# 两者不一致时以 assets 文件为准（发布前保持同步）。
FALLBACK_BLOCK = """<!-- feedback-loop:begin v1 -->
## 反馈感知与迭代（反馈飞轮）

- 把用户对上一轮结果的态度当作交付信号来读：明确的赞赏、失望、愤怒、反复纠偏、
  无奈或敷衍都要识别；不把沉默当作满意。
- 检测到强度大于等于 3 的信号时，记录一条反馈事件：宿主与会话、时间、用户原话、
  极性、强度、作用域、处置与最终结果；不记录凭据，也不整段转录私人对话。
- 负信号先做最小修复并在原路径回读；可复用反馈写入最窄的规则层
  （任务 → 项目规则 → 技能 → 全局 Prompt），全局规则变化要升版本、校验引用并分发。
- 主动评价（点赞、点踩、表情、评分、显式指令）与被动情绪走同一条闭环；
  闭环结果回填事件，保持可统计。
- 用户要看统计时生成满意度复盘：趋势、未闭环清单与 signal-to-fix 时长。
<!-- feedback-loop:end -->
"""

HOSTS = {
    "codex": {
        "prompt": "~/.codex/AGENTS.md",
        "skills": "~/.codex/skills",
    },
    "claude": {
        "prompt": "~/.claude/CLAUDE.md",
        "skills": "~/.claude/skills",
    },
    "cursor": {
        "prompt": ".cursor/rules/feedback-loop.mdc",
        "skills": "",
    },
    "openclaw": {
        "prompt": "~/.openclaw/workspace/AGENTS.md",
        "skills": "~/.openclaw/workspace/skills",
    },
    "generic": {
        "prompt": "./AGENTS.md",
        "skills": "~/.agents/skills",
    },
}


def expand(value: str) -> Path:
    return Path(value).expanduser()


def kit_root() -> Path:
    return Path(__file__).resolve().parents[1]


def fragment_path() -> Path:
    return kit_root() / "assets" / "system-prompt-block.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def block_digest(block: str) -> str:
    return hashlib.sha256(block.strip().encode("utf-8")).hexdigest()


def normalize_block(text: str) -> str:
    return text.strip() + "\n"


def plan_prompt_merge(target: Path, block: str) -> Dict[str, Any]:
    normalized = normalize_block(block)
    if not target.exists():
        return {
            "action": "create",
            "target": str(target),
            "current_digest": "",
            "block_digest": block_digest(normalized),
            "content": normalized,
            "backup": "",
        }
    current = read_text(target)
    begin = BEGIN_RE.search(current)
    end = current.find(END_MARKER)
    if begin and end != -1 and end > begin.end():
        existing = current[begin.start(): end + len(END_MARKER)]
        if existing.strip() == normalized.strip():
            return {
                "action": "skip",
                "target": str(target),
                "current_digest": block_digest(existing),
                "block_digest": block_digest(normalized),
                "content": "",
                "backup": "",
            }
        merged = current[: begin.start()] + normalized.rstrip("\n") + current[end + len(END_MARKER):]
        return {
            "action": "replace",
            "target": str(target),
            "current_digest": block_digest(existing),
            "block_digest": block_digest(normalized),
            "content": merged,
            "backup": "",
        }
    separator = "\n\n" if current.strip() else ""
    merged = current.rstrip("\n") + separator + normalized
    return {
        "action": "append",
        "target": str(target),
        "current_digest": block_digest(current) if current.strip() else "",
        "block_digest": block_digest(normalized),
        "content": merged,
        "backup": "",
    }


def plan_skill_install(skills_dir: Optional[Path], kit: Path, mode: str) -> Dict[str, Any]:
    if skills_dir is None:
        return {"action": "skip", "target": "", "reason": "该宿主没有默认技能目录"}
    target = skills_dir / SKILL_NAME
    if target.is_symlink():
        resolved = target.resolve()
        if resolved == kit.resolve():
            return {"action": "skip", "target": str(target), "resolved": str(resolved), "mode": "symlink"}
        return {"action": "conflict", "target": str(target), "resolved": str(resolved), "reason": "已指向其他目录", "mode": "symlink"}
    if target.exists():
        return {"action": "conflict", "target": str(target), "resolved": str(target.resolve()), "reason": "目标已存在且不是本 Skill 的软链", "mode": mode}
    return {"action": mode, "target": str(target), "resolved": str(kit.resolve()), "mode": mode}


def plan_store(store: Path) -> Dict[str, Any]:
    config = store / "config.json"
    return {
        "action": "skip" if config.exists() else "create",
        "target": str(store),
        "config": str(config),
    }


def apply_prompt(plan: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    if plan["action"] == "skip" or dry_run:
        return plan
    target = Path(plan["target"])
    if target.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = "{}.bak-{}".format(target, stamp)
        shutil.copy2(target, backup)
        plan["backup"] = backup
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(plan["content"], encoding="utf-8")
    return plan


def apply_skill(plan: Dict[str, Any], kit: Path, dry_run: bool) -> Dict[str, Any]:
    if plan["action"] in ("skip", "conflict") or dry_run:
        return plan
    target = Path(plan["target"])
    target.parent.mkdir(parents=True, exist_ok=True)
    if plan["mode"] == "copy":
        shutil.copytree(
            kit,
            target,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".DS_Store"),
        )
    else:
        target.symlink_to(kit.resolve(), target_is_directory=True)
    return plan


def apply_store(plan: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
    if plan["action"] == "skip" or dry_run:
        return plan
    store = Path(plan["target"])
    store.mkdir(parents=True, exist_ok=True)
    (store / "reports").mkdir(exist_ok=True)
    payload = {
        "schema": "feedback-loop-store/v1",
        "version": "0.1.0",
        "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    Path(plan["config"]).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name in ("events.jsonl", "outcomes.jsonl"):
        (store / name).touch()
    return plan


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="auto", choices=("auto",) + tuple(HOSTS))
    parser.add_argument("--prompt-target", default="", help="显式指定要写入的指令文件")
    parser.add_argument("--skills-dir", default="", help="显式指定技能目录")
    parser.add_argument("--store", default="", help="账本目录，默认 ~/.feedback-loop")
    parser.add_argument("--fragment", default="", help="托管块文件，默认 Skill 内 assets/system-prompt-block.md")
    parser.add_argument("--copy", action="store_true", help="复制而不是软链")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的非本 Skill 目标")
    parser.add_argument("--skip-prompt", action="store_true")
    parser.add_argument("--skip-skills", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="只输出计划，不写任何文件")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    kit = kit_root()
    problems: List[str] = []
    host = args.host
    prompt_value = args.prompt_target
    skills_value = args.skills_dir
    if host == "auto":
        for candidate in ("codex", "claude", "openclaw", "cursor", "generic"):
            prompt_candidate = expand(HOSTS[candidate]["prompt"])
            if prompt_candidate.exists() or prompt_candidate.parent.exists():
                host = candidate
                break
        if host == "auto":
            host = "generic"
    if not prompt_value:
        prompt_value = HOSTS[host]["prompt"]
    if not skills_value:
        skills_value = HOSTS[host]["skills"]

    block_file = Path(args.fragment).expanduser() if args.fragment else fragment_path()
    if block_file.is_file():
        block = read_text(block_file)
    elif args.fragment:
        print("ERROR: 找不到托管块：{}".format(block_file), file=sys.stderr)
        return 1
    else:
        block = FALLBACK_BLOCK
        block_file = Path("<内嵌托管块>")
    if not BEGIN_RE.search(block) or END_MARKER not in block:
        print("ERROR: 托管块缺少 begin/end 标记：{}".format(block_file), file=sys.stderr)
        return 1

    store = Path(args.store).expanduser() if args.store else Path("~/.feedback-loop").expanduser()
    skills_dir = Path(skills_value).expanduser() if skills_value else None

    prompt_plan = None if args.skip_prompt else plan_prompt_merge(Path(prompt_value).expanduser(), block)
    skill_plan = None if args.skip_skills else plan_skill_install(skills_dir, kit, "copy" if args.copy else "symlink")
    if skill_plan and skill_plan["action"] == "conflict" and args.force and not args.dry_run:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = "{}.bak-{}".format(skill_plan["target"], stamp)
        shutil.move(skill_plan["target"], backup)
        skill_plan["backup"] = backup
        skill_plan["action"] = skill_plan["mode"]
    store_plan = plan_store(store)

    result: Dict[str, Any] = {
        "ok": True,
        "host": host,
        "dry_run": bool(args.dry_run),
        "kit_root": str(kit),
        "fragment": str(block_file),
        "block_sha256": block_digest(block),
        "prompt": prompt_plan,
        "skills": skill_plan,
        "store": store_plan,
        "actions": [],
        "problems": problems,
    }

    if prompt_plan:
        apply_prompt(prompt_plan, args.dry_run)
        result["actions"].append("prompt:{}:{}".format(prompt_plan["action"], prompt_plan["target"]))
    if skill_plan:
        if skill_plan["action"] == "conflict":
            result["ok"] = False
            problems.append("技能目录冲突：{}（用 --force 备份后覆盖）".format(skill_plan.get("target", "")))
        else:
            apply_skill(skill_plan, kit, args.dry_run)
            result["actions"].append("skills:{}:{}".format(skill_plan["action"], skill_plan["target"]))
    apply_store(store_plan, args.dry_run)
    result["actions"].append("store:{}:{}".format(store_plan["action"], store_plan["target"]))

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("host={} dry_run={}".format(host, str(bool(args.dry_run)).lower()))
        print("fragment={}".format(block_file))
        print("block_sha256={}".format(result["block_sha256"]))
        if prompt_plan:
            print("prompt_action={} target={} backup={}".format(prompt_plan["action"], prompt_plan["target"], prompt_plan.get("backup", "") or "-"))
        if skill_plan:
            print("skills_action={} target={} mode={}".format(skill_plan["action"], skill_plan.get("target", "-"), skill_plan.get("mode", "-")))
        print("store_action={} target={}".format(store_plan["action"], store_plan["target"]))
        if problems:
            for problem in problems:
                print("PROBLEM: {}".format(problem))
        print("verify=readlink -f {} && grep -c 'feedback-loop:begin' {}".format(Path(skill_plan["target"]) if skill_plan and skill_plan.get("target") else "-", prompt_plan["target"] if prompt_plan else "-"))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
