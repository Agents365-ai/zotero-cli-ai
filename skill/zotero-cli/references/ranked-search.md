# Workspaces

A workspace is simply a Zotero collection. `zot` stores nothing locally — no
workspace files, no index. Membership lives in Zotero and queries run live, so
results are always fresh.

## Managing Workspaces

Curate membership in the Zotero app (drag & drop items into a collection), or
via the CLI:

```bash
zot --json collection list                       # find collection keys
zot collection create "LLM Safety"
zot collection move ITEMKEY COLLECTIONKEY
zot --json collection items COLLECTIONKEY
zot collection delete COLLECTIONKEY
```

Wherever `--workspace` is accepted, pass a collection name or key — nested
collections resolve by name too.

## Ranked Search: `zot workspace query`

```bash
zot workspace query "reward hacking"                            # whole library
zot workspace query "RLHF methods" --workspace "LLM Safety" --top-k 10
zot --json workspace query "attention" --workspace "LLM Safety"
```

`--workspace` is optional; omit it to search the whole library. JSON output:

```json
{
  "query": "reward hacking",
  "workspace": "LLM Safety",
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
zot ask "how does attention scale?"                             # whole library
zot --json ask "what dataset was used?" --workspace papers --evidence-k 8
```

`--evidence-k` defaults to 12. Returns a citation-keyed evidence pack
(`mode: "index-free"`): each entry has `cite_key` (Zotero item key), `source`
(`metadata` or `pdf`), `text`, and `scores`, plus `answer_instructions`.
`zot` never calls an LLM — the agent synthesizes a grounded answer from the
evidence and cites by `cite_key`.

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

## Migrating From Old Local Workspaces

Earlier versions kept local workspaces under `~/.config/zot/workspaces/`
(JSON membership files plus `*.idx.sqlite` RAG indexes) and required a
`zot workspace index` step. Both are gone — that directory is no longer used
and can be deleted. Recreate the same paper sets as Zotero collections (in the
app, or with `zot collection create` + `zot collection move`), then query with
`zot workspace query` / `zot ask --workspace <collection>`.
