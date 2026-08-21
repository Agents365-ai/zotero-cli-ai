from __future__ import annotations

import json

import click

from zotero_cli_cc.commands._helpers import build_writer, open_reader
from zotero_cli_cc.config import load_config
from zotero_cli_cc.core.markdown import md_to_zotero_html
from zotero_cli_cc.core.writer import SYNC_REMINDER, ZoteroWriteError
from zotero_cli_cc.exit_codes import emit_error
from zotero_cli_cc.formatter import envelope_ok, format_notes


@click.command("note")
@click.argument("key", required=False)
@click.option("--add", "content", default=None, help="Add a new note (Markdown, converted to HTML)")
@click.option(
    "--standalone",
    is_flag=True,
    help="Operate on standalone (top-level) notes: list them, or create one with --add",
)
@click.option("--raw", is_flag=True, help="Store note content verbatim, skipping Markdown-to-HTML conversion")
@click.option("--dry-run", is_flag=True, help="Preview the note addition without executing (only with --add)")
@click.option("--idempotency-key", default=None, help="Key so retries are safe; same key returns the original result")
@click.pass_context
def note_cmd(
    ctx: click.Context,
    key: str | None,
    content: str | None,
    standalone: bool,
    raw: bool,
    dry_run: bool,
    idempotency_key: str | None,
) -> None:
    """View a note or add one to an item. `--add` MUTATES LIBRARY.

    \b
    Zotero stores notes as HTML, so `--add` converts Markdown to HTML before
    submitting: YAML frontmatter is stripped and Obsidian callouts
    (> [!type] ...) become bold blockquotes. Use `--raw` to store the content
    verbatim instead.

    \b
    With `--standalone`, operate on top-level notes (no parent item): list
    them without a KEY, or create one with `--add`.

    \b
    Examples:
      zot note ABC123                            View notes
      zot note ABC123 --add "Key finding: ..."   Add a note (Markdown -> HTML)
      zot note ABC123 --add "<p>...</p>" --raw   Add verbatim HTML
      zot note --standalone                      List standalone notes
      zot note --standalone --add "..."          Add a standalone note
      zot note ABC123 --add "..." --dry-run      Preview addition
      zot --json note ABC123                     JSON output
    """
    cfg = load_config(profile=ctx.obj.get("profile"))
    json_out = ctx.obj.get("json", False)

    if content:
        if standalone and key is not None:
            emit_error(
                "validation_error",
                "KEY cannot be combined with --standalone",
                output_json=json_out,
                hint="Use: zot note --standalone --add 'content'",
                context="note",
            )
        if not standalone and key is None:
            emit_error(
                "validation_error",
                "KEY is required (unless --standalone)",
                output_json=json_out,
                hint="Use: zot note KEY --add 'content', or zot note --standalone --add 'content'",
                context="note",
            )

        payload = content if raw else md_to_zotero_html(content)
        parent_for_preview = None if standalone else key
        if dry_run:
            data = {"would": {"parent": parent_for_preview, "content_preview": payload[:200]}}
            if json_out:
                click.echo(json.dumps(envelope_ok(data, extra={"dry_run": True}), indent=2, ensure_ascii=False))
            else:
                human_preview = (
                    f"Would add standalone note: {payload[:80]}..."
                    if standalone
                    else f"Would add note to '{key}': {payload[:80]}..."
                )
                click.echo(f"[dry-run] {human_preview}")
            return

        from zotero_cli_cc.core.idempotency import get_cached, store_cached

        cache_scope = "note:standalone" if standalone else f"note:{key}"
        if idempotency_key:
            cached = get_cached(cache_scope, idempotency_key)
            if cached is not None:
                if json_out:
                    click.echo(json.dumps(cached, indent=2, ensure_ascii=False))
                else:
                    click.echo(f"Note added: {cached.get('data', {}).get('note_key', '?')} (cached).")
                return

        writer = build_writer(ctx, cfg, json_out, context="note")
        try:
            if standalone:
                note_key = writer.add_standalone_note(payload)
            else:
                assert key is not None
                note_key = writer.add_note(key, payload)
        except ZoteroWriteError as e:
            emit_error(
                e.code,
                str(e),
                output_json=json_out,
                retryable=e.retryable,
                hint="Check item key and API credentials",
                context="note",
            )

        env = envelope_ok(
            {"note_key": note_key, "parent_key": parent_for_preview, "sync_required": True},
            extra={"next": ["zot note --standalone"] if standalone else [f"zot note {key}"]},
        )
        if idempotency_key:
            store_cached(cache_scope, idempotency_key, env)
        if json_out:
            click.echo(json.dumps(env, indent=2, ensure_ascii=False))
        else:
            click.echo(f"Note added: {note_key}")
            click.echo(SYNC_REMINDER, err=True)
    else:
        with open_reader(ctx, cfg) as reader:
            if standalone:
                notes = reader.get_standalone_notes()
                not_found_msg = "No standalone notes found"
                not_found_hint = "Add one with: zot note --standalone --add 'content'"
            else:
                if key is None:
                    emit_error(
                        "validation_error",
                        "KEY is required (unless --standalone)",
                        output_json=json_out,
                        hint="Use: zot note KEY, or zot note --standalone",
                        context="note",
                    )
                notes = reader.get_notes(key)
                not_found_msg = f"No notes found for '{key}'"
                not_found_hint = "Add one with: zot note KEY --add 'content'"
            if not notes:
                emit_error(
                    "not_found",
                    not_found_msg,
                    output_json=json_out,
                    hint=not_found_hint,
                    context="note",
                )
            click.echo(format_notes(notes, output_json=json_out))
