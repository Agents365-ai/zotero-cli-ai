# Per-Item Summary Templates (Pattern 6, pipeline B)

Before writing `~/.config/zot/summary/<KEY>.md`, classify the item from its title and
abstract — Zotero's `item_type` alone cannot distinguish a method paper from a
research paper (both are `journalArticle`).

| Signal in title/abstract | Template |
| --- | --- |
| Proposes an algorithm, pipeline, or tool; benchmark / dataset / performance framing | Method paper |
| Addresses a scientific question; experiment / observation / hypothesis framing | Research paper |
| "review", "survey", "advances in", "state of the field" | Review paper |
| Anything else (book, thesis, web page, no strong signal) | Generic item |

## Output contract (all templates)

- Obsidian-flavored Markdown: YAML frontmatter (`title`, `key`, `date`, `model`,
  `tags` including the template tag), `#` for the paper title, `##` per section,
  Obsidian callouts (`> [!note]`, `> [!tip]`, `> [!warning]`) for key points.
- Inline math `$x$`, display math `$$...$$`. Never quote the source text; never add
  a citation list — items are cited by their Zotero keys in the reduce stage.
- Critical stance throughout: evaluate rigor, soundness, and impact, not just
  describe. Concise, no filler.
- Respond in the language of the request.
- Ground every claim in the supplied materials (summarize pack, pdf outline or
  sections, text files); never invent content they do not support.

## Method paper (tag: `method-paper`)

1. **Background & Scientific Problem** — the research background and the specific
   problem addressed; practical significance and application scenarios in the field
   (e.g., large-scale data analysis, disease diagnosis, biological mechanism
   discovery).
2. **Methods & Materials** — the proposed algorithm or analytical approach in
   detail: design rationale, key techniques, experimental design, data sources.
   Examine datasets, workflow, parameter settings, and baselines; assess
   soundness, rigor, and reproducibility, with particular attention to performance
   on complex, large-scale, or noisy data.
3. **Results & Conclusions** — core findings and key results; evaluate scientific
   validity, statistical significance, and the reliability and generalizability of
   the conclusions. Check whether the validation (controlled experiments,
   cross-validation, external datasets) supports the claims.
4. **Novelty & Contribution** — methodological innovations: algorithmic
   breakthroughs, theoretical insights, practical improvements. Foresight, practical
   value, potential impact on future work in the field.
5. **Limitations & Improvements** — shortcomings: experimental design, data
   representativeness, scope of applicability, generalizability. Concrete
   improvement suggestions: more rigorous experimental design, richer validation
   data, more comprehensive performance comparisons.

## Research paper (tag: `research-paper`)

Identify the field, adopt the role of a domain expert, and place the work in its
historical context.

1. **Background & Scientific Question** — what is known, what remains unknown; the
   specific scientific problem addressed and why solving it matters.
2. **Methods & Materials** — study design, data sources, analytical methods;
   soundness and rigor of the methodology.
3. **Results & Conclusions** — core findings; scientific soundness and reliability.
4. **Novelty & Contribution** — innovations in analytical approach, methodology, or
   conceptual breakthrough; theoretical and practical value.
5. **Limitations & Improvements** — experimental constraints, data sufficiency,
   generalizability; concrete improvements.

## Review paper (tag: `review-paper`)

1. **Scope & Theme** — the domain under review and its boundaries; core theme and
   main research directions covered.
2. **Logical Framework** — how the authors organize and develop the argument;
   narrative structure and progression.
3. **Key Points & Coverage** — each major section, its central claims, and whether
   the coverage is comprehensive and logically coherent.
4. **Strengths, Weaknesses & Suggestions** — strengths (systematic coverage, solid
   evidence, novel perspectives); flaws (biased literature selection, insufficient
   depth, weak discussion of future directions) and suggested improvements.

## Generic item (tag: `summary`)

1. **What it is** — item type, scope, intended audience.
2. **Key content** — structure and main points, grounded in the materials.
3. **Relevance** — why it matters for the collection's topic and the reduce stage.