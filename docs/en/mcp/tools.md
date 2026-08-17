# MCP Tools Reference

39 tools organized by category. All tools accept an optional `library` parameter (default: `"user"`). For group libraries use `"group:<id>"`.

## Read Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `search` | Search library by title, author, tag, fulltext | `query`, `collection?`, `item_type?`, `sort?`, `limit` |
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
| `note_view` | View item notes | `key` |
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
| `note_add` | Add note to item | `key`, `content` |
| `note_update` | Update existing note | `note_key`, `content` |
| `tag_add` | Add tags to items | `keys`, `tags` |
| `tag_remove` | Remove tags from items | `keys`, `tags` |
| `collection_create` | Create collection | `name`, `parent_key?` |
| `collection_move` | Move item to collection | `item_key`, `collection_key` |
| `collection_delete` | Delete collection | `collection_key` |
| `collection_rename` | Rename collection | `collection_key`, `new_name` |
| `collection_reorganize` | Batch reorganize | `plan` |
| `trash_list` | List trashed items | `limit?` |
| `trash_restore` | Restore from trash | `key` |

## Workspace Tools

A workspace is a Zotero collection — manage membership with the `collection_*` tools above or in the Zotero app. Retrieval is index-free: there is no index to build and results are always fresh.

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `workspace_query` | Rank papers by relevance to a question (returns ranked items with snippets) | `question`, `workspace?`, `top_k?` |
| `ask` | Citation-keyed evidence pack (metadata + PDF passages) plus answer instructions; the agent synthesizes the answer — zot never calls an LLM | `question`, `workspace?`, `evidence_k?` |
