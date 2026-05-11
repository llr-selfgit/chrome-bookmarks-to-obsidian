import unittest

from chrome_bookmarks_to_obsidian.summarize import classify_source, summarize_text


class SummarizeTests(unittest.TestCase):
    def test_classifies_agent_content(self):
        category, confidence = classify_source("Agent memory RAG tool calling context engineering")
        self.assertEqual(category, "AI Agent")
        self.assertGreaterEqual(confidence, 0.5)

    def test_classifies_uncertain_content_as_uncategorized(self):
        category, confidence = classify_source("short vague text")
        self.assertEqual(category, "未分类")
        self.assertLess(confidence, 0.5)

    def test_summary_has_required_sections(self):
        text = "Agent memory helps systems retrieve prior context. It should not be treated as complete truth. Sources need timestamps."
        summary = summarize_text("Memory article", text)
        self.assertIn("one_line", summary)
        self.assertIn("key_points", summary)
        self.assertIn("limitations", summary)
        self.assertTrue(summary["key_points"])

    def test_summary_skips_common_navigation_boilerplate(self):
        text = (
            "Skip to content Navigation Menu Toggle navigation Sign in Appearance settings Platform AI CODE CREATION. "
            "Search code, repositories, users, issues, pull requests. "
            "DeepSeek-Reasonix is a DeepSeek-native AI coding agent engineered around prefix-cache stability."
        )
        summary = summarize_text("DeepSeek-Reasonix", text)
        self.assertIn("DeepSeek-Reasonix", summary["one_line"])
        self.assertNotIn("Skip to content", summary["one_line"])

    def test_summary_deduplicates_near_duplicate_points(self):
        text = (
            "DeepSeek-native AI coding agent for your terminal. "
            "- esengine/DeepSeek-Reasonix DeepSeek-native AI coding agent for your terminal. "
            "Engineered around prefix-cache stability."
        )
        summary = summarize_text("DeepSeek-Reasonix", text)
        joined = "\n".join(summary["key_points"])
        self.assertEqual(joined.count("DeepSeek-native AI coding agent for your terminal"), 1)

    def test_summary_skips_github_ui_boilerplate_points(self):
        text = (
            "DeepSeek-native AI coding agent for your terminal. "
            "Search Clear Search syntax tips Provide feedback We read every piece of feedback. "
            "Include my email address so I can be contacted Cancel Submit feedback Saved searches. "
            "Reload to refresh your session. You signed out in another tab or window. "
            "Engineered around prefix-cache stability."
        )
        summary = summarize_text("DeepSeek-Reasonix", text)
        joined = "\n".join(summary["key_points"])
        self.assertNotIn("Provide feedback", joined)
        self.assertNotIn("Include my email", joined)
        self.assertNotIn("Reload to refresh", joined)
        self.assertNotIn("signed out in another tab", joined)


if __name__ == "__main__":
    unittest.main()
