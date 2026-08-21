"""Unit tests for core.markdown (Zotero note write-path conversion)."""

from zotero_cli_cc.core.markdown import (
    convert_obsidian_callouts,
    md_to_zotero_html,
    strip_yaml_frontmatter,
)


class TestStripYamlFrontmatter:
    def test_strips_frontmatter(self):
        md = "---\ntitle: My paper\ntags: [cd]\n---\n# Heading"
        assert strip_yaml_frontmatter(md) == "# Heading"

    def test_strips_crlf_frontmatter(self):
        md = "---\r\ntitle: x\r\n---\r\n# H"
        assert strip_yaml_frontmatter(md) == "# H"

    def test_strips_end_dot_fence(self):
        md = "---\ntitle: x\n...\n# H"
        assert strip_yaml_frontmatter(md) == "# H"

    def test_keeps_missing_key_value(self):
        # A leading `---` that is a horizontal rule, not frontmatter.
        md = "---\nsome text\n---"
        assert strip_yaml_frontmatter(md) == md

    def test_keeps_plain_note(self):
        md = "Just a note.\n"
        assert strip_yaml_frontmatter(md) == md


class TestConvertObsidianCallouts:
    def test_callout_with_title(self):
        assert convert_obsidian_callouts("> [!note] 核心发现:重点\n> 正文") == "> **核心发现:重点**\n> 正文"

    def test_callout_without_title(self):
        assert convert_obsidian_callouts("> [!warning]\n> body") == "> **warning**\n> body"

    def test_leaves_plain_blockquote(self):
        assert convert_obsidian_callouts("> normal quote") == "> normal quote"


class TestMdToZoteroHtml:
    def test_emphasis_and_heading(self):
        out = md_to_zotero_html("# H\n**bold** *italic*")
        assert "<h1>H</h1>" in out
        assert "<strong>bold</strong>" in out
        assert "<em>italic</em>" in out

    def test_no_backslash_escaped_asterisks(self):
        out = md_to_zotero_html("**bold**")
        assert "\\*" not in out

    def test_strips_frontmatter_and_callout(self):
        out = md_to_zotero_html("---\ntitle: x\n---\n> [!note] 重点\n> 正文")
        assert "title: x" not in out
        assert "[!note]" not in out
        assert "<strong>重点</strong>" in out

    def test_table_renders(self):
        out = md_to_zotero_html("| a | b |\n|---|---|\n| 1 | 2 |")
        assert "<table>" in out
        assert "<th>a</th>" in out

    def test_html_passthrough(self):
        html = '<div class="zotero-note"><p><strong>y</strong></p></div>'
        assert md_to_zotero_html(html) == html

    def test_html_passthrough_with_leading_space(self):
        html = "  <p>x</p>"
        assert md_to_zotero_html(html) == html

    def test_plain_text_becomes_paragraph(self):
        assert md_to_zotero_html("hello world") == "<p>hello world</p>"

    def test_empty(self):
        assert md_to_zotero_html("") == ""
