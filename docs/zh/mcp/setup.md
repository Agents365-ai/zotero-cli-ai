# MCP 服务器配置

zotero-cli-ai 支持 [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)，可在兼容 MCP 的 AI 客户端中使用。

## 安装 MCP 支持

```bash
pip install zotero-cli-ai[mcp]
```

## 启动服务器

```bash
zot mcp serve
```

## 客户端配置

=== "Claude Desktop"

    编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）或 `%APPDATA%\Claude\claude_desktop_config.json`（Windows）：

    ```json
    {
      "mcpServers": {
        "zotero": {
          "command": "zot",
          "args": ["mcp", "serve"]
        }
      }
    }
    ```

=== "Cursor"

    编辑项目或全局设置中的 `.cursor/mcp.json`：

    ```json
    {
      "mcpServers": {
        "zotero": {
          "command": "zot",
          "args": ["mcp", "serve"]
        }
      }
    }
    ```

=== "LM Studio"

    在 LM Studio 设置中添加 MCP 服务器：

    ```json
    {
      "mcpServers": {
        "zotero": {
          "command": "zot",
          "args": ["mcp", "serve"]
        }
      }
    }
    ```

## 验证连接

配置完成后，AI 客户端应显示 45 个可用的 Zotero 工具。尝试提问：

> "搜索我的 Zotero 文献库中关于注意力机制的论文"
