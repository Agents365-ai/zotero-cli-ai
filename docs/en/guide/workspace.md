# Workspaces

A workspace is simply a Zotero collection. There is nothing to create inside zot and nothing stored locally — curate the collection in the Zotero app (or via `zot collection *`), and zot queries it live. There is no index to build, so results are always fresh.

## Manage Membership

Organize papers in the Zotero app, or from the CLI:

```bash
zot collection list                        # All collections (names + keys)
zot collection items COLL_KEY              # Items in a collection
zot collection create "LLM Safety"         # Create a collection (needs API key)
zot collection move ITEM_KEY COLL_KEY      # Add an item to a collection
zot collection rename COLL_KEY "New Name"  # Rename
zot collection delete COLL_KEY             # Delete a collection
zot collection reorganize plan.json        # Batch create + move from a JSON plan
```

## Ranked Search

`zot workspace query` ranks papers by relevance to a natural-language question:

```bash
zot workspace query "reward hacking methods"
zot workspace query "reward hacking methods" --workspace "LLM Safety"
zot workspace query "tumour immunity" --workspace "CR | HCC" --top-k 10
```

- `--workspace` scopes the search to a collection (name or key). Omit it to search the whole library.
- `--top-k` sets the number of results (default: 5).

Retrieval is index-free: items are scored with idf-weighted term coverage from Zotero's own full-text index tables (the same index the Zotero app builds), fused with metadata matching (title/abstract/creators/tags/notes) via reciprocal rank fusion. A paper added to the collection a second ago is already searchable.

JSON output:

```json
{
  "ok": true,
  "data": {
    "query": "reward hacking methods",
    "workspace": "LLM Safety",
    "results": [
      {
        "rank": 1,
        "score": 0.0328,
        "scores": { "rrf": 0.0328, "fulltext": 4.5612, "metadata": 2.0 },
        "item_key": "ABC123",
        "title": "...",
        "creators": ["..."],
        "date": "2024",
        "snippet": "..."
      }
    ]
  }
}
```

## Evidence Packs

`zot ask` goes one step further: after ranking, it extracts PDF passages around the query terms on the fly (pdfium, cached) and returns a citation-keyed evidence pack. zot never calls an LLM — the calling agent synthesizes a grounded answer from the evidence.

```bash
zot ask "how does attention scale?"
zot ask "what dataset was used?" --workspace papers --evidence-k 8
```

- `--workspace` scopes retrieval to a collection (name or key). Omit it for the whole library.
- `--evidence-k` sets the number of evidence entries (default: 12).

JSON output:

```json
{
  "ok": true,
  "data": {
    "question": "what dataset was used?",
    "workspace": "papers",
    "mode": "index-free",
    "evidence": [
      { "cite_key": "ABC123", "source": "metadata", "text": "Title: ...", "scores": { "rrf": 0.0328, "fulltext": 4.5612, "metadata": 2.0 } },
      { "cite_key": "ABC123", "source": "pdf", "text": "...passage around the query terms...", "scores": { "rrf": 0.0328, "fulltext": 4.5612, "metadata": 2.0 } }
    ],
    "answer_instructions": "Answer the question using ONLY the evidence below. Cite each claim with its cite_key in parentheses, e.g. (ABCD1234). ..."
  }
}
```

## Migrating from Earlier Versions

Earlier versions kept local workspaces under `~/.config/zot/workspaces/` (JSON files plus a `*.idx.sqlite` BM25/embedding index) with their own subcommands (`workspace new/add/remove/list/show/export/import/search/index/delete`) and optional embedding providers (`[embedding]` in `config.toml`, `ZOT_EMBEDDING_*` environment variables). All of that has been removed — the old files are unused and can be deleted.

To migrate, recreate the same paper sets as Zotero collections (in the app, or with `zot collection create` + `zot collection move`), then use `zot workspace query` / `zot ask` as above. No indexing step is needed.
