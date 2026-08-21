# Notes & Tags

## View Notes

```bash
zot note ABC123
```

Displays all notes attached to an item, converted from HTML to Markdown.

## Add a Note

```bash
zot note ABC123 --add "This paper proposes a new attention mechanism"
```

!!! note "Write operations require API credentials"
    See [Setup](../getting-started/setup.md#api-credentials) to configure your API key.

### Markdown handling

Zotero stores notes as HTML, so `--add` converts Markdown to HTML before submitting:

- YAML frontmatter (`--- ... ---`) at the top of the note is stripped.
- Obsidian callouts (`> [!type] text`) become blockquotes with the text in bold.
- Headings, emphasis, lists, links, code, and tables render as Zotero formatting.

Pass `--raw` to store the content verbatim (e.g. when you already have HTML):

```bash
zot note ABC123 --add "<p>Already <strong>HTML</strong>.</p>" --raw
```

!!! warning "Do not POST raw `**` Markdown"
    The Zotero API escapes Markdown emphasis it does not interpret: posting `**bold**` stores `\*\*bold\*\*`, which Zotero renders as literal text. Always let `--add` convert, or pass `--raw` with HTML.

### Standalone (top-level) notes

Standalone notes have no parent item and appear at the top level of the library. Create and list them with `--standalone` (no `KEY`):

```bash
zot note --standalone --add "Key finding: ..."   # create a standalone note
zot note --standalone                            # list all standalone notes
zot note STANKEY                                 # read a standalone note by its key
```

The same Markdown handling (conversion, `--raw`, `--dry-run`) applies to standalone notes.

## Update a Note

Notes can be updated via the MCP tools (`note_update`). See [MCP Tools Reference](../mcp/tools.md).

## View Tags

```bash
zot tag ABC123
```

## Add Tags

```bash
zot tag ABC123 --add "important"
zot tag ABC123 --add "to-read" --add "attention"
```

## Remove Tags

```bash
zot tag ABC123 --remove "to-read"
```

## Batch Tag Operations

Tags can be added to or removed from multiple items at once via MCP tools (`tag_add`, `tag_remove`). See [MCP Tools Reference](../mcp/tools.md).
