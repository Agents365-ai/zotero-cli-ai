# Workflow Patterns

## Pattern 1: Find and Read a Paper

```bash
# Step 1: Search
zot --json search "single cell RNA sequencing"

# Step 2: Read metadata
zot --json read K853PGUG

# Step 3: PDF — check structure first, extract selectively
zot --json pdf --outline K853PGUG             # Get numbered section headings
zot --json pdf --section 10 K853PGUG          # Extract only the section you need
zot --json pdf K853PGUG                       # Full text (only if short or necessary)
```

**Token budget**: For PDFs >20k chars, always use `--outline` then `--section` instead of pulling full text.

**No PDF attached?** If `zot pdf` reports no attachment, run `zot find-pdf K853PGUG` to have Zotero desktop fetch and attach one (requires the bridge — see `references/commands.md`).

## Pattern 2: Deep Content Search in a Collection

```bash
# Step 1: Curate a collection (drag & drop in the Zotero app, or CLI)
zot collection create "drug-resistance"
zot --json search "drug resistance cancer" --limit 20
zot collection move ITEMKEY COLLECTIONKEY       # repeat per item

# Step 2: Ranked search — no index step, always fresh
zot --json search --ranked "mechanisms of acquired resistance" --collection drug-resistance --limit 5

# Step 3: Drill into specific items for more context
zot --json pdf --outline ITEMKEY
zot --json pdf --section N ITEMKEY
```

## Pattern 3: Batch Export from Collections

```python
import subprocess, json, os

env = os.environ.copy()
env['PYTHONIOENCODING'] = 'utf-8'  # Required on Windows CJK systems (older versions)

collections = {
    'topic_a': 'COLLKEY1',
    'topic_b': 'COLLKEY2',
}

for name, key in collections.items():
    result = subprocess.run(
        ['zot', '--json', 'collection', 'items', key],
        capture_output=True, env=env,
    )
    if result.returncode != 0:
        print(f'{name}: error - {result.stderr.decode("utf-8", errors="replace")}')
        continue

    data = json.loads(result.stdout.decode('utf-8'))
    with open(f'batch_{name}.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'{name}: {data["meta"]["count"]} items')
```

## Pattern 4: Library Reorganization

```bash
# Step 1: Export all abstracts
zot --json summarize-all > abstracts.json

# Step 2: Analyze and classify (AI or manual)
# Step 3: Create collections and move items
zot collection create "Category A"
zot collection move ITEMKEY COLLECTIONKEY
```

## Pattern 5: Literature Review Pipeline

```bash
# 1. Import papers from DOI list
zot add --from-file dois.txt

# 2. Organize into a collection (or drag & drop in the Zotero app)
zot collection create "lit-review"
zot collection move ITEMKEY COLLECTIONKEY

# 3. Ranked search for themes — runs live, no index to build
zot --json search --ranked "methodology comparison" --collection lit-review --limit 10

# 4. Or get a citation-keyed evidence pack for a grounded answer
zot --json ask "which methodologies are compared?" --collection lit-review
```

## Pattern 6: Collection Summary & Topic Q&A

Summarize or run Q&A over a whole collection. zot supplies the materials and the
storage; the summaries themselves are written by you (or subagents) — zot never calls
an LLM. Three pipelines, chosen by the SOURCE the summary should be grounded in, not
by collection size. PDF text extraction is cached, so repeated passes cost nothing.

### A. Collection summary — abstract based (fast)

```bash
# 1. Abstracts of all items in the collection, one call
zot --json collection items COLLKEY              # key, title, abstract, date, doi

# 2. Summarize the abstracts — direct synthesis, no per-paper step
```

### B. Collection summary — summary based (map-reduce, full text)

```bash
# 1. Full text per item — zot extracts and caches (no repeated cost)
zot --json pdf --outline KEY                     # section headings only (token-cheap)
zot --json pdf --section N KEY                   # read only the sections that matter

# 2. Create a summary for each item — subagents in parallel (batch 3-5 papers):
#    bounded summary: problem / method / findings / relevance (~5 sentences)
zot note KEY --add "**Summary**: ..."            # persist per-paper summary as a note

# 3. Summarize the summaries
zot --json summarize KEY                         # notes[:500] come back with the pack
#    (or `zot note KEY` for full note text when a summary runs longer)
zot note --standalone --add "## Collection summary: <name> ..."
```

### C. Summary / Q&A on a topic or key words, scoped to a collection

```bash
# 1. Rank the collection's text against the key words (FTS, always fresh)
zot --json search --ranked "KEY WORDS" --collection COLLKEY

# 2. Extract the context around each hit in each paper — evidence passages,
#    citation-keyed; internally re-ranks by term frequency over cached PDF text
zot --json ask "topic question" --collection COLLKEY

# 3. Summarize from the extracted passages; cite with the returned item keys
```

Steps 1-2 of this pipeline are one `zot ask --collection` call away: `ask` runs the
ranked retrieval AND carves the evidence passages in a single invocation. Use
`search --ranked` first when you want to see the ranked item list before committing
to evidence extraction.

**Why persist per-paper summaries to notes (pipeline B).** Notes are part of the
library: the reduce stage reads them back with plain read commands, and so does any
future session. The collection-level synthesis becomes a standalone note retrievable
with `zot note --standalone`.

**Safety.** `zot note --add` mutates the library via the Web API and needs write
credentials (`zot config init`).
