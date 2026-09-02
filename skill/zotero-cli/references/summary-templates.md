# Per-Item Summary Templates (Pattern 6, pipeline B)

Each per-paper summary is composed from two axes:

1. **Type template** (section skeleton) — chosen from the title/abstract. Zotero's
   `item_type` alone is too coarse (a method paper and a research paper are both
   `journalArticle`; reviews may be too).
2. **Discipline lens** (critique focus) — matched to the item's field and appended
   as the final section, `## Discipline-specific assessment`.

Write the result to `~/.config/zot/summary/<KEY>.md`.

## Output contract (all templates)

- Obsidian-flavored Markdown: YAML frontmatter (`title`, `key`, `date`, `model`,
  `tags` including the type tag and the discipline tag), `#` for the paper title,
  `##` per section, Obsidian callouts (`> [!note]`, `> [!tip]`, `> [!warning]`)
  for key points.
- Inline math `$x$`, display math `$$...$$`. Never quote the source text; never add
  a citation list — items are cited by their Zotero keys in the reduce stage.
- Critical stance throughout: evaluate rigor, soundness, and impact, not just
  describe. Concise, no filler. Lenses are cues, not checkboxes — include only what
  the supplied materials support.
- Respond in the language of the request.
- Ground every claim in the pipeline materials (summarize pack, pdf outline or
  sections, text files); never invent content they do not support.

## Type templates

### Method paper (tag: `method-paper`)

1. **Background & Scientific Problem** — the research background and the specific
   problem addressed; practical significance and application scenarios.
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
   improvement suggestions.

### Research paper (tag: `research-paper`)

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

Preprints use this template unchanged, but the frontmatter `tags` must include
`preprint` and the summary must state that the work is not peer-reviewed.

### Review / survey paper (tag: `review-paper`)

1. **Scope & Theme** — the domain under review and its boundaries; core theme and
   main research directions covered.
2. **Logical Framework** — how the authors organize and develop the argument;
   narrative structure and progression.
3. **Key Points & Coverage** — each major section, its central claims, and whether
   the coverage is comprehensive and logically coherent.
4. **Strengths, Weaknesses & Suggestions** — strengths (systematic coverage, solid
   evidence, novel perspectives); flaws (biased literature selection, insufficient
   depth, weak discussion of future directions) and suggested improvements.

### Clinical study (tag: `clinical-study`)

Cohort, case-control, RCT, or single-arm trial.

1. **Design & Population** — study design and its hierarchy of evidence; eligibility
   criteria, sample size, and whether the registry (e.g., ClinicalTrials.gov)
   matches the reported outcomes.
2. **Intervention / Exposure & Endpoints** — primary and secondary endpoints;
   effect sizes with confidence intervals, not p-values alone.
3. **Results & Conclusions** — findings vs the pre-registered hypothesis; clinical
   as well as statistical significance.
4. **Validity & Bias** — randomization, blinding, intention-to-treat vs per-protocol,
   confounding, attrition, adverse events, ethics approval.
5. **Limitations & Generalizability** — external validity, population
   representativeness, follow-up duration; concrete improvements.

### Meta-analysis / systematic review (tag: `meta-analysis`)

1. **Question & Protocol** — the review question and whether the protocol (e.g.,
   PROSPERO, PRISMA flow) was pre-registered and followed.
2. **Search & Selection** — databases searched, inclusion/exclusion criteria,
   study selection and quality assessment of the primary studies.
3. **Synthesis** — heterogeneity assessment, pooling model (fixed vs random
   effects), sensitivity analyses; whether combining the studies was appropriate
   at all.
4. **Strength of Evidence** — what the pooled effect does and does not establish;
   publication-bias checks (funnel plots, trim-and-fill).
5. **Limitations & Implications** — coverage gaps, primary-study quality ceiling,
   actionable implications for practice or research.

### Dataset / resource / benchmark paper (tag: `dataset-resource`)

Databases, atlases, benchmarks, software, model releases.

1. **Scope & Design** — what the resource contains, how it was assembled, and the
   curation pipeline.
2. **Quality & Provenance** — data sources, QC measures, versioning, update policy;
   contamination/leakage risks for benchmarks.
3. **Access & Documentation** — availability, license, API/format, documentation
   quality, sustained maintenance plan.
4. **Reuse & Impact** — who needs it, what becomes possible, adoption evidence.
5. **Limitations & Improvements** — coverage gaps, accessibility barriers,
   sustainability risks.

### Generic item (tag: `summary`)

Books, theses, web pages, items without a strong type signal.

1. **What it is** — item type, scope, intended audience.
2. **Key content** — structure and main points, grounded in the materials.
3. **Relevance** — why it matters for the collection's topic and the reduce stage.

## Discipline lenses

Append as the final section, `## Discipline-specific assessment`, and add the lens
tag to the frontmatter. Pick by field; when two apply, use the closer one.

### Bioinformatics / computational biology (tag: `bioinformatics`)

- Code and data availability: repository links, versioned references, container or
  environment reproducibility.
- Reference genome / annotation version pinning; pipeline parameter reporting.
- Batch effects, normalization, and whether multiple-testing correction (e.g., FDR)
  is applied at the right level.
- Validation on independent cohorts or external datasets, not just resampling of
  the discovery set.
- Benchmark fairness: comparable inputs, meaningful baselines, honest compute
  reporting.

### Clinical / medical research (tag: `clinical`)

- Design hierarchy and prospective registration; outcome switching between registry
  and paper.
- Effect sizes with CIs and absolute vs relative risk framing.
- Intention-to-treat handling, blinding, confounding control, attrition.
- Safety reporting (adverse events) and ethics approval.
- External validity: does the population generalize beyond the enrollment criteria?

### Machine learning / AI (tag: `ml-ai`)

- Data leakage: split hygiene, preprocessing fitted before the split, test-set
  contamination in foundation-model evaluations.
- Baseline strength and ablations: are gains attributable to the claimed idea?
- Variance reporting: seeds, runs, error bars; single-run SOTA claims.
- Metric choice aligned with the task; deployment-cost and compute honesty.
- Reproducibility artifacts: released code, weights, configs, data cards.

### Wet-lab experimental biology (tag: `wet-lab`)

- Controls: positive and negative controls present and appropriate.
- Replication: biological vs technical replicates, n, and what the statistics were
  computed over.
- Reagent validation: antibody specificity, cell-line identity, knockout/overexpression
  efficiency verification.
- Dose-response and time-course evidence; physiological plausibility of conditions.
- Blinding and predefined exclusion criteria.