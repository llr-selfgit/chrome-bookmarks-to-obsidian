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
            "one_line": f"视频标题指向“{clean_title}”；当前没有 transcript，只能据标题判断主题，不能当作已理解视频正文。",
            "key_points": [
                f"标题显示该视频大概率讨论 {clean_title} 这一主题。",
                "未获取到可靠 transcript，因此不能提炼视频里的论证、步骤、案例或具体结论。",
                "适合作为待补 transcript 或后续浏览器辅助整理的线索。",
            ],
            "use_cases": ["作为用户收藏来源的主题线索", "后续补 transcript 后再整理为正式内容"],
            "limitations": [
                "该条目只基于标题判断，不代表视频正文内容。",
                "不能引用视频中的具体观点，除非后续补充 transcript 或人工观看整理。",
            ],
        }
    sentences = _sentences(text)
    if not sentences:
        return {
            "summary_basis": "metadata",
            "one_line": f"未提取到可靠正文；当前只保留标题“{clean_title}”作为线索。",
            "key_points": [
                f"标题显示该来源可能与“{clean_title}”相关。",
                "自动抽取结果主要是导航、按钮、统计、登录提示或其他页面元素，未达到正文整理标准。",
                "需要浏览器辅助、transcript 或人工整理后，才能生成正文级摘要。",
            ],
            "use_cases": ["作为待复核来源线索", "后续补正文后再整理为正式内容"],
            "limitations": [
                "该条目没有可靠正文摘要，不能引用为来源观点。",
                "需要回到原网页或使用浏览器辅助流程重新获取正文。",
            ],
        }
    key_points = sentences[:5]
    one_line = key_points[0][:180]
    limitations = [
        "该来源来自用户收藏，覆盖范围是局部的，不代表该主题的完整资料。",
        "如用于时效性判断，应重新联网核验。",
    ]
    return {
        "summary_basis": "content",
        "one_line": one_line,
        "key_points": key_points,
        "use_cases": ["作为用户收藏来源的背景资料", "用于后续研究时的起点和线索"],
        "limitations": limitations,
    }
