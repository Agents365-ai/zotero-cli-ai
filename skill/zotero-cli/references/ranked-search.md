# Ranked Search & Ask

Ranked retrieval runs over your whole library or any Zotero collection. `zot`
stores nothing locally — no index to build, no local state. Collection
membership lives in Zotero and queries run live, so results are always fresh.

## Scoping to a Collection

Curate membership in the Zotero app (drag & drop items into a collection, or
remove them from it), or via the CLI:

```bash
zot --json collection list                       # find collection keys
zot collection create "LLM Safety"
zot collection move ITEMKEY COLLECTIONKEY        # add an item to a collection
zot collection remove ITEMKEY COLLECTIONKEY      # remove an item (item stays in the library)
zot --json collection items COLLECTIONKEY
zot collection delete COLLECTIONKEY
```

Wherever `--collection` is accepted, pass a collection name or key — nested
collections resolve by name too.

## Ranked Search: `zot search --ranked`

```bash
zot search --ranked "reward hacking"                                # whole library
zot search --ranked "RLHF methods" --collection "LLM Safety" --limit 10
zot --json search --ranked "attention" --collection "LLM Safety"
```

`--collection` is optional; omit it to search the whole library. `--ranked`
ignores `--sort`/`--type`/`--stream`. JSON output:

```json
{
  "query": "reward hacking",
  "collection": "LLM Safety",
  "results": [
    {
      "rank": 1,
      "score": 0.0154,
      "scores": {"rrf": 0.0154, "fulltext": 3.21, "metadata": 2.0},
      "item_key": "B6TZ6TQX",
      "title": "...",
      "creators": ["..."],
      "date": "2024",
      "snippet": "..."
    }
  ]
}
```

## Evidence Packs: `zot ask`

```bash
zot ask "how does attention scale?"                                 # whole library
zot --json ask "what dataset was used?" --collection papers --evidence-k 8
```

`--evidence-k` defaults to 12. Returns a citation-keyed evidence pack:
`{question, collection, mode: "index-free", evidence: [{cite_key, source,
text, scores}], answer_instructions}` where `cite_key` is the Zotero item key
and `source` is `metadata` or `pdf`. `zot` never calls an LLM — the agent
synthesizes a grounded answer from the evidence and cites by `cite_key`.

## How Retrieval Works

Index-free two-stage ranking — nothing to build or maintain:

1. **Stage 1** scores items with idf-weighted term coverage from Zotero's own
   full-text index tables (the same index the Zotero app builds), fused via
   reciprocal rank fusion with metadata matching (title/abstract/creators/
   tags/notes).
2. **Stage 2** (`ask` only) extracts PDF passages on the fly around query
   terms (cached), so evidence includes both metadata/abstract and full-text
   passages.

Because queries hit Zotero's live tables, newly added items show up as soon as
Zotero indexes them — there is no stale index to rebuild.

## Drilling Into Evidence

When a snippet or passage is incomplete, pull more context from the source:

```bash
zot --json pdf --outline ITEMKEY            # Get numbered section headings
zot --json pdf --section N ITEMKEY          # Extract content under the N-th heading
```

> **Migration:** the pre-0.13 `zot workspace` command group was removed — its functionality lives in `zot search --ranked` and `zot ask --collection`.
