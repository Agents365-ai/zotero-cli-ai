# 笔记与标签

## 查看笔记

```bash
zot note ABC123
```

显示附加到条目的所有笔记，从 HTML 转换为 Markdown。

## 添加笔记

```bash
zot note ABC123 --add "这篇论文提出了一种新的注意力机制"
```

!!! note "写入操作需要 API 凭据"
    请参阅 [配置](../getting-started/setup.md#api) 来设置 API 密钥。

## 更新笔记

可以通过 MCP 工具（`note_update`）更新笔记。参见 [MCP 工具参考](../mcp/tools.md)。

## 查看标签

```bash
zot tag ABC123
```

## 添加标签

```bash
zot tag ABC123 --add "important"
zot tag ABC123 --add "to-read" --add "attention"
```

## 删除标签

```bash
zot tag ABC123 --remove "to-read"
```

## 批量标签操作

可以通过 MCP 工具（`tag_add`、`tag_remove`）批量操作多个条目的标签。参见 [MCP 工具参考](../mcp/tools.md)。
