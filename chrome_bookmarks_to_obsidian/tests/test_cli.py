import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from chrome_bookmarks_to_obsidian.cli import run_import


class CliTests(unittest.TestCase):
    def test_empty_folder_writes_base_files_and_imports_zero(self):
        fixture = Path(__file__).parent / "fixtures" / "account_bookmarks_empty.json"
        with tempfile.TemporaryDirectory() as tmp:
            result = run_import(
                bookmark_file=fixture,
                output_root=Path(tmp),
                dry_run=False,
                bookmark_folder="其他书签 / 知识库",
            )
            self.assertEqual(result["imported"], 0)
            self.assertEqual(result["failed"], 0)
            self.assertTrue((Path(tmp) / "知识库索引.md").exists())

    def test_dry_run_accepts_custom_bookmark_folder(self):
        fixture = Path(__file__).parent / "fixtures" / "account_bookmarks_custom_folder.json"
        with tempfile.TemporaryDirectory() as tmp:
            result = run_import(
                bookmark_file=fixture,
                output_root=Path(tmp),
                dry_run=True,
                bookmark_folder="Other Bookmarks / Reading List",
            )
            self.assertEqual(result["total"], 1)
            self.assertEqual(result["items"][0]["url"], "https://example.com/article")

    def test_default_candidates_find_localized_bookmark_folder(self):
        fixture = Path(__file__).parent / "fixtures" / "account_bookmarks_existing.json"
        with tempfile.TemporaryDirectory() as tmp:
            result = run_import(
                bookmark_file=fixture,
                output_root=Path(tmp),
                dry_run=True,
            )
            self.assertEqual(result["bookmark_folder"], "其他书签 / 知识库")
            self.assertEqual(result["total"], 5)

    def test_env_bookmark_folder_is_default_candidate(self):
        fixture = Path(__file__).parent / "fixtures" / "account_bookmarks_existing.json"
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            "os.environ", {"CHROME_BOOKMARKS_TO_OBSIDIAN_FOLDER": "其他书签 / 知识库"}
        ):
            result = run_import(
                bookmark_file=fixture,
                output_root=Path(tmp),
                dry_run=True,
            )
            self.assertEqual(result["bookmark_folder"], "其他书签 / 知识库")
            self.assertEqual(result["total"], 5)


if __name__ == "__main__":
    unittest.main()
