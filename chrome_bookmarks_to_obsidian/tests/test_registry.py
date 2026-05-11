import tempfile
import unittest
from pathlib import Path

from chrome_bookmarks_to_obsidian.registry import ImportRegistry, normalize_url


class RegistryTests(unittest.TestCase):
    def test_normalize_url_removes_fragment_and_default_slash(self):
        self.assertEqual(normalize_url("https://Example.com/path/#frag"), "https://example.com/path")
        self.assertEqual(normalize_url("https://example.com/"), "https://example.com")

    def test_registry_save_load_and_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "_registry.json"
            registry = ImportRegistry.load(path)
            self.assertFalse(registry.has_imported("https://example.com/a#x"))
            registry.mark_imported(
                url="https://example.com/a#x",
                source_note="80_web_knowledge_base/Test/sources/a.md",
                category="Test",
                content_hash="abc",
            )
            registry.save()
            loaded = ImportRegistry.load(path)
            self.assertTrue(loaded.has_imported("https://example.com/a"))
            self.assertEqual(loaded.records["https://example.com/a"]["category"], "Test")


if __name__ == "__main__":
    unittest.main()

