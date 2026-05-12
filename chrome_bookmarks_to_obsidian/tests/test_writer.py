import tempfile
import unittest
from pathlib import Path

from chrome_bookmarks_to_obsidian.bookmarks import Bookmark
from chrome_bookmarks_to_obsidian.fetcher import FetchResult
from chrome_bookmarks_to_obsidian.writer import ObsidianWriter


class WriterTests(unittest.TestCase):
    def test_writes_source_note_indexes_and_inbox(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            writer = ObsidianWriter(root)
            bookmark = Bookmark("Codex Quickstart", "https://developers.openai.com/codex/quickstart", ["其他书签", "知识库"])
            fetch = FetchResult(bookmark.url, bookmark.title, "Agent memory context tools", "developers.openai.com", bookmark.url, "direct_http", "ok")
            summary = {
                "summary_basis": "content",
                "curation_status": "needs_agent",
                "one_line": "Codex quickstart introduces setup.",
                "candidate_excerpts": ["Install Codex.", "Use it for agentic work."],
                "limitations": ["Check latest docs before relying on commands."],
            }
            note_path = writer.write_imported_source(bookmark, fetch, "AI Agent", summary, "abc")
            self.assertTrue(note_path.exists())
            self.assertTrue((root / "知识库索引.md").exists())
            self.assertTrue((root / "AI Agent" / "大纲.md").exists())
            content = note_path.read_text(encoding="utf-8")
            self.assertIn("coverage: partial", content)
            self.assertIn("summary_basis: content", content)
            self.assertIn("curation_status: needs_agent", content)
            self.assertIn("status: candidate", content)
            self.assertIn("## Agent 整理状态", content)
            self.assertIn("## 待 Agent 整理", content)
            self.assertIn("not_authoritative: true", content)
            writer.record_failure(bookmark, "fetch failed")
            self.assertIn("fetch failed", (root / "_inbox" / "待处理.md").read_text(encoding="utf-8"))

    def test_video_note_marks_missing_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            writer = ObsidianWriter(root)
            bookmark = Bookmark("Obsidian Video", "https://www.youtube.com/watch?v=AnyAbiXOf8g", ["其他书签", "知识库"])
            fetch = FetchResult(
                bookmark.url,
                bookmark.title,
                "Only visible metadata.",
                "www.youtube.com",
                bookmark.url,
                "direct_http",
                "ok",
                media_type="video",
                transcript_status="missing",
            )
            summary = {
                "summary_basis": "title",
                "curation_status": "needs_agent",
                "one_line": "Video metadata only.",
                "candidate_excerpts": ["Only title and metadata were available."],
                "limitations": ["No transcript was available."],
            }
            note_path = writer.write_imported_source(bookmark, fetch, "Obsidian", summary, "hash")
            content = note_path.read_text(encoding="utf-8")
            self.assertIn("coverage: title_only", content)
            self.assertIn("media_type: video", content)
            self.assertIn("transcript_status: missing", content)
            self.assertIn("summary_basis: title", content)
            self.assertIn("curation_status: needs_agent", content)

    def test_rewriting_same_source_updates_outline_without_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            writer = ObsidianWriter(root)
            bookmark = Bookmark("Codex Quickstart", "https://developers.openai.com/codex/quickstart", ["其他书签", "知识库"])
            fetch = FetchResult(bookmark.url, bookmark.title, "Agent memory context tools", "developers.openai.com", bookmark.url, "direct_http", "ok")
            first = {
                "summary_basis": "content",
                "curation_status": "needs_agent",
                "one_line": "Old summary.",
                "candidate_excerpts": ["Old."],
                "limitations": ["Recheck."],
            }
            second = {
                "summary_basis": "content",
                "curation_status": "needs_agent",
                "one_line": "New summary.",
                "candidate_excerpts": ["New."],
                "limitations": ["Recheck."],
            }
            writer.write_imported_source(bookmark, fetch, "AI Agent", first, "abc")
            note_path = writer.write_imported_source(bookmark, fetch, "AI Agent", second, "abc")
            outline = (root / "AI Agent" / "大纲.md").read_text(encoding="utf-8")
            self.assertEqual(outline.count(f"[[AI Agent/sources/{note_path.stem}|"), 1)
            self.assertIn("New summary.", outline)
            self.assertNotIn("Old summary.", outline)
            self.assertLess(outline.index("[[AI Agent/sources/"), outline.index("## 共同结论"))


if __name__ == "__main__":
    unittest.main()
