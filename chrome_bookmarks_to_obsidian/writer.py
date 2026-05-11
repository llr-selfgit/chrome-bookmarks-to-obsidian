import json
import re
from pathlib import Path
from typing import Dict, Iterable

from chrome_bookmarks_to_obsidian.bookmarks import Bookmark
from chrome_bookmarks_to_obsidian.config import BOUNDARY_TEXT
from chrome_bookmarks_to_obsidian.fetcher import FetchResult
from chrome_bookmarks_to_obsidian.registry import now_iso


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text).strip("-").lower()
    return slug[:80] or "source"


def _md_list(items: Iterable[object]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _yaml_string(value: object) -> str:
    return json.dumps(str(value), ensure_ascii=False)


class ObsidianWriter:
    def __init__(self, root: Path):
        self.root = root

    def ensure_base(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "_inbox").mkdir(parents=True, exist_ok=True)
        index_path = self.root / "知识库索引.md"
        if not index_path.exists():
            index_path.write_text(
                f"# 网页知识库索引\n\n## 使用边界\n\n{BOUNDARY_TEXT}\n\n## 分类地图\n\n",
                encoding="utf-8",
            )

    def write_imported_source(
        self,
        bookmark: Bookmark,
        fetch: FetchResult,
        category: str,
        summary: Dict[str, object],
        content_hash: str,
    ) -> Path:
        self.ensure_base()
        category_dir = self.root / category
        source_dir = category_dir / "sources"
        source_dir.mkdir(parents=True, exist_ok=True)
        source_path = source_dir / f"{slugify(bookmark.title)}.md"
        timestamp = now_iso()
        media_type = fetch.media_type or "article"
        transcript_status = fetch.transcript_status or "not_applicable"
        video_status = ""
        if media_type == "video" and transcript_status != "available":
            video_status = (
                "\n## 内容状态\n\n"
                "- 未获取到视频转录文本；当前摘要只基于可见页面文本或元数据。\n"
                "- 后续如果需要准确理解视频内容，应补充 transcript 或人工整理。\n"
            )
        content = f"""---
type: web-source
source_type: chrome_bookmark
coverage: partial
not_authoritative: true
url: {_yaml_string(bookmark.url)}
canonical_url: {_yaml_string(fetch.canonical_url or bookmark.url)}
title: {_yaml_string(bookmark.title)}
site: {_yaml_string(fetch.site)}
bookmark_path: {_yaml_string(" / ".join(bookmark.bookmark_path))}
category: {_yaml_string(category)}
retrieval_method: {_yaml_string(fetch.retrieval_method)}
media_type: {media_type}
transcript_status: {transcript_status}
imported_at: {_yaml_string(timestamp)}
last_checked_at: {_yaml_string(timestamp)}
content_hash: {_yaml_string(content_hash)}
status: active
---

# {bookmark.title}

## 一句话摘要

{summary["one_line"]}

## 关键观点

{_md_list(summary["key_points"])}

## 适合用于

{_md_list(summary["use_cases"])}

## 局限和需复核点

{_md_list(summary["limitations"])}
{video_status}
## 来源链接

- {bookmark.url}
"""
        source_path.write_text(content, encoding="utf-8")
        self._update_category_outline(category, source_path, summary)
        self._update_global_index(category)
        return source_path

    def _update_global_index(self, category: str) -> None:
        index_path = self.root / "知识库索引.md"
        content = index_path.read_text(encoding="utf-8")
        entry = f"- [[{category}/大纲|{category}]]"
        if entry not in content:
            content = content.rstrip() + f"\n{entry}\n"
            index_path.write_text(content, encoding="utf-8")

    def _update_category_outline(self, category: str, source_path: Path, summary: Dict[str, object]) -> None:
        outline_path = self.root / category / "大纲.md"
        relative = source_path.relative_to(self.root).with_suffix("")
        link_prefix = f"[[{relative.as_posix()}|"
        entry = f"- [[{relative.as_posix()}|{source_path.stem}]] - {summary['one_line']}"
        if outline_path.exists():
            content = outline_path.read_text(encoding="utf-8")
            lines = [line for line in content.splitlines() if link_prefix not in line]
            content = "\n".join(lines).rstrip() + f"\n{entry}\n"
        else:
            content = (
                f"# {category} 大纲\n\n"
                f"## 分类摘要\n\n这个分类由 Chrome 收藏夹自动导入，内容是局部来源集合。\n\n"
                f"## 主要来源\n\n{entry}\n\n"
                "## 共同结论\n\n- 待积累更多来源后整理。\n\n"
                "## 分歧和需复核点\n\n- 收藏来源不等于完整证据，需要按任务重新核验。\n\n"
                f"## 最后更新\n\n{now_iso()}\n"
            )
        outline_path.write_text(content, encoding="utf-8")

    def record_failure(self, bookmark: Bookmark, reason: str) -> Path:
        self.ensure_base()
        inbox_path = self.root / "_inbox" / "待处理.md"
        existing = inbox_path.read_text(encoding="utf-8") if inbox_path.exists() else "# 待处理网页\n\n"
        entry = f"- [{now_iso()}] `{reason}`: [{bookmark.title}]({bookmark.url})"
        if bookmark.url not in existing:
            existing = existing.rstrip() + f"\n{entry}\n"
        inbox_path.write_text(existing, encoding="utf-8")
        return inbox_path
