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
        self.assertIn("candidate_excerpts", summary)
        self.assertIn("limitations", summary)
        self.assertEqual(summary["summary_basis"], "content")
        self.assertEqual(summary["curation_status"], "needs_agent")
        self.assertTrue(summary["candidate_excerpts"])

    def test_summary_skips_common_navigation_boilerplate(self):
        text = (
            "Skip to content Navigation Menu Toggle navigation Sign in Appearance settings Platform AI CODE CREATION. "
            "Search code, repositories, users, issues, pull requests. "
            "Example Agent is a terminal coding assistant engineered around stable context reuse."
        )
        summary = summarize_text("Example Agent", text)
        joined = "\n".join(summary["candidate_excerpts"])
        self.assertIn("Example Agent", joined)
        self.assertNotIn("Skip to content", joined)

    def test_summary_deduplicates_near_duplicate_points(self):
        text = (
            "Terminal coding assistant for local workflows. "
            "- example/agent-playbook Terminal coding assistant for local workflows. "
            "Engineered around stable context reuse."
        )
        summary = summarize_text("Example Agent", text)
        joined = "\n".join(summary["candidate_excerpts"])
        self.assertEqual(joined.count("Terminal coding assistant for local workflows"), 1)

    def test_summary_skips_github_ui_boilerplate_points(self):
        text = (
            "Terminal coding assistant for local workflows. "
            "Search Clear Search syntax tips Provide feedback We read every piece of feedback. "
            "Include my email address so I can be contacted Cancel Submit feedback Saved searches. "
            "Reload to refresh your session. You signed out in another tab or window. "
            "Engineered around stable context reuse."
        )
        summary = summarize_text("Example Agent", text)
        joined = "\n".join(summary["candidate_excerpts"])
        self.assertNotIn("Provide feedback", joined)
        self.assertNotIn("Include my email", joined)
        self.assertNotIn("Reload to refresh", joined)
        self.assertNotIn("signed out in another tab", joined)

    def test_summary_skips_csdn_metrics_and_article_directory(self):
        text = (
            "文章浏览阅读8.2k次，点赞30次，收藏31次。文章目录 1、前言 2、tmux 是什么。"
            "本文是一篇从零到实战的完整指南，目标是让你读完就能用 tmux 驾驭 Agent Teams。"
        )
        summary = summarize_text("tmux完全指南", text)
        joined = "\n".join(summary["candidate_excerpts"])
        self.assertNotIn("文章浏览阅读", joined)
        self.assertIn("tmux 驾驭 Agent Teams", joined)

    def test_video_without_transcript_uses_title_but_marks_limit(self):
        summary = summarize_text("Example Bookmark Workflow - YouTube", "", "video", "missing")
        self.assertEqual(summary["summary_basis"], "title")
        self.assertEqual(summary["curation_status"], "needs_agent")
        joined = "\n".join(summary["candidate_excerpts"] + summary["limitations"])
        self.assertIn("Example Bookmark Workflow", joined)
        self.assertIn("不能整理视频正文观点", joined)

    def test_boilerplate_only_becomes_metadata_summary(self):
        text = "Please update your browser Your browser isn’t supported anymore. About Copyright Contact us Terms Privacy Policy."
        summary = summarize_text("Example video page", text)
        self.assertEqual(summary["summary_basis"], "metadata")
        joined = "\n".join(summary["candidate_excerpts"] + summary["limitations"])
        self.assertIn("未达到正文整理标准", joined)
        self.assertNotIn("Please update your browser", joined)


if __name__ == "__main__":
    unittest.main()
