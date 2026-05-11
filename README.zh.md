# Chrome Bookmarks To Obsidian

[English](README.md) | 中文

把一个专门的 Chrome 收藏夹整理成结构化的 Obsidian 网页知识库。

## 为什么做这个

很多人会把有价值的网页先丢进 Chrome 收藏夹：文章、GitHub repo、Reddit 讨论、教程、视频、产品页、参考文档。时间一长，收藏夹很容易变成一个安静的待办黑洞：

- 链接有了，但没有摘要和分类。
- 同一主题的来源散在不同地方。
- Obsidian 里没有对应索引。
- AI coding agent 也不知道该读哪里。
- 真要用这些资料时，还是要重新人工整理。

这个工具想做一件很小但很实用的事：把一个 Chrome 收藏目录自动整理成 Obsidian 里的 Markdown 知识库。它会生成总索引、分类大纲、来源笔记、去重状态和失败收件箱。

它不会把收藏夹当成完整真理库，只把它当作“你曾经主动保存过的局部线索”，方便人和 agent 后续检索、复核、继续研究。

## 它会做什么

- 读取 Chrome bookmark JSON；macOS 上优先读取同步书签 `AccountBookmarks`。
- 提取某个收藏目录下的链接，比如 `Other Bookmarks / Reading List`。
- 用直接 HTTP 抓取公开网页。
- 写入简洁的 Obsidian 来源笔记、分类大纲和总索引。
- 用 `_registry.json` 做去重和重复运行状态记录。
- 把失败、受阻、需要登录、CAPTCHA 或需要浏览器辅助的页面写到 `_inbox/待处理.md`。
- 单独标记视频链接；如果没有 transcript，会写 `transcript_status: missing`，不会根据标题编造视频内容总结。

## 安全边界

- 只保存摘要和关键观点，不保存完整文章归档。
- 不绕过登录墙、付费墙、CAPTCHA 或明确受保护的页面。
- 生成的知识库只是局部收藏来源，不是权威资料库。
- 时效性或高风险问题仍需回到原始来源或外部资料核验。

## 环境要求

- Python 3.9+
- Chrome 或 Chromium bookmark JSON
- Obsidian vault，或者任意可写 Markdown 的目录

V1 主要在 macOS 上测试。其他系统可以用 `--bookmark-file` 指定浏览器书签 JSON 路径。

## 安装

```bash
git clone https://github.com/llr-selfgit/chrome-bookmarks-to-obsidian.git
cd chrome-bookmarks-to-obsidian
python3 -m pip install -e .
```

也可以不安装，直接运行：

```bash
python3 -m chrome_bookmarks_to_obsidian.cli --help
```

## 快速开始

先创建一个专门的 Chrome 收藏目录，例如：

```text
Other Bookmarks / Reading List
```

先预览会导入什么：

```bash
chrome-bookmarks-to-obsidian \
  --bookmark-folder "Other Bookmarks / Reading List" \
  --output-root "$HOME/Documents/Obsidian Vault/80_web_knowledge_base" \
  --dry-run
```

确认后再真实导入：

```bash
chrome-bookmarks-to-obsidian \
  --bookmark-folder "Other Bookmarks / Reading List" \
  --output-root "$HOME/Documents/Obsidian Vault/80_web_knowledge_base"
```

如果 Chrome 是中文界面，用收藏夹里的实际路径：

```bash
chrome-bookmarks-to-obsidian \
  --bookmark-folder "其他书签 / 知识库" \
  --output-root "$HOME/Documents/Obsidian Vault/80_web_knowledge_base"
```

## 常用参数

```bash
chrome-bookmarks-to-obsidian --help
```

常用参数：

- `--bookmark-folder`：Chrome 收藏夹内部路径，用 `/` 分隔。
- `--bookmark-file`：手动指定 Chrome bookmark JSON 文件。
- `--output-root`：Obsidian 网页知识库输出目录。
- `--dry-run`：只预览，不写入。
- `--limit`：只处理前 N 条，用于烟测。

## 输出结构

```text
80_web_knowledge_base/
  知识库索引.md
  _registry.json
  _inbox/
    待处理.md
  AI Agent/
    大纲.md
    sources/
      example-source.md
```

建议 agent 读取路径：

1. 先读 `知识库索引.md`。
2. 选择 1-3 个相关分类大纲。
3. 只读取任务需要的少量来源笔记。
4. 把这些笔记当作用户收藏过的上下文线索，不要当成唯一事实来源。

## 开发

```bash
python3 -m unittest discover chrome_bookmarks_to_obsidian/tests -v
```

## 当前状态

这是一个很小的 V1。后续可以继续做：

- 针对公开动态页面的浏览器辅助抓取；
- 视频 transcript 抽取；
- 更好的中英文笔记模板；
- 定时自动导入。

