---
name: zotero-cli
description: Use when user mentions papers, references, citations, Zotero, literature, bibliography, or needs to search, read, export, or organize documents. Handles all zot CLI operations including ranked search over Zotero collections.
---

# Zotero CLI Skill

`zot` is an all-in-one Zotero CLI: search, CRUD, PDF extraction, citation export, and ranked retrieval over collections. Local SQLite for reads, Zotero Web API for writes.

## Quick Start

```bash
zot search "transformer attention"                      # Search papers
zot --detail minimal search "transformer attention"     # Search papers (minimal output)
zot --detail full search "transformer attention"        # Search papers (full output)
zot --json read ABC123                                  # View paper details (JSON)
zot export ABC123                                       # Export BibTeX
zot --json search --ranked "RLHF" --collection my-collection  # Ranked search scoped to a collection
```

## Critical Rules

1. **Always use `--json`** for programmatic processing (auto-enabled when stdout is not a TTY).
2. **Windows CJK encoding**: On Windows with a CJK locale, recent `zot` versions auto-reconfigure stdout to UTF-8. For older versions or subprocess calls, set `PYTHONIOENCODING=utf-8`. See `references/windows-encoding.md`.
3. **Write safety**: Use `--dry-run` to preview mutations. Pass `--idempotency-key` on retries.
4. **Large PDFs**: Use `--outline` first, then `--section N` (the heading number from the outline) to extract selectively. Avoid pulling full text when >20k chars.
5. **Find Full Text**: `zot find-pdf KEY` fetches paywalled PDFs but needs Zotero desktop running + the bridge plugin. One-time setup: `zot bridge install`. See `references/commands.md`.
6. **Canonical schema**: Run `zot schema <cmd>` for exhaustive flags, types, and safety tiers.

## Routing Table

| User Intent | Command |
| ------------- | --------- |
| Search metadata | `zot --json search "query"` |
| Read item detail | `zot --json read KEY` |
| Export BibTeX/RIS/JSON | `zot export KEY --format bibtex` |
| Formatted citation | `zot cite KEY --style apa` |
| Batch import DOIs | `zot add --from-file dois.txt` |
| Add single item | `zot add --doi "10.1038/..."` |
| Update metadata | `zot update KEY --title "New"` |
| Delete item | `zot --no-interaction delete KEY` |
| PDF full text | `zot --json pdf KEY` |
| PDF outline | `zot --json pdf --outline KEY` |
| PDF section | `zot --json pdf --section N KEY` |
| Local PDF path | `zot attachment path KEY` (first PDF; `--all` for appendix/supplementary too) |
| Fetch/attach missing PDF | `zot find-pdf KEY` (needs Zotero desktop + bridge) |
| Rename attachment files | `zot rename KEY --dry-run` (needs bridge; preview first) |
| Add journal metrics (IF/分区) | `zot enrich KEY --set "JCR=Q1"` or `--from-map journals.toml` |
| Set up find-pdf bridge | `zot bridge install` |
| Collection list | `zot --json collection list` |
| Collection items | `zot --json collection items COLLKEY` |
| Find duplicates | `zot --json duplicates` |
| Recent items | `zot --json recent --days 7` |
| Library stats | `zot --json stats` |
| Collection create | `zot collection create "NAME"` |
| Remove item from collection | `zot collection remove ITEM COLL` |
| Ranked deep search | `zot --json search --ranked "q" --collection COLL` |
| Ask (evidence pack) | `zot --json ask "question" --collection COLL` |
| Grep-able full-text corpus | `zot text --dir ~/zot-text` → `grep -r "term" ~/zot-text/` (hit filename = item key) |
| Similarity network graph | `zot net --seed KEY --open` or `zot net --collection COLL` (offline TF-IDF, needs [net] extra) |
| Group library | `zot --library group:ID search "q"` |

**Rule of thumb**: `zot search` for quick metadata + full-text lookups. `zot search --ranked` for relevance-ranked deep search with scores and snippets, optionally scoped to a collection via `--collection`. `zot ask` when you need a citation-keyed evidence pack to write a grounded answer — it returns chunks tagged with their Zotero item key plus `answer_instructions`; `zot` does not call an LLM, so *you* synthesize and cite the answer from the evidence.

## Global Flags

| Flag | Purpose |
| ------ | --------- |
| `--json` | JSON output (always use for programmatic processing) |
| `--limit N` | Limit results (default: 50) |
| `--detail minimal` | Only key/title/authors/year — saves tokens |
| `--detail full` | All fields |
| `--no-interaction` | Suppress prompts (automation) |
| `--verbose` | Debug output |

## Key Facts

- Read ops work offline with zero config
- Write ops need API credentials (`zot config init`)
- Item keys are 8-char alphanumeric strings (e.g. `K853PGUG`)
- Non-TTY stdout auto-emits JSON envelope — agents never need explicit `--json`

## References

- `references/commands.md` — Full command reference with examples
- `references/ranked-search.md` — Ranked search and evidence packs over collections
- `references/workflows.md` — Common multi-step workflow patterns
- `references/windows-encoding.md` — Windows CJK encoding fix
