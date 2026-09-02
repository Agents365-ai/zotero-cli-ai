"""Local Connected-Papers-style similarity network, rendered as one HTML file.

Similarity is computed entirely offline: TF-IDF + cosine over the item text
corpus materialized by `zot text` (falling back to title+abstract for items
without a corpus file). Two modes: a whole-collection panorama, or a seed
item expanded to its nearest neighbors. Rendering goes through pyvis
(vis-network physics) into a single self-contained HTML; hover shows
title/year, and every node title carries the item key for `zot read`.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import click

from zotero_cli_cc.commands._helpers import open_reader
from zotero_cli_cc.commands.text import DEFAULT_TEXT_DIR
from zotero_cli_cc.core.rank import resolve_collection_key
from zotero_cli_cc.exit_codes import emit_error
from zotero_cli_cc.formatter import emit_progress, envelope_ok
from zotero_cli_cc.models import Item

_KNN_EDGES = 5  # per-node nearest-neighbour edges in collection mode
_EDGE_MIN_SIM = 0.05


def _load_doc(item: Item) -> str:
    f = DEFAULT_TEXT_DIR / f"{item.key}.txt"
    if f.exists():
        return f.read_text()
    return f"{item.title}\n{item.abstract or ''}"


@click.command("net")
@click.option("--collection", default=None, help="Item scope: Zotero collection name/key (panorama graph)")
@click.option("--seed", "seed_key", default=None, help="Seed item key: expand to its nearest neighbours (CP-style)")
@click.option("--neighbors", default=25, show_default=True, help="Neighbours pulled in around the seed")
@click.option(
    "--out",
    "out_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("zot-graph.html"),
    show_default=True,
)
@click.option("--open", "open_browser", is_flag=True, help="Open the HTML in the default browser when done")
@click.pass_context
def net_cmd(
    ctx: click.Context,
    collection: str | None,
    seed_key: str | None,
    neighbors: int,
    out_path: Path,
    open_browser: bool,
) -> None:
    """Build an interactive similarity graph of the library as one HTML file.

    Fully offline: TF-IDF over the `zot text` corpus (title/abstract fallback),
    kNN edges, vis-network physics layout. Needs the [net] extra:
    pip install 'zotero-cli-ai[net]'

    \b
    Examples:
      zot net --collection "RLHF" --out rlhf.html
      zot net --seed ABC123 --neighbors 30 --open
      zot net --out ~/library-graph.html
    """
    json_out = ctx.obj.get("json", False)
    try:
        from pyvis.network import Network  # type: ignore[import-untyped]
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError as e:
        emit_error(
            "validation_error",
            f"`zot net` needs the optional [net] extra ({e}). Install it with: pip install 'zotero-cli-ai[net]'",
            output_json=json_out,
            hint="pip install 'zotero-cli-ai[net]'",
            context="net",
        )
    emit_progress("start", phase="net", out=str(out_path))
    with open_reader(ctx) as reader:
        if collection:
            if resolve_collection_key(reader, collection) is None:
                emit_error(
                    "not_found",
                    f"Collection '{collection}' not found",
                    output_json=json_out,
                    hint="Use 'zot collection list' to see available collections",
                    context="net",
                )
        items = list(reader.search("", collection=collection, limit=10_000_000).items)
        if not items:
            emit_error("not_found", "No items in scope", output_json=json_out, context="net")
        docs = [_load_doc(item) for item in items]
        emit_progress("progress", phase="net", done=1, total=3, detail=f"{len(items)} docs in scope")

        vec = TfidfVectorizer(stop_words="english", max_features=50000, min_df=2, sublinear_tf=True)
        from sklearn.metrics.pairwise import cosine_similarity

        sims = cosine_similarity(vec.fit_transform(docs))
        emit_progress("progress", phase="net", done=2, total=3, detail="tf-idf built")

        seed_pos = -1
        if seed_key:
            keys = [item.key for item in items]
            if seed_key in keys:
                seed_pos = keys.index(seed_key)
            elif seed_key.lower() in " ".join(keys).lower():
                seed_pos = keys.index(next(k for k in keys if seed_key.lower() in k.lower()))
            if seed_pos < 0:
                emit_error(
                    "not_found",
                    f"Seed item '{seed_key}' not found in scope",
                    output_json=json_out,
                    hint="Check the key with 'zot read KEY'",
                    context="net",
                )

        def _sim(a: int, b: int) -> float:
            try:
                return float(sims[a][b])
            except (IndexError, ValueError, TypeError) as e:  # pragma: no cover - defensive
                raise RuntimeError(f"similarity lookup failed at ({a}, {b})") from e

        edges: set[tuple[int, int, float]] = set()
        nodes: list[int]
        if seed_pos >= 0:
            ranked = sorted((i for i in range(len(items)) if i != seed_pos), key=lambda i: -_sim(seed_pos, i))
            near = set(ranked[:neighbors]) | {seed_pos}
            nodes = sorted(near)
            for a, b in itertools.combinations(nodes, 2):
                w = _sim(a, b)
                if w >= _EDGE_MIN_SIM:
                    edges.add((a, b, w))
        else:
            nodes = list(range(len(items)))
            for a in nodes:
                nn = sorted(nodes, key=lambda b: -_sim(a, b))[: _KNN_EDGES + 1]
                for b in nn:
                    if b == a:
                        continue
                    w = _sim(a, b)
                    if w >= _EDGE_MIN_SIM:
                        edges.add((min(a, b), max(a, b), w))
        emit_progress("progress", phase="net", done=3, total=3, detail=f"{len(nodes)} nodes, {len(edges)} edges")

        degrees: dict[int, int] = {}
        for a, b, _w in edges:
            degrees[a] = degrees.get(a, 0) + 1
            degrees[b] = degrees.get(b, 0) + 1

        net = Network(height="92vh", width="100%", bgcolor="#111111", font_color="#e0e0e0", cdn_resources="in_line")
        net.force_atlas_2based(gravity=-40)
        # Cluster colours: greedy modularity over the displayed subgraph.
        import networkx as nx

        palette = [
            "#4363d8",
            "#3cb44b",
            "#e6194b",
            "#f58231",
            "#911eb4",
            "#46f0f0",
            "#f032e6",
            "#bcf60c",
            "#008080",
            "#9a6324",
            "#800000",
            "#808000",
            "#000075",
            "#e6beff",
            "#469990",
        ]
        sub = nx.Graph()
        sub.add_nodes_from(nodes)
        sub.add_weighted_edges_from(edges)
        community_of: dict[int, str] = {}
        legend: list[tuple[str, str]] = []
        for ci, comm in enumerate(nx.community.greedy_modularity_communities(sub)):
            color = palette[ci % len(palette)]
            for n in comm:
                community_of[n] = color
            sample = sorted((items[n].title or items[n].key for n in comm), key=str)[:2]
            legend.append((color, f"{len(comm)} papers: {'; '.join(sample)}"))
        for i in nodes:
            item = items[i]
            title = item.title or item.key
            year = (item.date or "")[:4]
            tooltip = f"{title}<br>{', '.join(c.full_name for c in item.creators)} ({year})<br>key: {item.key}"
            color = community_of.get(i, "#666666")
            net.add_node(
                item.key,
                label=title[:70],
                title=tooltip,
                value=max(1, degrees.get(i, 0)),
                color=color,
            )
        for a, b, w in edges:
            net.add_edge(items[a].key, items[b].key, value=max(0.1, w), title=f"sim {w:.2f}")
        net.set_options(json.dumps({"edges": {"color": {"color": "rgba(190,190,190,0.12)", "highlight": "#ffd166"}}}))
        net.write_html(str(out_path))
        # pyvis has no native legend: inject a small fixed div above <body>.
        legend_rows = "".join(
            f'<div style="display:flex;align-items:center;margin:2px 0">'
            f'<span style="width:11px;height:11px;background:{c};border-radius:2px;'
            f'margin-right:7px;flex:none"></span>'
            f"<span>{t}</span></div>"
            for c, t in legend
        )
        legend_div = (
            '<div style="position:absolute;top:10px;left:10px;z-index:999;'
            "background:rgba(17,17,17,0.92);border:1px solid #444;border-radius:6px;"
            "padding:8px 12px;color:#e0e0e0;font:11px/1.5 -apple-system,Segoe UI,sans-serif;"
            'max-width:340px;max-height:80%;overflow:auto">'
            f"{legend_rows}</div>"
        )
        html = out_path.read_text()
        out_path.write_text(html.replace("<body>", f"<body>\n{legend_div}", 1))

    if open_browser:
        import webbrowser

        webbrowser.open(out_path.resolve().as_uri())
    mode = "seed" if seed_key else "collection" if collection else "library"
    if json_out:
        click.echo(
            json.dumps(
                envelope_ok({"html": str(out_path), "nodes": len(nodes), "edges": len(edges), "mode": mode}),
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        click.echo(
            f"Wrote {out_path}: {len(nodes)} nodes, {len(edges)} edges ({mode} mode). Node titles carry item keys."
        )
