# Chrome Bookmarks To Obsidian

English | [中文](README.zh.md)

Connect a Chrome bookmark folder to an Obsidian web knowledge base, without changing the habit of saving links in Chrome.

## Why This Exists

This project started from a very ordinary habit: I save useful web pages in Chrome bookmarks.

Chrome is the easiest capture point for me. It is always there, it works across devices, and saving a page takes almost no thought. What I do **not** naturally do is save every useful page into a local folder, create a Markdown note, classify it, and then keep an index updated in Obsidian.

So instead of asking myself to change that habit, I wanted the tool to adapt to it:

- Chrome bookmarks remain the lightweight place to save links.
- Obsidian becomes the local place where those links are organized into Markdown.
- Agents can later read the index, outlines, and source notes without scanning an entire vault.

This tool is that bridge. It turns one Chrome bookmark folder into an Obsidian-friendly web knowledge base with a top-level index, category outlines, source notes, duplicate tracking, and a visible inbox for pages that need review.

It does **not** treat bookmarks as a complete source of truth. It treats them as user-curated starting points: links you cared enough to save, ready to be organized, revisited, and checked later.

## What It Does

- Reads Chrome bookmark JSON, preferring synced `AccountBookmarks` on macOS.
- Extracts bookmarks under one folder path, such as `Other Bookmarks / Reading List`.
- Fetches public web pages with direct HTTP.
- Writes concise Obsidian source notes, category outlines, and a top-level index.
- Keeps `_registry.json` for duplicate detection and reruns.
- Records failed, blocked, login-only, CAPTCHA, or browser-needed pages in `_inbox/待处理.md`.
- Marks video links separately. If no transcript is available, it records `transcript_status: missing` instead of inventing a summary.

## Safety Boundaries

- Stores summaries and key points, not full article archives.
- Does not bypass login walls, paywalls, CAPTCHAs, or explicitly protected pages.
- Treats the generated knowledge base as partial and non-authoritative.
- For time-sensitive or high-stakes topics, re-check the original source or use external research.

## Requirements

- Python 3.9+
- Chrome or Chromium bookmark JSON
- An Obsidian vault, or any folder where Markdown files can be written

V1 is tested on macOS. On other systems, pass `--bookmark-file` with the path to your browser bookmark JSON.

## Install

```bash
git clone https://github.com/llr-selfgit/chrome-bookmarks-to-obsidian.git
cd chrome-bookmarks-to-obsidian
python3 -m pip install -e .
```

You can also run it without installing:

```bash
python3 -m chrome_bookmarks_to_obsidian.cli --help
```

## Quick Start

Create a dedicated Chrome bookmark folder, for example:

```text
Other Bookmarks / Reading List
```

Preview what would be imported:

```bash
chrome-bookmarks-to-obsidian \
  --bookmark-folder "Other Bookmarks / Reading List" \
  --output-root "$HOME/Documents/Obsidian Vault/80_web_knowledge_base" \
  --dry-run
```

If the preview looks right, run the import:

```bash
chrome-bookmarks-to-obsidian \
  --bookmark-folder "Other Bookmarks / Reading List" \
  --output-root "$HOME/Documents/Obsidian Vault/80_web_knowledge_base"
```

For a localized Chrome UI, use the exact folder names from your bookmark tree:

```bash
chrome-bookmarks-to-obsidian \
  --bookmark-folder "其他书签 / 知识库" \
  --output-root "$HOME/Documents/Obsidian Vault/80_web_knowledge_base"
```

## Useful Options

```bash
chrome-bookmarks-to-obsidian --help
```

Common options:

- `--bookmark-folder`: folder path inside Chrome bookmarks, separated by `/`.
- `--bookmark-file`: explicit Chrome bookmark JSON path.
- `--output-root`: output folder for the Obsidian web knowledge base.
- `--dry-run`: show what would be processed without writing notes.
- `--limit`: process only the first N bookmarks, useful for smoke tests.

## Output Structure

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

Suggested agent reading path:

1. Read `知识库索引.md`.
2. Pick 1-3 relevant category outlines.
3. Read only a few source notes needed for the task.
4. Use these notes as user-curated context, not as the only source of truth.

## Development

```bash
python3 -m unittest discover chrome_bookmarks_to_obsidian/tests -v
```

## Status

This is a small V1. Good next steps:

- browser-assisted extraction for public dynamic pages;
- optional transcript extraction for videos;
- better multilingual note templates;
- scheduled imports.
