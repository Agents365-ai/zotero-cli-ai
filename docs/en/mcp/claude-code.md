# Using with Claude Code

!!! tip "Agent-native interface (0.3.0+)"
    `zot` auto-emits JSON envelopes when stdout is not a TTY, so Claude Code gets
    parseable output without `--json`. Exit codes are typed (validation, auth,
    not-found, network, conflict), every envelope carries a `meta.request_id`,
    and mutating commands support `--dry-run` and `--idempotency-key`.
    Full contract: [Agent Interface](../reference/agent-interface.md).

## Install the Skill

Copy the zotero-cli skill so Claude Code automatically recognizes literature-related requests:

```bash
cp -r skill/zotero-cli ~/.claude/skills/
```

## How It Works

With the skill installed, Claude Code automatically uses `zot` commands when you ask about papers:

```
Search my Zotero for single cell papers
→ Claude runs: zot --json search "single cell"

Show me details of this paper
→ Claude runs: zot --json read ABC123

Export BibTeX for these papers
→ Claude runs: zot export ABC123

Create a collection for my ICML submission
→ Claude runs: zot collection create "ICML 2026"
```

## Workspace Workflow

A workspace is simply a Zotero collection. A typical research workflow with Claude Code:

1. **Create a collection** for your project
2. **Add papers** to it — in the Zotero app, or with `zot collection move`
3. **Ask questions** — no index to build, results are always fresh

```
Create a collection called "llm-safety" for my alignment papers
→ Claude runs: zot collection create "llm-safety"

What methods do these papers use for reward hacking detection?
→ Claude runs: zot ask "reward hacking detection methods" --workspace llm-safety
  and synthesizes a cited answer from the returned evidence pack
```

## Shell Completions

Enable tab completions for faster CLI use:

=== "Zsh"

    ```bash
    zot completions zsh >> ~/.zshrc
    ```

=== "Bash"

    ```bash
    zot completions bash >> ~/.bashrc
    ```

=== "Fish"

    ```bash
    zot completions fish > ~/.config/fish/completions/zot.fish
    ```
