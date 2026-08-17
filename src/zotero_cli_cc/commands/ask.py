from __future__ import annotations

import click

from zotero_cli_cc.commands._helpers import open_reader
from zotero_cli_cc.core.rank import build_ask_evidence, rank, resolve_collection_key
from zotero_cli_cc.exit_codes import emit_error
from zotero_cli_cc.formatter import emit_progress, format_ask


@click.command("ask")
@click.argument("question")
@click.option(
    "--workspace",
    "ws_name",
    default=None,
    help="Scope to a Zotero collection (name or key). Default: whole library. "
    "Manage the collection in the Zotero app or via 'zot collection *'.",
)
@click.option("--evidence-k", default=12, help="Number of evidence entries to retrieve (default: 12)")
@click.pass_context
def ask_cmd(ctx: click.Context, question: str, ws_name: str | None, evidence_k: int) -> None:
    """Retrieve a citation-keyed evidence pack to answer a question.

    Runs index-free ranked retrieval over Zotero's own full-text index
    (optionally scoped to a collection), then returns evidence tagged with
    Zotero item keys plus answer instructions, so the calling agent can
    synthesize a grounded, cited answer. zot does not call an LLM itself.

    \b
    Examples:
      zot ask "how does attention scale?"
      zot --json ask "what dataset was used?" --workspace papers --evidence-k 8
    """
    json_out = ctx.obj.get("json", False)
    with open_reader(ctx) as reader:
        collection_key = None
        if ws_name:
            collection_key = resolve_collection_key(reader, ws_name)
            if collection_key is None:
                emit_error(
                    "not_found",
                    f"Collection '{ws_name}' not found",
                    output_json=json_out,
                    hint="Use 'zot collection list' to see available collections",
                    context="ask",
                )
        emit_progress("progress", phase="ask", step="rank")
        ranked = rank(reader, question, collection_key=collection_key, top_k=evidence_k)
        emit_progress("progress", phase="ask", step="extract")
        evidence = build_ask_evidence(reader, ranked, evidence_k=evidence_k)
        click.echo(format_ask(question, evidence, "index-free", output_json=json_out, workspace=ws_name))
