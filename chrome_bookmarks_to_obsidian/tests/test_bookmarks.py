import json
import unittest
from pathlib import Path

from chrome_bookmarks_to_obsidian.bookmarks import Bookmark, extract_bookmarks_under_path, load_bookmark_file

FIXTURES = Path(__file__).parent / "fixtures"


class BookmarkTests(unittest.TestCase):
    def test_empty_target_folder_returns_empty_list(self):
        data = json.loads((FIXTURES / "account_bookmarks_empty.json").read_text())
        bookmarks = extract_bookmarks_under_path(data, ["其他书签", "知识库"])
        self.assertEqual(bookmarks, [])

    def test_extracts_nested_bookmarks_under_target_folder(self):
        data = json.loads((FIXTURES / "account_bookmarks_nested.json").read_text())
        bookmarks = extract_bookmarks_under_path(data, ["其他书签", "知识库"])
        self.assertEqual(len(bookmarks), 1)
        self.assertIsInstance(bookmarks[0], Bookmark)
        self.assertEqual(bookmarks[0].title, "Codex Quickstart")
        self.assertEqual(bookmarks[0].url, "https://developers.openai.com/codex/quickstart")
        self.assertEqual(bookmarks[0].bookmark_path, ["其他书签", "知识库", "Agent"])

    def test_extracts_existing_like_bookmarks_under_target_folder_only(self):
        data = json.loads((FIXTURES / "account_bookmarks_existing.json").read_text())
        bookmarks = extract_bookmarks_under_path(data, ["其他书签", "知识库"])
        urls = [bookmark.url for bookmark in bookmarks]
        self.assertEqual(len(bookmarks), 5)
        self.assertIn("https://github.com/example/agent-harness", urls)
        self.assertIn("https://github.com/example/markdown-knowledge-base", urls)
        self.assertNotIn("https://example.com/outside", urls)

    def test_missing_folder_raises_clear_error(self):
        data = json.loads((FIXTURES / "account_bookmarks_empty.json").read_text())
        with self.assertRaisesRegex(ValueError, "Bookmark folder not found"):
            extract_bookmarks_under_path(data, ["其他书签", "missing"])

    def test_load_bookmark_file_reports_invalid_json_path(self):
        bad_path = FIXTURES / "bad.json"
        bad_path.write_text("{bad json", encoding="utf-8")
        try:
            with self.assertRaisesRegex(ValueError, str(bad_path)):
                load_bookmark_file(bad_path)
        finally:
            bad_path.unlink()


if __name__ == "__main__":
    unittest.main()
