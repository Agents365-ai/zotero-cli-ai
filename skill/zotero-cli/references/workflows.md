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
# 1. Materialize full text once — one <KEY>.txt file per item, grep-able
zot text --only-cached                           # instant if extraction cache is warm
#    (per-paper drill-down without materializing: zot pdf --outline KEY / --section N KEY)

# 2. Create a summary for each item — subagents in parallel (batch 3-5 papers):
#    compose the summary from two axes in references/summary-templates.md:
#    the TYPE template (method / research / review / clinical / meta-analysis /
#    dataset-resource / generic, classified from title+abstract) plus the
#    DISCIPLINE lens (bioinformatics / clinical / ml-ai / wet-lab) appended as
#    the final assessment section. Write ~/.config/zot/summary/<KEY>.md:
#    Obsidian-flavored markdown, YAML frontmatter (title, key, date, model,
#    type + discipline tags), ## per section.

# 3. Summarize the summaries — Read/Glob the summary files back
#    optional library-visible copy: zot note KEY --add "..." (tagged llm-summary)
zot note --standalone --add "## Collection summary: <name> ..."
```

### C. Summary / Q&A on a topic or key words, scoped to a collection

```bash
# 1. Materialize the corpus once (cached extraction, parallel workers)
zot text                                         # ~/.config/zot/text/<KEY>.txt

# 2. File-content search over the materialized text — hit filename = item key
grep -rln "KEY WORDS" ~/.config/zot/text/        # -l: files containing matches

# 3. Collect the context around each hit (grep -C 3, or Read the file sections),
#    then hand the collected passages to the LLM for the topic summary or Q&A
```

Index-based alternative for the same pipeline: `zot search --ranked "KEY WORDS"
--collection COLLKEY` ranks the collection's text against the key words directly
from Zotero's own FTS index (no materialization step, CJK tokenization handled), and
`zot ask "topic question" --collection COLLKEY` returns citation-keyed evidence
passages in one call. Prefer the index route for one-off questions over a large
library; prefer the file route (grep) for repeated, hands-on analysis sessions.

**Local storage conventions.** Full text and summaries are per-item files under the
zot config dir, keyed by the item key: `~/.config/zot/text/<KEY>.txt` (written by
`zot text`) and `~/.config/zot/summary/<KEY>.md` (written by the agent during
pipeline B, Obsidian-flavored with YAML frontmatter carrying provenance: title,
key, date, model, type tag — templates in `references/summary-templates.md`). Both
are local working stores: fast for agents, regenerable, not synced with Zotero.
When a summary should also be visible in the Zotero app (and travel with the
library), mirror its body into a child note with `zot note KEY --add "..."`
optionally tagged `llm-summary` (strip the frontmatter first — `zot note` drops
it during Markdown-to-HTML conversion).

**Safety.** `zot note --add` mutates the library via the Web API and needs write
credentials (`zot config init`); the file-based stores above need no credentials.
