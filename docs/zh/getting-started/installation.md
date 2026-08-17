# 安装

## 环境要求

- Python 3.10 或更高版本
- 本地安装的 Zotero（用于读取 SQLite 数据库）

## 安装

=== "uv（推荐）"

    ```bash
    uv tool install zotero-cli-ai
    ```

=== "pipx"

    ```bash
    pipx install zotero-cli-ai
    ```

=== "pip"

    ```bash
    pip install zotero-cli-ai
    ```

## 升级

=== "uv"

    ```bash
    uv tool upgrade zotero-cli-ai
    ```

=== "pipx"

    ```bash
    pipx upgrade zotero-cli-ai
    ```

=== "pip"

    ```bash
    pip install -U zotero-cli-ai
    ```

## MCP 支持

如需将 zotero-cli-ai 用作 MCP 服务器（适用于 Claude Desktop、Cursor、LM Studio）：

```bash
pip install zotero-cli-ai[mcp]
```

## 验证安装

```bash
zot --version
```
