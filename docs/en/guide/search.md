# Search & Browse

## How Search Works

`zot search` matches keywords across four layers:

1. **Titles & abstracts** — direct text match
2. **Author names** — first and last name matching
3. **Tags** — exact tag matching
4. **PDF fulltext index** — Zotero's built-in fulltext index

## Choosing a Search Command

- **`zot search`** — quick keyword lookup across metadata and the full-text index (this page).
- **`zot search --ranked`** — ranked deep search over a natural-language question: relevance scores and snippets, optionally scoped to a collection. Index-free: results are always fresh.
- **`zot ask`** — same ranked retrieval, but returns a citation-keyed evidence pack (metadata + PDF passages) for an agent to synthesize an answer from.

## Ranked Deep Search

```bash
zot search "RLHF reward hacking" --ranked
zot search "tumour immunity" --ranked --collection "CR | HCC" --limit 10
```

- `--collection` scopes the search to a collection (name or key; nested collections resolve by name). Omit it to search the whole library.
- `--limit` sets the number of results. `--ranked` ignores `--sort`/`--type`/`--stream`.

Retrieval is index-free: items are scored with FTS5 bm25 against Zotero 10's own full-text index (`fulltext.sqlite`, the same index the Zotero app builds), fused with metadata matching (title/abstract/creators/tags/notes) via reciprocal rank fusion. A paper added a second ago is already searchable. On pre-Zotero 10 data directories (no `fulltext.sqlite`) full-text scoring degrades to metadata-only matching with a warning.

JSON output:

```json
{
  "ok": true,
  "data": {
    "query": "reward hacking methods",
    "collection": "LLM Safety",
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
zot ask "what dataset was used?" --collection papers --evidence-k 8
```

- `--collection` scopes retrieval to a collection (name or key). Omit it for the whole library.
- `--evidence-k` sets the number of evidence entries (default: 12).

JSON output:

```json
{
  "ok": true,
  "data": {
    "question": "what dataset was used?",
    "collection": "papers",
    "mode": "index-free",
    "evidence": [
      { "cite_key": "ABC123", "source": "metadata", "text": "Title: ...", "scores": { "rrf": 0.0328, "fulltext": 4.5612, "metadata": 2.0 } },
      { "cite_key": "ABC123", "source": "pdf", "text": "...passage around the query terms...", "scores": { "rrf": 0.0328, "fulltext": 4.5612, "metadata": 2.0 } }
    ],
    "answer_instructions": "Answer the question using ONLY the evidence below. Cite each claim with its cite_key in parentheses, e.g. (ABCD1234). ..."
  }
}
```

## Scoping with Collections

Any Zotero collection can scope a ranked search or evidence pack — there is nothing to create inside zot and no index to build. Manage membership in the Zotero app, or from the CLI:

```bash
zot collection list                        # All collections (names + keys)
zot collection items COLL_KEY              # Items in a collection
zot collection create "LLM Safety"         # Create a collection (needs API key)
zot collection move ITEM_KEY COLL_KEY      # Add an item to a collection
zot collection remove ITEM_KEY COLL_KEY    # Remove from collection (item stays in library)
zot collection rename COLL_KEY "New Name"  # Rename
zot collection delete COLL_KEY             # Delete a collection
zot collection reorganize plan.json        # Batch create + move from a JSON plan
```

!!! note "Upgrading from pre-0.13"
    The `zot workspace` command group was removed in 0.13 — use `zot search --ranked` instead of `zot workspace query`, and `zot ask --collection` instead of `zot ask --workspace`.

## Basic Search

```bash
zot search "transformer attention"
```

## Filter by Collection

```bash
zot search "BERT" --collection "NLP"
```

## Filter by Item Type

```bash
zot search "protein" --type journalArticle
```

Common types: `journalArticle`, `conferencePaper`, `preprint`, `book`, `bookSection`, `thesis`

## Sort Results

```bash
zot search "attention" --sort dateAdded --direction desc
zot search "attention" --sort title --direction asc
```

Sort fields: `dateAdded`, `dateModified`, `title`, `creator`

## List All Items

```bash
zot list --limit 20
zot list --collection "Machine Learning"
```

## Recently Added Items

```bash
zot recent                    # Last 7 days (default)
zot recent --days 30          # Last 30 days
zot recent --days 7 --modified  # Recently modified
```

## View Item Details

```bash
zot read ABC123
```

Shows metadata, abstract, and notes. Use `--detail full` for extra fields.

## Find Related Items

```bash
zot relate ABC123
```

Finds items sharing tags, collections, or explicit relations.

## Detail Levels

```bash
zot --detail minimal search "attention"   # Key, title, authors, year only
zot --detail standard read ABC123         # Default — includes abstract, tags, DOI
zot --detail full read ABC123             # All fields including extra metadata
```

## JSON Output

```bash
zot --json search "attention"
```

All commands support `--json` for machine-readable output.

## Library Statistics

```bash
zot stats
```

Shows total items, PDFs, notes, breakdown by type, collections, and top tags.
