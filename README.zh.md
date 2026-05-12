# Chrome Bookmarks To Obsidian

[English](README.md) | 中文

把 Chrome 收藏夹和 Obsidian 连接起来：继续用 Chrome 收藏网页，同时自动沉淀成本地 Markdown 知识库。

## 为什么做这个

这个项目来自一个很普通的使用习惯：我看到有价值的网页，会顺手收藏到 Chrome。

Chrome 收藏夹对我来说是最自然的捕捉入口：随手、低成本，而且同账号多设备同步。但我并没有“把每个网页保存成本地文件夹，再手动整理成 Obsidian 笔记”的习惯，也不想为了让知识库或 agent 用起来，每次都额外搬运一遍。

所以我想做的不是改变这个习惯，而是让工具适配这个习惯：

- Chrome 继续负责快速收藏链接。
- Obsidian 负责把这些链接整理成本地 Markdown 知识库。
- 后续人或 agent 可以从索引、大纲、来源笔记里读取上下文，而不是全库乱扫。

这个工具就是中间那座桥。它把一个 Chrome 收藏目录整理成 Obsidian 友好的网页知识库，包含总索引、分类大纲、来源笔记、去重状态和失败收件箱。

它不会把收藏夹当成完整真理库，只把它当作“我曾经主动保存过的局部线索”，方便后续检索、复核和继续研究。

## 它会做什么

- 读取 Chrome bookmark JSON；macOS 上优先读取同步书签 `AccountBookmarks`。
- 提取某个收藏目录下的链接，比如 `Other Bookmarks / Reading List`。
- 用直接 HTTP 抓取公开网页。
- 抽取网页内容，而不是整理网页外壳。它会优先读取文章正文、main 区域或 README 这类内容，并过滤导航、按钮、统计数字、登录提示、版权栏等页面元素。
- 写入 Obsidian 来源候选笔记、分类大纲和总索引。
- 用 `_registry.json` 做去重和重复运行状态记录。
- 把失败、受阻、需要登录、CAPTCHA 或需要浏览器辅助的页面写到 `_inbox/待处理.md`。
- 单独标记视频链接；如果没有 transcript，只会根据标题保留主题线索，写 `transcript_status: missing`，不会编造视频正文观点。

脚本生成的笔记不是最终知识笔记。它们会标记 `curation_status: needs_agent`，后续由 agent 或人工阅读候选内容，再写真正的“一句话摘要”“关键观点”“适合用于”和“局限”。

每条生成笔记都会写入 `summary_basis`：

- `content`：候选摘录来自抽取到的正文内容，比如文章正文或 README。
- `title`：没有 transcript 或正文，只保留标题推断出的主题线索。
- `metadata`：只抽到了页面 UI 或元数据；这只是待复核占位，不是正文摘要。

## 安全边界

- 只保存候选摘录和整理状态，不保存完整文章归档。
- 不绕过登录墙、付费墙、CAPTCHA 或明确受保护的页面。
- 不把 HTML 元素、导航文字、浏览器提示、GitHub UI、CSDN 阅读量等页面外壳当成来源内容来总结。
- 不把最终内容组织写死；真正的摘要、关键观点、用途和局限，应由 agent 或人工读完来源后整理。
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

如果不想每次写 `--bookmark-folder`，可以在本机设置：

```bash
export CHROME_BOOKMARKS_TO_OBSIDIAN_FOLDER="其他书签 / 知识库"
```

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
