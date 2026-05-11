import unittest

from chrome_bookmarks_to_obsidian.fetcher import (
    FetchResult,
    detect_blocked_reason,
    detect_media_type,
    extract_description_from_html,
    extract_text_from_html,
    infer_transcript_status,
)


class FetcherTests(unittest.TestCase):
    def test_extract_text_from_html_removes_script_and_style(self):
        html = "<html><head><title>T</title><style>x</style></head><body><h1>Hello</h1><script>x</script><p>World text.</p></body></html>"
        text = extract_text_from_html(html)
        self.assertIn("Hello", text)
        self.assertIn("World text.", text)
        self.assertNotIn("script", text.lower())

    def test_extracts_meta_description(self):
        html = '<html><head><meta property="og:description" content="DeepSeek-native AI coding agent."></head></html>'
        self.assertEqual(extract_description_from_html(html), "DeepSeek-native AI coding agent.")

    def test_detects_captcha_login_and_paywall(self):
        self.assertEqual(detect_blocked_reason("Please complete the CAPTCHA"), "captcha")
        self.assertEqual(detect_blocked_reason("Sign in to continue"), "login_required")
        self.assertEqual(detect_blocked_reason("Subscribe to read"), "paywall")

    def test_public_page_navigation_sign_in_is_not_login_wall(self):
        text = "Sign in Product Actions Code Issues Pull requests DeepSeek-native AI coding agent"
        self.assertEqual(detect_blocked_reason(text), "")

    def test_detects_video_sources_and_missing_transcript(self):
        self.assertEqual(detect_media_type("https://www.youtube.com/watch?v=AnyAbiXOf8g"), "video")
        self.assertEqual(infer_transcript_status("video", "Only title and channel metadata"), "missing")

    def test_fetch_result_can_request_browser_assisted(self):
        result = FetchResult(
            url="https://example.com",
            title="Example",
            text="",
            site="example.com",
            canonical_url="https://example.com",
            retrieval_method="direct_http",
            status="needs_browser",
            failure_reason="empty_text",
        )
        self.assertEqual(result.status, "needs_browser")
        self.assertEqual(result.failure_reason, "empty_text")


if __name__ == "__main__":
    unittest.main()
