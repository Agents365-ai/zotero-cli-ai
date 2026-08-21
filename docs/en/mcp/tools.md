# MCP Tools Reference

39 tools organized by category. All tools accept an optional `library` parameter (default: `"user"`). For group libraries use `"group:<id>"`.

## Read Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `search` | Search library by title, author, tag, fulltext; `ranked=True` gives relevance-ranked results (scores + snippets, index-free) | `query`, `collection?`, `item_type?`, `sort?`, `limit`, `ranked?` |
| `list_items` | List all items | `item_type?`, `sort?`, `limit` |
| `read` | Read item details + notes | `key`, `detail?` |
| `pdf` | Extract PDF text | `key`, `pages?` |
| `annotations` | Extract PDF annotations | `key` |
| `references` | Extract parsed bibliography (needs GROBID service) | `key` |
| `tables` | Extract tables from PDF (pdfplumber) | `key` |
| `summarize` | Structured summary for AI | `key` |
| `summarize_all` | Export all items as summaries | `limit` |
| `export` | Export citation (bibtex/csl-json/ris) | `key`, `fmt?` |
| `cite` | Format citation (apa/nature/vancouver) | `key`, `style?` |
| `relate` | Find related items | `key`, `limit?` |
| `recent` | Recently added/modified | `days?`, `modified?`, `limit?` |
| `note_view` | View item notes (or all standalone notes with `standalone=True`) | `key`, `standalone?` |
| `tag_view` | View item tags | `key` |
| `find_orphans` | Find attachments whose file is missing locally | `dead_only?` |
| `collection_list` | List all collections | — |
| `collection_items` | Items in a collection | `collection_key` |
| `duplicates` | Find duplicates | `strategy?`, `threshold?`, `limit?` |
| `stats` | Library statistics | — |
| `update_status` | Check preprint publication status | `key?`, `collection?`, `limit?`, `apply?` |

## Write Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `add` | Add item by DOI or URL | `doi?`, `url?` |
| `add_from_pdf` | Add from local PDF | `file_path`, `doi_override?` |
| `delete` | Delete items (trash) | `keys` |
| `update` | Update metadata | `key`, `title?`, `date?`, `fields?` |
| `attach` | Upload file attachment | `parent_key`, `file_path`, `via_bridge?` |
| `note_add` | Add note to item (Markdown auto-converted to HTML; pass `raw=True` for verbatim; `standalone=True` creates a top-level note) | `key`, `content`, `raw?`, `standalone?` |
| `note_update` | Update existing note (Markdown auto-converted to HTML; pass `raw=True` for verbatim) | `note_key`, `content`, `raw?` |
| `tag_add` | Add tags to items | `keys`, `tags` |
| `tag_remove` | Remove tags from items | `keys`, `tags` |
| `collection_create` | Create collection | `name`, `parent_key?` |
| `collection_move` | Move item to collection | `item_key`, `collection_key` |
| `collection_remove` | Remove item from collection (item stays in library) | `item_key`, `collection_key` |
| `collection_delete` | Delete collection | `collection_key` |
| `collection_rename` | Rename collection | `collection_key`, `new_name` |
| `collection_reorganize` | Batch reorganize | `plan` |
| `trash_list` | List trashed items | `limit?` |
| `trash_restore` | Restore from trash | `key` |

## Ranked Retrieval Tools

Scope retrieval with any Zotero collection — manage membership with the `collection_*` tools above or in the Zotero app. Retrieval is index-free: there is no index to build and results are always fresh. For a plain ranked result list without evidence passages, use `search` with `ranked=True`.

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `ask` | Citation-keyed evidence pack (metadata + PDF passages) plus answer instructions; the agent synthesizes the answer — zot never calls an LLM | `question`, `collection?`, `evidence_k?` |
