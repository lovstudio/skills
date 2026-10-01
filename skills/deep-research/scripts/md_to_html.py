#!/usr/bin/env python3
"""
Markdown to HTML converter for research reports
Properly converts markdown sections to HTML while preserving structure and formatting
"""

import argparse
import base64
import html as html_lib
import mimetypes
import re
from typing import Optional, Tuple
from pathlib import Path


def convert_markdown_to_html(
    markdown_text: str,
    base_dir: Optional[Path] = None,
    embed_images: bool = False,
) -> Tuple[str, str]:
    """
    Convert markdown to HTML in two parts: content and bibliography

    Args:
        markdown_text: Full markdown report text
        base_dir: Directory that relative figure paths resolve against
        embed_images: Inline local figures as data URIs for self-contained HTML

    Returns:
        Tuple of (content_html, bibliography_html)
    """
    # Split content and bibliography
    # Accept English or Chinese bibliography headings.
    parts = re.split(r'##\s*(?:Bibliography|References|参考文献)[^\n]*\n', markdown_text, maxsplit=1)
    content_md = parts[0]
    bibliography_md = parts[1] if len(parts) > 1 else ""

    # Convert content (everything except bibliography)
    content_html = _convert_content_section(content_md, base_dir, embed_images)

    # Convert bibliography separately
    bibliography_html = _convert_bibliography_section(bibliography_md)

    return content_html, bibliography_html


def _convert_content_section(
    markdown: str,
    base_dir: Optional[Path] = None,
    embed_images: bool = False,
) -> str:
    """Convert main content sections to HTML"""
    html = markdown

    # Remove title and front matter (first ## heading is handled separately)
    lines = html.split('\n')
    processed_lines = []
    skip_until_first_section = True

    for line in lines:
        # Skip everything until we hit "## Executive Summary" or first major section
        if skip_until_first_section:
            if line.startswith('## ') and not line.startswith('### '):
                skip_until_first_section = False
                processed_lines.append(line)
            continue
        processed_lines.append(line)

    html = '\n'.join(processed_lines)

    # Convert headers
    # ## Section Title → <div class="section"><h2 class="section-title">Section Title</h2></div>
    html = re.sub(
        r'^## (.+)$',
        r'<div class="section"><h2 class="section-title">\1</h2>',
        html,
        flags=re.MULTILINE
    )

    # ### Subsection → <h3 class="subsection-title">Subsection</h3>
    html = re.sub(
        r'^### (.+)$',
        r'<h3 class="subsection-title">\1</h3>',
        html,
        flags=re.MULTILINE
    )

    # #### Subsubsection → <h4 class="subsubsection-title">Title</h4>
    html = re.sub(
        r'^#### (.+)$',
        r'<h4 class="subsubsection-title">\1</h4>',
        html,
        flags=re.MULTILINE
    )

    # Convert figures (image line + optional caption line) before inline
    # emphasis, so captions written as *图 N：...* are not split apart.
    html = _convert_figures(html, base_dir, embed_images)

    # Convert **bold** text
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

    # Convert *italic* text
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

    # Convert inline code `code`
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)

    # Convert direct HTTP(S) links before tables and paragraphs so repository
    # links remain clickable inside the Open-Source Solutions Landscape.
    html = _convert_inline_links(html)

    # Convert unordered lists
    html = _convert_lists(html)

    # Convert tables
    html = _convert_tables(html)

    # Convert paragraphs (wrap non-HTML lines in <p> tags)
    html = _convert_paragraphs(html)

    # Close all open sections
    html = _close_sections(html)

    # Wrap executive summary if present
    html = html.replace(
        '<h2 class="section-title">Executive Summary</h2>',
        '<div class="executive-summary"><h2 class="section-title">Executive Summary</h2>'
    )
    if '<div class="executive-summary">' in html:
        # Close executive summary at the next section
        html = html.replace(
            '</h2>\n<div class="section">',
            '</h2></div>\n<div class="section">',
            1
        )

    return html


FIGURE_LINE = re.compile(r'^!\[([^\]]*)\]\(([^)\s]+)\)\s*$')
CAPTION_LINE = re.compile(r'^\*?((?:图|表|Figure|Fig\.|Table)\s*\d+[^\n]*?)\*?\s*$')


def _is_safe_image_src(src: str) -> bool:
    """Allow relative paths and https URLs; reject javascript:, data:, file: and the like."""
    if src.startswith('https://'):
        return True
    return not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', src) and not src.startswith('//')


def _embed_src(src: str, base_dir: Optional[Path]) -> str:
    """Return a data URI for a local figure, or the original src when it cannot be read."""
    if base_dir is None or src.startswith('https://'):
        return src
    path = (base_dir / src).resolve()
    if not path.is_file():
        return src
    mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    data = base64.b64encode(path.read_bytes()).decode('ascii')
    return f'data:{mime};base64,{data}'


def _convert_figures(html: str, base_dir: Optional[Path] = None, embed_images: bool = False) -> str:
    """Turn a standalone image line plus an optional caption line into <figure>."""
    lines = html.split('\n')
    result = []
    i = 0
    while i < len(lines):
        match = FIGURE_LINE.match(lines[i].strip())
        if not match or not _is_safe_image_src(match.group(2)):
            result.append(lines[i])
            i += 1
            continue
        alt, src = match.group(1), match.group(2)
        caption = ''
        j = i + 1
        while j < len(lines) and not lines[j].strip() and j - i <= 2:
            j += 1
        if j < len(lines):
            cap = CAPTION_LINE.match(lines[j].strip())
            if cap:
                caption = cap.group(1).strip()
                i = j
        if embed_images:
            src = _embed_src(src, base_dir)
        caption_html = f'<figcaption>{html_lib.escape(caption or alt)}</figcaption>' if (caption or alt) else ''
        result.append(
            f'<figure class="report-figure"><img src="{html_lib.escape(src, quote=True)}" '
            f'alt="{html_lib.escape(alt, quote=True)}" loading="lazy">{caption_html}</figure>'
        )
        i += 1
    return '\n'.join(result)


def _convert_inline_links(html: str) -> str:
    """Convert Markdown HTTP(S) links while leaving other URI schemes inert."""
    return re.sub(
        r'\[([^\]]+)\]\((https?://[^\s)]+)\)',
        r'<a href="\2" target="_blank" rel="noreferrer">\1</a>',
        html,
    )


def _convert_bibliography_section(markdown: str) -> str:
    """Convert bibliography section to HTML"""
    if not markdown.strip():
        return ""

    html = markdown

    # Convert each [N] citation to a proper bibliography entry
    # Look for patterns like [1] Title - URL
    html = re.sub(
        r'\[(\d+)\]\s*(.+?)\s*-\s*(https?://[^\s\)]+)',
        r'<div class="bib-entry"><span class="bib-number">[\1]</span> <a href="\3" target="_blank">\2</a></div>',
        html
    )

    # Convert any remaining **bold** sections
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

    # Wrap in bibliography content div
    html = f'<div class="bibliography-content">{html}</div>'

    return html


def _convert_lists(html: str) -> str:
    """Convert markdown lists to HTML lists"""
    lines = html.split('\n')
    result = []
    in_list = False
    list_level = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Check for unordered list item
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                result.append('<ul>')
                in_list = True
                list_level = len(line) - len(line.lstrip())

            # Get the content after the marker
            content = stripped[2:]
            result.append(f'<li>{content}</li>')

        # Check for ordered list item
        elif re.match(r'^\d+\.\s', stripped):
            if not in_list:
                result.append('<ol>')
                in_list = True
                list_level = len(line) - len(line.lstrip())

            # Get the content after the number and period
            content = re.sub(r'^\d+\.\s', '', stripped)
            result.append(f'<li>{content}</li>')

        else:
            # Not a list item
            if in_list:
                # Check if we're still in the list (indented continuation)
                current_level = len(line) - len(line.lstrip())
                if current_level > list_level and stripped:
                    # Continuation of previous list item
                    if result[-1].endswith('</li>'):
                        result[-1] = result[-1][:-5] + ' ' + stripped + '</li>'
                    continue
                else:
                    # End of list
                    result.append('</ul>' if '<ul>' in '\n'.join(result[-10:]) else '</ol>')
                    in_list = False
                    list_level = 0

            result.append(line)

    # Close any remaining open list
    if in_list:
        result.append('</ul>' if '<ul>' in '\n'.join(result[-10:]) else '</ol>')

    return '\n'.join(result)


def _convert_tables(html: str) -> str:
    """Convert markdown tables to HTML tables"""
    lines = html.split('\n')
    result = []
    in_table = False

    for i, line in enumerate(lines):
        if '|' in line and line.strip().startswith('|'):
            if not in_table:
                result.append('<table>')
                in_table = True
                # This is the header row
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                result.append('<thead><tr>')
                for cell in cells:
                    result.append(f'<th>{cell}</th>')
                result.append('</tr></thead>')
                result.append('<tbody>')
            elif '---' in line:
                # Skip separator row
                continue
            else:
                # Data row
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                result.append('<tr>')
                for cell in cells:
                    result.append(f'<td>{cell}</td>')
                result.append('</tr>')
        else:
            if in_table:
                result.append('</tbody></table>')
                in_table = False
            result.append(line)

    if in_table:
        result.append('</tbody></table>')

    return '\n'.join(result)


def _convert_paragraphs(html: str) -> str:
    """Wrap non-HTML lines in paragraph tags"""
    lines = html.split('\n')
    result = []
    in_paragraph = False

    for line in lines:
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            if in_paragraph:
                result.append('</p>')
                in_paragraph = False
            result.append(line)
            continue

        # Skip lines that are already HTML tags
        if (stripped.startswith('<') and stripped.endswith('>')) or \
           stripped.startswith('</') or \
           '<h' in stripped or '<div' in stripped or '<ul' in stripped or \
           '<ol' in stripped or '<li' in stripped or '<table' in stripped or \
           '<figure' in stripped or \
           '</div>' in stripped or '</ul>' in stripped or '</ol>' in stripped:
            if in_paragraph:
                result.append('</p>')
                in_paragraph = False
            result.append(line)
            continue

        # Regular text line - wrap in paragraph
        if not in_paragraph:
            result.append('<p>' + line)
            in_paragraph = True
        else:
            result.append(line)

    if in_paragraph:
        result.append('</p>')

    return '\n'.join(result)


def _close_sections(html: str) -> str:
    """Close all open section divs"""
    # Count open and closed divs
    open_divs = html.count('<div class="section">')
    closed_divs = html.count('</div>')

    # Add closing divs for sections
    # Each section should be closed before the next section starts
    lines = html.split('\n')
    result = []
    section_open = False

    for i, line in enumerate(lines):
        if '<div class="section">' in line:
            if section_open:
                result.append('</div>')  # Close previous section
            section_open = True
        result.append(line)

    # Close final section if still open
    if section_open:
        result.append('</div>')

    return '\n'.join(result)


def main():
    """Convert a report and print the content and bibliography fragments."""
    parser = argparse.ArgumentParser(description="Convert a research Markdown report to HTML fragments")
    parser.add_argument("markdown_file", type=Path, help="Path to the Markdown report")
    parser.add_argument(
        "--embed-images",
        action="store_true",
        help="Inline local figures as data URIs so the HTML is self-contained",
    )
    args = parser.parse_args()

    md_file = args.markdown_file
    if not md_file.exists():
        parser.error(f"file not found: {md_file}")

    markdown_text = md_file.read_text()
    content_html, bib_html = convert_markdown_to_html(
        markdown_text, base_dir=md_file.parent, embed_images=args.embed_images
    )

    print("=== CONTENT HTML ===")
    print(content_html[:1000])
    print("\n=== BIBLIOGRAPHY HTML ===")
    print(bib_html[:500])


if __name__ == "__main__":
    main()
