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


def _coverage_for_summary_basis(summary_basis: str) -> str:
    if summary_basis == "title":
        return "title_only"
    if summary_basis == "metadata":
        return "metadata_only"
    return "partial"


def _curation_status(summary: Dict[str, object]) -> str:
    return str(summary.get("curation_status") or "needs_agent")


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
        summary_basis = str(summary.get("summary_basis") or "content")
        curation_status = _curation_status(summary)
        coverage = _coverage_for_summary_basis(summary_basis)
        body = self._source_body(bookmark, summary, summary_basis, curation_status)
        content = f"""---
type: web-source
source_type: chrome_bookmark
coverage: {coverage}
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
summary_basis: {summary_basis}
curation_status: {curation_status}
imported_at: {_yaml_string(timestamp)}
last_checked_at: {_yaml_string(timestamp)}
content_hash: {_yaml_string(content_hash)}
status: {"candidate" if curation_status == "needs_agent" else "active"}
---

# {bookmark.title}

{body}

## 来源链接

- {bookmark.url}
"""
        source_path.write_text(content, encoding="utf-8")
        self._update_category_outline(category, source_path, summary)
        self._update_global_index(category)
        return source_path

    def _source_body(
        self,
        bookmark: Bookmark,
        summary: Dict[str, object],
        summary_basis: str,
        curation_status: str,
    ) -> str:
        if curation_status != "needs_agent":
            return f"""## 一句话摘要

{summary["one_line"]}

## 关键观点

{_md_list(summary["key_points"])}

## 适合用于

{_md_list(summary["use_cases"])}

## 局限和需复核点

{_md_list(summary["limitations"])}
"""

        excerpts = summary.get("candidate_excerpts") or []
        return f"""## Agent 整理状态

- curation_status: needs_agent
- summary_basis: {summary_basis}
- 当前脚本只完成抓取、正文抽取和去噪；以下内容是候选材料，不是最终摘要。
- 不要把网页导航、按钮、统计栏、登录提示、版权栏等页面外壳整理成知识内容。

## 候选内容

{_md_list(excerpts)}

## 待 Agent 整理

- 阅读候选内容和原始链接，判断网页正文真正讲了什么。
- 生成具体的“一句话摘要”“关键观点”“适合用于”“局限和需复核点”。
- 如果只有标题、元数据或 transcript 缺失，明确保留限制，不要编造正文观点。

## 局限和需复核点

{_md_list(summary["limitations"])}
"""

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
            lines = content.splitlines()
            existing_entries = [
                line
                for line in lines
                if line.startswith("- [[") and link_prefix not in line
            ]
            lines = [line for line in lines if not line.startswith("- [[")]
            entries = existing_entries + [entry]
            content = self._insert_outline_sources(lines, entries)
            content = self._update_outline_timestamp(content)
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

    def _insert_outline_sources(self, lines: list, entries: list) -> str:
        try:
            heading_index = lines.index("## 主要来源")
        except ValueError:
            lines.extend(["", "## 主要来源", ""])
            heading_index = len(lines) - 2

        insert_at = heading_index + 1
        while insert_at < len(lines) and not lines[insert_at].startswith("## "):
            del lines[insert_at]

        lines[insert_at:insert_at] = ["", *entries, ""]
        return "\n".join(lines).rstrip() + "\n"

    def _update_outline_timestamp(self, content: str) -> str:
        lines = content.splitlines()
        timestamp = now_iso()
        try:
            heading_index = lines.index("## 最后更新")
        except ValueError:
            return content.rstrip() + f"\n\n## 最后更新\n\n{timestamp}\n"

        value_index = heading_index + 1
        while value_index < len(lines) and not lines[value_index].strip():
            value_index += 1
        if value_index < len(lines) and not lines[value_index].startswith("## "):
            lines[value_index] = timestamp
        else:
            lines.insert(heading_index + 1, "")
            lines.insert(heading_index + 2, timestamp)
        return "\n".join(lines).rstrip() + "\n"

    def record_failure(self, bookmark: Bookmark, reason: str) -> Path:
        self.ensure_base()
        inbox_path = self.root / "_inbox" / "待处理.md"
        existing = inbox_path.read_text(encoding="utf-8") if inbox_path.exists() else "# 待处理网页\n\n"
        entry = f"- [{now_iso()}] `{reason}`: [{bookmark.title}]({bookmark.url})"
        if bookmark.url not in existing:
            existing = existing.rstrip() + f"\n{entry}\n"
        inbox_path.write_text(existing, encoding="utf-8")
        return inbox_path
