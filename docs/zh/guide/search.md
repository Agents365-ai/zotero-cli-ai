# 搜索与浏览

## 搜索原理

`zot search` 在四个层面进行关键词匹配：

1. **标题与摘要** — 直接文本匹配
2. **作者姓名** — 姓和名匹配
3. **标签** — 精确标签匹配
4. **PDF 全文索引** — Zotero 内置的全文索引

## 选择搜索命令

- **`zot search`** — 跨元数据和全文索引的快速关键词查找（本页内容）。
- **[`zot workspace query`](workspace.md)** — 对自然语言问题进行排序深度检索，可限定在某个集合内。无索引：结果始终最新。
- **`zot ask`** — 同样的排序检索，但返回带引用键的证据包（元数据 + PDF 片段），供 Agent 综合答案。

## 基本搜索

```bash
zot search "transformer attention"
```

## 按集合过滤

```bash
zot search "BERT" --collection "NLP"
```

## 按条目类型过滤

```bash
zot search "protein" --type journalArticle
```

常用类型：`journalArticle`、`conferencePaper`、`preprint`、`book`、`bookSection`、`thesis`

## 排序结果

```bash
zot search "attention" --sort dateAdded --direction desc
zot search "attention" --sort title --direction asc
```

排序字段：`dateAdded`、`dateModified`、`title`、`creator`

## 列出所有条目

```bash
zot list --limit 20
zot list --collection "Machine Learning"
```

## 最近添加的条目

```bash
zot recent                    # 最近 7 天（默认）
zot recent --days 30          # 最近 30 天
zot recent --days 7 --modified  # 最近修改的
```

## 查看条目详情

```bash
zot read ABC123
```

显示元数据、摘要和笔记。使用 `--detail full` 查看所有字段。

## 查找相关条目

```bash
zot relate ABC123
```

查找共享标签、集合或显式关联的条目。

## 详情级别

```bash
zot --detail minimal search "attention"   # 仅显示键、标题、作者、年份
zot --detail standard read ABC123         # 默认 — 包含摘要、标签、DOI
zot --detail full read ABC123             # 所有字段，包括额外元数据
```

## JSON 输出

```bash
zot --json search "attention"
```

所有命令都支持 `--json` 获取机器可读输出。

## 文献库统计

```bash
zot stats
```

显示总条目数、PDF 数、笔记数、按类型分类、集合信息和热门标签。
