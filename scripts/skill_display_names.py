"""Apply catalog display names without changing Skill identity or executable content."""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml


def replace_title(text: str, title: str, accepted: tuple[str, ...] = ()) -> str:
    lines = text.splitlines(keepends=True)
    in_frontmatter = bool(lines and lines[0].strip() == '---')
    fence = None
    for index, line in enumerate(lines):
        if in_frontmatter:
            if index and line.strip() == '---':
                in_frontmatter = False
            continue
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            current = marker.group(1)
            if fence is None:
                fence = current
            elif current[0] == fence[0] and len(current) >= len(fence):
                fence = None
            continue
        if fence is None and re.match(r'^#\s+\S', line):
            if line[2:].strip() in accepted:
                break
            ending = '\r\n' if line.endswith('\r\n') else '\n' if line.endswith('\n') else ''
            lines[index] = f'# {title}{ending}'
            break
    return ''.join(lines)


def update_scalar(text: str, key: str, value: str, indent: str = '') -> str:
    pattern = rf'^{re.escape(indent + key)}:.*$'
    replacement = f'{indent}{key}: {json.dumps(value, ensure_ascii=False)}'
    if re.search(pattern, text, re.M):
        return re.sub(pattern, lambda _: replacement, text, count=1, flags=re.M)
    if not indent:
        return text.rstrip() + '\n' + replacement + '\n'
    return text


def apply_names(root: Path, name_zh: str, display_name: str) -> list[Path]:
    title = f'{name_zh} · {display_name}'
    changed = []
    files = ['SKILL.md', 'README.md', 'README.en.md', 'README.zh-CN.md', 'skill-card.md']
    for relative in files + ['skill.yaml', 'agents/openai.yaml']:
        path = root / relative
        if not path.is_file():
            continue
        original = path.read_text()
        if relative.endswith('.md'):
            suffix = ' · Skill Card' if relative == 'skill-card.md' else ''
            accepted = (display_name,) if relative == 'README.en.md' else (name_zh, title)
            if suffix:
                accepted = tuple(f'{name} Skill Card' for name in accepted)
            updated = replace_title(original, (display_name if relative == 'README.en.md' else title) + suffix, accepted)
        elif relative == 'skill.yaml':
            updated = original
            if re.search(r'^display_name:', original, re.M):
                updated = update_scalar(original, 'display_name', name_zh)
                updated = update_scalar(updated, 'display_name_en', display_name)
        else:
            updated = update_scalar(original, 'display_name', name_zh, '  ')
        if updated != original:
            path.write_text(updated)
            changed.append(path)
    return changed


def read_skill_id(path: Path) -> str | None:
    text = path.read_text()
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.S)
    return (yaml.safe_load(match.group(1)) or {}).get('name') if match else None


def apply_catalog_names(root: Path, skills: list[dict], module_names: dict) -> int:
    by_id = {s.get('runtime_name', s['name']): s for s in skills}
    by_id.update(module_names)
    changed = set()
    for skill in skills:
        if skill.get('test'):
            continue
        folder = root / skill['name']
        if not folder.is_dir():
            continue
        changed.update(apply_names(folder, skill.get('name_zh', skill['name']), skill.get('display_name', skill['name'])))
        for path in folder.glob('skills/**/SKILL.md'):
            names = by_id.get(read_skill_id(path))
            if names:
                changed.update(apply_names(path.parent, names['name_zh'], names['display_name']))
    return len(changed)
