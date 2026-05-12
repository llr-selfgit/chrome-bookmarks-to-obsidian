import os
from pathlib import Path

DEFAULT_BOOKMARKS_PATHS = [
    Path.home() / "Library/Application Support/Google/Chrome/Default/AccountBookmarks",
    Path.home() / "Library/Application Support/Google/Chrome/Default/Bookmarks",
]

BOOKMARK_FOLDER_ENV = "CHROME_BOOKMARKS_TO_OBSIDIAN_FOLDER"
DEFAULT_BOOKMARK_FOLDER = "Other Bookmarks / Reading List"
DEFAULT_BOOKMARK_FOLDER_CANDIDATES = [
    DEFAULT_BOOKMARK_FOLDER,
    "其他书签 / 知识库",
]
DEFAULT_VAULT_ROOT = Path.home() / "Documents/Obsidian Vault"
DEFAULT_OUTPUT_DIR = DEFAULT_VAULT_ROOT / "80_web_knowledge_base"

BOUNDARY_TEXT = (
    "本知识库来自用户主动收藏的网页，只代表用户当前关注过的一部分资料，"
    "不代表某个领域的完整参考资料。Agent 可以优先用它理解用户上下文和已有来源，"
    "但回答开放性、时效性或需要完整性的任务时，必须结合外部检索或其他可靠来源。"
)


def bookmark_folder_candidates() -> list[str]:
    folders = []
    env_folder = os.environ.get(BOOKMARK_FOLDER_ENV, "").strip()
    if env_folder:
        folders.append(env_folder)
    folders.extend(DEFAULT_BOOKMARK_FOLDER_CANDIDATES)

    candidates = []
    seen = set()
    for folder in folders:
        if folder not in seen:
            candidates.append(folder)
            seen.add(folder)
    return candidates
