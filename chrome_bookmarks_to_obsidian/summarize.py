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
)


def _sentences(text: str) -> List[str]:
    chunks = re.split(r"(?<=[.!?。！？])\s+", " ".join(text.split()))
    candidates = [chunk.strip() for chunk in chunks if len(chunk.strip()) > 20]
    filtered = []
    seen_normalized = []
    for sentence in candidates:
        lower = sentence.lower()
        marker_count = sum(1 for marker in BOILERPLATE_MARKERS if marker in lower)
        if lower.startswith("skip to content") or lower.startswith("search code, repositories") or marker_count >= 1:
            continue
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
    return filtered or candidates


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


def summarize_text(title: str, text: str) -> Dict[str, object]:
    sentences = _sentences(text)
    key_points = sentences[:5] if sentences else [text[:300].strip() or title]
    one_line = key_points[0][:180]
    limitations = [
        "该来源来自用户收藏，覆盖范围是局部的，不代表该主题的完整资料。",
        "如用于时效性判断，应重新联网核验。",
    ]
    return {
        "one_line": one_line,
        "key_points": key_points,
        "use_cases": ["作为用户收藏来源的背景资料", "用于后续研究时的起点和线索"],
        "limitations": limitations,
    }
