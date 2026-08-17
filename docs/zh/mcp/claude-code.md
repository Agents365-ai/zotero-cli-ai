# 搭配 Claude Code 使用

!!! tip "Agent-native 接口（0.3.0+）"
    当 stdout 不是 TTY 时，`zot` 自动输出 JSON envelope，Claude Code 无需加
    `--json` 就能拿到可解析的结构化输出。退出码已按类别细分（校验、鉴权、
    未找到、网络、冲突），每个 envelope 携带 `meta.request_id`，所有写命令
    支持 `--dry-run` 和 `--idempotency-key`。完整契约见：[Agent Interface](../reference/agent-interface.md)。

## 安装 Skill

复制 zotero-cli skill，让 Claude Code 自动识别文献相关请求：

```bash
cp -r skill/zotero-cli ~/.claude/skills/
```

## 工作原理

安装 skill 后，Claude Code 会在你提到论文时自动使用 `zot` 命令：

```
搜索我的 Zotero 中关于单细胞的论文
→ Claude 运行: zot --json search "single cell"

查看这篇论文的详情
→ Claude 运行: zot --json read ABC123

导出这些论文的 BibTeX
→ Claude 运行: zot export ABC123

为我的 ICML 投稿创建一个集合
→ Claude 运行: zot collection create "ICML 2026"
```

## 集合工作流

任何深度搜索或提问都可以限定在某个 Zotero 集合内。Claude Code 的典型科研工作流：

1. **创建集合** — 为你的项目建立文献集
2. **添加论文** — 在 Zotero 应用中操作，或用 `zot collection move`
3. **提问** — 无需构建索引，结果始终最新

```
创建一个叫 "llm-safety" 的集合来放我的 alignment 论文
→ Claude 运行: zot collection create "llm-safety"

这些论文使用了哪些方法来检测 reward hacking？
→ Claude 运行: zot ask "reward hacking detection methods" --collection llm-safety
  并基于返回的证据包综合出带引用的答案
```

## Shell 自动补全

启用 tab 自动补全以加速 CLI 使用：

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
