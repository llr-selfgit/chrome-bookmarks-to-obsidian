from dataclasses import dataclass
from html.parser import HTMLParser
import re
from typing import List
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


@dataclass
class FetchResult:
    url: str
    title: str
    text: str
    site: str
    canonical_url: str
    retrieval_method: str
    status: str
    failure_reason: str = ""
    media_type: str = "article"
    transcript_status: str = "not_applicable"


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._skip_stack: List[str] = []
        self._semantic_stack: List[str] = []
        self.parts: List[str] = []
        self.semantic_parts: List[str] = []
        self.title_parts: List[str] = []
        self.description_parts: List[str] = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_stack.append(tag)
        if _looks_like_content_container(tag, attrs):
            self._semantic_stack.append(tag)
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            attr_map = {str(key).lower(): value for key, value in attrs}
            name = str(attr_map.get("name") or attr_map.get("property") or "").lower()
            if name in {"description", "og:description", "twitter:description"} and attr_map.get("content"):
                self.description_parts.append(" ".join(str(attr_map["content"]).split()))

    def handle_endtag(self, tag):
        if self._skip_stack and self._skip_stack[-1] == tag:
            self._skip_stack.pop()
        if self._semantic_stack and self._semantic_stack[-1] == tag:
            self._semantic_stack.pop()
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._skip_stack:
            return
        clean = " ".join(data.split())
        if not clean:
            return
        if self._in_title:
            self.title_parts.append(clean)
        elif self._semantic_stack:
            self.semantic_parts.append(clean)
        else:
            self.parts.append(clean)


def _looks_like_content_container(tag, attrs) -> bool:
    if tag in {"article", "main"}:
        return True
    attr_map = {str(key).lower(): str(value or "").lower() for key, value in attrs}
    marker_text = " ".join([attr_map.get("id", ""), attr_map.get("class", "")])
    markers = (
        "markdown-body",
        "readme",
        "article",
        "post-content",
        "entry-content",
        "content_views",
        "blog-content",
        "main-content",
    )
    return any(marker in marker_text for marker in markers)


def extract_text_from_html(html: str) -> str:
    parser = TextExtractor()
    parser.feed(html)
    semantic_text = "\n".join(parser.semantic_parts)
    if len(re.sub(r"\s+", "", semantic_text)) >= 60:
        return semantic_text
    return "\n".join(parser.parts)


def extract_title_from_html(html: str) -> str:
    parser = TextExtractor()
    parser.feed(html)
    return " ".join(parser.title_parts).strip()


def extract_description_from_html(html: str) -> str:
    parser = TextExtractor()
    parser.feed(html)
    return " ".join(parser.description_parts).strip()


def detect_blocked_reason(text: str) -> str:
    lower = text.lower()
    if "captcha" in lower or "verify you are human" in lower:
        return "captcha"
    login_markers = (
        "sign in to continue",
        "log in to continue",
        "login to continue",
        "please sign in",
        "please log in",
        "authentication required",
        "you must be logged in",
    )
    if any(marker in lower for marker in login_markers):
        return "login_required"
    if "subscribe to read" in lower or "paywall" in lower or "subscribe now" in lower:
        return "paywall"
    if "access denied" in lower or "forbidden" in lower:
        return "blocked"
    return ""


def detect_media_type(url: str) -> str:
    host = urlsplit(url).netloc.lower()
    if any(domain in host for domain in ("youtube.com", "youtu.be", "bilibili.com", "vimeo.com")):
        return "video"
    return "article"


def infer_transcript_status(media_type: str, text: str) -> str:
    if media_type != "video":
        return "not_applicable"
    lower = text.lower()
    if "transcript" in lower or "字幕" in text or "转录" in text:
        return "available"
    return "missing"


def github_readme_url_candidates(url: str) -> List[str]:
    parts = [part for part in urlsplit(url).path.split("/") if part]
    if urlsplit(url).netloc.lower() != "github.com" or len(parts) < 2:
        return []
    owner, repo = parts[0], parts[1]
    if len(parts) > 2 and parts[2] in {"blob", "tree", "issues", "pull", "releases"}:
        return []
    base = f"https://raw.githubusercontent.com/{owner}/{repo}"
    return [
        f"{base}/refs/heads/main/README.md",
        f"{base}/refs/heads/main/README.zh-CN.md",
        f"{base}/refs/heads/master/README.md",
        f"{base}/refs/heads/master/README.zh-CN.md",
    ]


def _fetch_github_readme(url: str, timeout: int) -> FetchResult:
    site = urlsplit(url).netloc
    for readme_url in github_readme_url_candidates(url):
        try:
            request = Request(readme_url, headers={"User-Agent": "Mozilla/5.0 ChromeBookmarksToObsidian/0.1"})
            with urlopen(request, timeout=timeout) as response:
                raw = response.read(500_000)
            text = raw.decode("utf-8", errors="replace")
            if len(re.sub(r"\s+", "", text)) >= 200:
                return FetchResult(url, "", text, site, url, "github_readme_raw", "ok")
        except Exception:
            continue
    return FetchResult(url, "", "", site, url, "github_readme_raw", "needs_browser", "readme_not_found")


def fetch_url(url: str, timeout: int = 20) -> FetchResult:
    site = urlsplit(url).netloc
    media_type = detect_media_type(url)
    if site.lower() == "github.com":
        readme_result = _fetch_github_readme(url, timeout)
        if readme_result.status == "ok":
            return readme_result

    request = Request(url, headers={"User-Agent": "Mozilla/5.0 ChromeBookmarksToObsidian/0.1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(2_000_000)
            content_type = response.headers.get("content-type", "")
        transcript_status = "missing" if media_type == "video" else "not_applicable"
        if "text/html" not in content_type and "text/plain" not in content_type:
            return FetchResult(
                url,
                "",
                "",
                site,
                url,
                "direct_http",
                "failed",
                f"unsupported_content_type:{content_type}",
                media_type,
                transcript_status,
            )
        html = raw.decode("utf-8", errors="replace")
        text = extract_text_from_html(html)
        description = extract_description_from_html(html)
        if description and description not in text[:1000]:
            text = f"{description}\n{text}"
        title = extract_title_from_html(html) or site or url
        transcript_status = infer_transcript_status(media_type, text)
        blocked = detect_blocked_reason(text[:4000])
        if blocked:
            return FetchResult(url, title, text[:1000], site, url, "direct_http", "failed", blocked, media_type, transcript_status)
        if len(re.sub(r"\s+", "", text)) < 200:
            return FetchResult(url, title, text, site, url, "direct_http", "needs_browser", "empty_text", media_type, transcript_status)
        return FetchResult(url, title, text, site, url, "direct_http", "ok", "", media_type, transcript_status)
    except Exception as exc:
        transcript_status = "missing" if media_type == "video" else "not_applicable"
        return FetchResult(url, "", "", site, url, "direct_http", "needs_browser", f"{type(exc).__name__}: {exc}", media_type, transcript_status)
