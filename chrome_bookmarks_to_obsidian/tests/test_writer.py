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
                "one_line": "Codex quickstart introduces setup.",
                "key_points": ["Install Codex.", "Use it for agentic work."],
                "use_cases": ["Agent workflow setup"],
                "limitations": ["Check latest docs before relying on commands."],
            }
            note_path = writer.write_imported_source(bookmark, fetch, "AI Agent", summary, "abc")
            self.assertTrue(note_path.exists())
            self.assertTrue((root / "知识库索引.md").exists())
            self.assertTrue((root / "AI Agent" / "大纲.md").exists())
            self.assertIn("not_authoritative: true", note_path.read_text(encoding="utf-8"))
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
                "one_line": "Video metadata only.",
                "key_points": ["Only title and metadata were available."],
                "use_cases": ["Follow up with transcript extraction."],
                "limitations": ["No transcript was available."],
            }
            note_path = writer.write_imported_source(bookmark, fetch, "Obsidian", summary, "hash")
            content = note_path.read_text(encoding="utf-8")
            self.assertIn("media_type: video", content)
            self.assertIn("transcript_status: missing", content)
            self.assertIn("未获取到视频转录文本", content)

    def test_rewriting_same_source_updates_outline_without_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            writer = ObsidianWriter(root)
            bookmark = Bookmark("Codex Quickstart", "https://developers.openai.com/codex/quickstart", ["其他书签", "知识库"])
            fetch = FetchResult(bookmark.url, bookmark.title, "Agent memory context tools", "developers.openai.com", bookmark.url, "direct_http", "ok")
            first = {
                "one_line": "Old summary.",
                "key_points": ["Old."],
                "use_cases": ["Setup."],
                "limitations": ["Recheck."],
            }
            second = {
                "one_line": "New summary.",
                "key_points": ["New."],
                "use_cases": ["Setup."],
                "limitations": ["Recheck."],
            }
            writer.write_imported_source(bookmark, fetch, "AI Agent", first, "abc")
            note_path = writer.write_imported_source(bookmark, fetch, "AI Agent", second, "abc")
            outline = (root / "AI Agent" / "大纲.md").read_text(encoding="utf-8")
            self.assertEqual(outline.count(f"[[AI Agent/sources/{note_path.stem}|"), 1)
            self.assertIn("New summary.", outline)
            self.assertNotIn("Old summary.", outline)


if __name__ == "__main__":
    unittest.main()
