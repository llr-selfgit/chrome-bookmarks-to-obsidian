import re
from typing import Dict, List, Tuple


CATEGORY_KEYWORDS = {
    "AI Agent": ["agent", "memory", "rag", "tool", "context", "mcp", "codex", "claude"],
    "Obsidian": ["obsidian", "vault", "markdown", "note", "pkm"],
    "产品设计": ["product", "ux", "design", "onboarding", "dashboard"],
    "工程实践": ["python", "github", "api", "testing", "architecture", "cli"],
}

BOILERPLATE_MARKERS = (
    "skip to content",
    "navigation menu",
    "toggle navigation",
    "appearance settings",
    "search code, repositories",
    "search clear search syntax tips",
    "provide feedback",
    "include my email address",
    "submit feedback",
    "saved searches",
    "reload to refresh your session",
    "signed out in another tab",
    "switched accounts on another tab",
    "dismiss alert",
    "{{ message }}",
    "you must be signed in",
    "last commit message",
    "repository files navigation",
    "additional navigation options",
    "文章浏览阅读",
    "文章标签",
    "文章目录",
    "版权声明",
    "最新推荐文章",
    "作者介绍",
    "个人主页",
    "一键三连",
    "please update your browser",
    "your browser isn",
    "about copyright contact us",
)


def _clean_title(title: str) -> str:
    clean = re.sub(r"^\(\d+\)\s*", "", title or "").strip()
    clean = re.sub(r"\s*[-|]\s*YouTube\s*$", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s*[-|]\s*GitHub\s*$", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s*[-|]\s*CSDN博客\s*$", "", clean)
    return clean or title or "Untitled"


def _is_boilerplate(chunk: str) -> bool:
    lower = chunk.lower()
    if any(marker in lower for marker in BOILERPLATE_MARKERS):
        return True
    ui_terms = ("fork", "star", "code", "issues", "pull requests", "actions", "projects", "insights")
    if sum(1 for term in ui_terms if term in lower) >= 5:
        return True
    if len(chunk) > 260 and not re.search(r"[。！？.!?]", chunk):
        return True
    return False


def _sentences(text: str) -> List[str]:
    normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    chunks = []
    for line in normalized.splitlines():
        split_line = re.sub(r"(文章浏览阅读[^。]*。|文章目录[^。]*。|文章标签[^。]*。)", r"\1\n", line)
        chunks.extend(re.split(r"(?<=[.!?。！？])\s*|\n+", split_line))
    candidates = [chunk.strip() for chunk in chunks if len(chunk.strip()) > 20]
    filtered = []
    seen_normalized = []
    for sentence in candidates:
        if _is_boilerplate(sentence):
            continue
        lower = sentence.lower()
        normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", lower)
        if any(
            len(normalized) > 24
            and len(seen) > 24
            and (normalized in seen or seen in normalized)
            for seen in seen_normalized
        ):
            continue
        seen_normalized.append(normalized)
        filtered.append(sentence)
    return filtered


def classify_source(text: str) -> Tuple[str, float]:
    lower = text.lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        scores[category] = sum(1 for keyword in keywords if keyword.lower() in lower)
    category, score = max(scores.items(), key=lambda item: item[1])
    if score == 0:
        return "未分类", 0.0
    confidence = min(1.0, score / 4.0)
    return category, confidence


def summarize_text(
    title: str,
    text: str,
    media_type: str = "article",
    transcript_status: str = "not_applicable",
) -> Dict[str, object]:
    clean_title = _clean_title(title)
    if media_type == "video" and transcript_status != "available":
        return {
            "summary_basis": "title",
            "curation_status": "needs_agent",
            "one_line": f"待 Agent 整理：{clean_title}",
            "candidate_excerpts": [
                f"标题：{clean_title}",
                "未获取到可靠 transcript；这只能作为标题级线索。",
            ],
            "limitations": [
                "当前没有可靠 transcript，不能整理视频正文观点。",
                "需要补充 transcript 或人工观看后，再由 Agent 生成摘要、关键观点、用途和局限。",
            ],
        }
    sentences = _sentences(text)
    if not sentences:
        return {
            "summary_basis": "metadata",
            "curation_status": "needs_agent",
            "one_line": f"待 Agent 整理：{clean_title}",
            "candidate_excerpts": [
                f"标题：{clean_title}",
                "自动抽取结果主要是导航、按钮、统计、登录提示或其他页面元素，未达到正文整理标准。",
            ],
            "limitations": [
                "当前没有可靠正文，不能生成来源观点。",
                "需要回到原网页或使用浏览器辅助流程重新获取正文，再由 Agent 整理。",
            ],
        }
    return {
        "summary_basis": "content",
        "curation_status": "needs_agent",
        "one_line": f"待 Agent 整理：{clean_title}",
        "candidate_excerpts": sentences[:8],
        "limitations": [
            "脚本只负责抽取和去噪，不负责最终语义整理。",
            "需要 Agent 阅读候选正文和原链接后，再生成摘要、关键观点、用途和局限。",
        ],
    }
