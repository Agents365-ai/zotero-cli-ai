# Quickstart

After [installing](installation.md) zot, you can immediately search and read papers.

## 1. Search Your Library

```bash
zot search "transformer attention"
```

This searches across titles, authors, tags, and full-text PDF index.

## 2. Read a Paper

From the search results, pick an item key (e.g. `ABC123`):

```bash
zot read ABC123
```

This shows the full metadata, abstract, and notes.

## 3. Extract PDF Text

```bash
zot pdf ABC123
```

Extracts the full text from the paper's PDF attachment. Use `--pages 1-5` for specific pages.

## JSON Output for AI

Add `--json` to any command for machine-readable output:

```bash
zot --json search "single cell RNA"
```

This is what Claude Code uses behind the scenes when you ask it about papers.

## Using with Claude Code

Install the zotero-cli skill so Claude Code automatically recognizes literature-related requests:

```bash
cp -r skill/zotero-cli ~/.claude/skills/
```

Then in any Claude Code session, use natural language:

```
Search my Zotero for single cell papers
→ Claude runs: zot --json search "single cell"

Show me details of this paper
→ Claude runs: zot --json read ABC123
```

## Next Steps

- [User Guide](../guide/search.md) — Full command reference
- [MCP Server](../mcp/setup.md) — Use with Claude Desktop, Cursor, LM Studio
- [Workspaces](../guide/workspace.md) — Ranked natural-language search over your collections, no index to build
