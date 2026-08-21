"""Markdown helpers for the Zotero note write path.

Zotero stores notes as HTML (``itemNotes.note``) and the Web API round-trips
HTML verbatim, but treats content with no HTML tags as plain text and
server-converts it, escaping markdown metacharacters it does not interpret
(e.g. ``**bold**`` is stored as ``\\*\\*bold\\*\\*`` and rendered literally).
To get correct rendering, ``zot note --add`` converts the caller's markdown
to HTML before POSTing. These helpers strip Obsidian-only syntax (YAML
frontmatter, callouts) and render the rest with markdown-it (CommonMark).
"""

from __future__ import annotations

import re

from markdown_it import MarkdownIt

_RENDERER = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"])

# Leading `--- ... ---` (or `...`) block. Only a *closing* fence is matched;
# whether to strip at all is decided in strip_yaml_frontmatter.
_FRONTMATTER_RE = re.compile(
    r"\A---[ \t]*\r?\n"
    r"(?P<body>.*?)"
    r"\r?\n(?:---|\.\.\.)[ \t]*(?:\r?\n|\Z)",
    re.DOTALL,
)

_CALLOUT_RE = re.compile(r"^>\s*\[!([A-Za-z][A-Za-z0-9_-]*)\]\s*(.*)$")


def strip_yaml_frontmatter(md: str) -> str:
    """Drop a leading YAML frontmatter block, if present.

    Follows Obsidian's rule: the block must start the document and contain at
    least one ``key: value`` pair. A note that merely opens with a horizontal
    rule (``---`` alone) is left untouched.
    """
    m = _FRONTMATTER_RE.match(md)
    if m is None:
        return md
    if not re.search(r"^\s*\S+\s*:", m.group("body"), re.M):
        return md
    return md[m.end() :]


def convert_obsidian_callouts(md: str) -> str:
    """Lower Obsidian callout markers to bold blockquote labels.

    ``> [!type] rest`` becomes ``> **rest**`` (or ``> **type**`` when there is
    no rest), keeping any following ``> body`` lines as normal blockquote
    lines. Zotero has no callout concept, so the marker must not survive as
    literal text.
    """
    out: list[str] = []
    for line in md.split("\n"):
        m = _CALLOUT_RE.match(line)
        if m is None:
            out.append(line)
            continue
        label = m.group(2).strip() or m.group(1)
        out.append(f"> **{label}**")
    return "\n".join(out)


def md_to_zotero_html(md: str) -> str:
    """Convert markdown to HTML for Zotero's note field.

    Content that already starts with ``<`` is treated as HTML and returned
    unchanged (the MCP tools accept HTML or markdown). Anything else is
    treated as markdown: YAML frontmatter is stripped, Obsidian callouts are
    lowered to bold blockquotes, and the remainder is rendered to HTML.
    """
    if md.lstrip().startswith("<"):
        return md
    prepared = convert_obsidian_callouts(strip_yaml_frontmatter(md))
    return str(_RENDERER.render(prepared)).strip()
