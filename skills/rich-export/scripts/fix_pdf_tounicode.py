#!/usr/bin/env python3
"""把 Chrome 导出 PDF 文字层里的部首码位改回汉字（原地改写，页面显示不变）。

Chrome（Skia）给每个字形只写一个 Unicode，取字体 cmap 里最小的码位。PingFang、Songti、Hiragino、
Noto Sans SC 等中文字体让部首（U+2F00–U+2FD5、U+2E80–U+2EF3）与对应汉字共用字形，于是正文「手工川」
在文字层里成了「⼿⼯川」，复制、搜索都会出错。这里只改写各字体的 ToUnicode CMap，不动页面内容。

对照表按字体推：用 PDF 里的字体名找到本机字体文件，取 cmap 里与该字形共用的统一汉字。各字体的共用关系
不一致（⼾ 在 PingFang 里是「戶」、在 Noto Sans SC 里是「户」），不能共用一张表；找不到字体文件
（如网页字体）时退回 PingFang 的对照表，再用 NFKC 补齐康熙部首。

用法：python3 fix_pdf_tounicode.py a.pdf [b.pdf ...]；改完仍有部首码位时退出码为 1。
"""
import argparse
import functools
import os
import re
import sys
import unicodedata

from fontTools.ttLib import TTCollection, TTFont
from pypdf import PdfReader, PdfWriter

FONT_DIRS = [
    '/System/Library/Fonts', '/System/Library/AssetsV2', '/Library/Fonts', '~/Library/Fonts',
    '/usr/share/fonts', '/usr/local/share/fonts', '~/.local/share/fonts', '~/.fonts',
    'C:/Windows/Fonts', '~/AppData/Local/Microsoft/Windows/Fonts',
]


def is_han(cp):
    return 0x3400 <= cp <= 0x4DBF or 0x4E00 <= cp <= 0x9FFF or 0x20000 <= cp <= 0x3FFFF


def is_radical(ch):
    return 0x2E80 <= ord(ch) <= 0x2FDF


@functools.lru_cache(maxsize=None)
def font_index():
    """PostScript 名 → (字体文件, TTC 序号)。"""
    index = {}
    for top in FONT_DIRS:
        for root, _, names in os.walk(os.path.expanduser(top)):
            for name in names:
                if not name.lower().endswith(('.ttf', '.otf', '.ttc')):
                    continue
                path = os.path.join(root, name)
                try:
                    faces = TTCollection(path, lazy=True).fonts if name.lower().endswith('.ttc') else [TTFont(path, lazy=True)]
                    for number, face in enumerate(faces):
                        postscript = face['name'].getDebugName(6)
                        if postscript:
                            index.setdefault(postscript, (path, number))
                except Exception:  # 损坏或不支持的字体文件直接跳过
                    continue
    return index


def cmap_map(path, number):
    """与统一汉字共用字形、码位又比它小的字符 → 该汉字。"""
    by_glyph = {}
    for cp, glyph in (TTFont(path, fontNumber=number, lazy=True).getBestCmap() or {}).items():
        by_glyph.setdefault(glyph, []).append(cp)
    mapping = {}
    for cps in by_glyph.values():
        han = [cp for cp in cps if is_han(cp)]
        if han:
            mapping.update((cp, min(han)) for cp in cps if cp < min(han))
    return mapping


@functools.lru_cache(maxsize=None)
def fallback_map():
    found = font_index().get('PingFangSC-Regular')
    mapping = cmap_map(*found) if found else {}
    for cp in range(0x2F00, 0x2FD6):
        mapping.setdefault(cp, ord(unicodedata.normalize('NFKC', chr(cp))))
    return mapping


@functools.lru_cache(maxsize=None)
def font_map(name):
    found = font_index().get(name)
    return cmap_map(*found) if found else fallback_map()


def font_name(font):
    descriptor = font.get('/FontDescriptor')
    raw = font.get('/BaseFont') or (descriptor.get_object().get('/FontName') if descriptor is not None else '')
    # 去掉子集前缀 ABCDEF+，以及 Skia 给可变字体实例加的 _Bold 一类后缀
    return re.sub(r'^[A-Z]{6}\+', '', str(raw).lstrip('/')).split('_')[0]


def utf16(cp):
    return chr(cp).encode('utf-16-be').hex().upper()


def parse(text):
    m = {}
    for block in re.finditer(r'beginbfchar(.*?)endbfchar', text, re.S):
        for src, dst in re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]*)>', block.group(1)):
            m[src.upper()] = dst.upper()
    for block in re.finditer(r'beginbfrange(.*?)endbfrange', text, re.S):
        for lo, hi, rest in re.findall(r'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(\[[^\]]*\]|<[0-9A-Fa-f]*>)', block.group(1)):
            a, b, w = int(lo, 16), int(hi, 16), len(lo)
            if rest.startswith('['):
                for k, d in enumerate(re.findall(r'<([0-9A-Fa-f]*)>', rest)):
                    m[f'{a + k:0{w}X}'] = d.upper()
            else:
                d = rest[1:-1]
                for k in range(b - a + 1):
                    m[f'{a + k:0{w}X}'] = f'{int(d, 16) + k:0{len(d)}X}'
    return m


def rewrite(text, mapping):
    m = parse(text)
    fixed = 0
    for src, dst in m.items():
        if len(dst) == 4 and int(dst, 16) in mapping:
            m[src] = utf16(mapping[int(dst, 16)])
            fixed += 1
    if not fixed:
        return text, 0
    first = re.search(r'\d+\s+begin(?:bfchar|bfrange)', text)
    last = list(re.finditer(r'end(?:bfchar|bfrange)', text))[-1]
    items = sorted(m.items(), key=lambda kv: int(kv[0], 16))
    blocks = []
    for i in range(0, len(items), 100):
        chunk = items[i : i + 100]
        blocks.append(f'{len(chunk)} beginbfchar\n' + '\n'.join(f'<{s}> <{d}>' for s, d in chunk) + '\nendbfchar')
    return text[: first.start()] + '\n'.join(blocks) + text[last.end() :], fixed


def resolve(x):
    return x.get_object() if hasattr(x, 'get_object') else x


def fonts_in(resources, seen=None):
    seen = set() if seen is None else seen
    if not resources:
        return
    resources = resolve(resources)
    for ref in resolve(resources.get('/Font') or {}).values():
        yield resolve(ref)
    for ref in resolve(resources.get('/XObject') or {}).values():
        xo = resolve(ref)
        if xo.get('/Subtype') == '/Form' and id(xo) not in seen:
            seen.add(id(xo))
            yield from fonts_in(xo.get('/Resources'), seen)


def radicals_left(path):
    text = ''.join(p.extract_text() or '' for p in PdfReader(path).pages)
    return sum(1 for ch in text if is_radical(ch))


def fix(path):
    """原地修复一个 PDF，返回（改写的字形映射数, 文字层剩余部首码位数, 退回默认对照表的字体名）。"""
    writer = PdfWriter(clone_from=PdfReader(path))
    done, fallback, total = set(), set(), 0
    for page in writer.pages:
        for font in fonts_in(page.get('/Resources')):
            ref = font.get('/ToUnicode')
            if ref is None:
                continue
            key = getattr(ref, 'idnum', None) or id(ref)
            if key in done:
                continue
            done.add(key)
            name = font_name(font)
            stream = ref.get_object()
            new, n = rewrite(stream.get_data().decode('latin-1'), font_map(name))
            if n:
                stream.set_data(new.encode('latin-1'))
                total += n
                if name not in font_index():
                    fallback.add(name)
    if total:
        tmp = f'{path}.tmp'
        with open(tmp, 'wb') as fh:
            writer.write(fh)
        os.replace(tmp, path)
    return total, radicals_left(path), sorted(fallback)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('pdf', nargs='+', help='要原地修复的 PDF')
    failed = False
    for p in parser.parse_args().pdf:
        total, left, fallback = fix(p)
        note = f' (fallback map for: {", ".join(fallback)})' if fallback else ''
        print(f'tounicode: {os.path.basename(p)} fixed {total} glyph mappings, radicals left in text {left}{note}')
        failed |= left > 0
    sys.exit(1 if failed else 0)
