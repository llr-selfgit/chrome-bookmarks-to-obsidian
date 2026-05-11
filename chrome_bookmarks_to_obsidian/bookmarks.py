from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class Bookmark:
    title: str
    url: str
    bookmark_path: List[str]
    date_added: str = ""
    chrome_id: str = ""


def load_bookmark_file(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid Chrome bookmark JSON at {path}: {exc}") from exc


def _folder_children(node: Dict[str, Any]) -> List[Dict[str, Any]]:
    return list(node.get("children") or [])


def _find_root_folder(data: Dict[str, Any], name: str) -> Optional[Dict[str, Any]]:
    for node in (data.get("roots") or {}).values():
        if node.get("type") == "folder" and node.get("name") == name:
            return node
    return None


def _find_child_folder(parent: Dict[str, Any], name: str) -> Optional[Dict[str, Any]]:
    for child in _folder_children(parent):
        if child.get("type") == "folder" and child.get("name") == name:
            return child
    return None


def _walk_urls(node: Dict[str, Any], path: List[str]) -> Iterable[Bookmark]:
    for child in _folder_children(node):
        child_type = child.get("type")
        if child_type == "url":
            yield Bookmark(
                title=child.get("name") or child.get("url") or "Untitled",
                url=child.get("url") or "",
                bookmark_path=path,
                date_added=child.get("date_added") or "",
                chrome_id=child.get("id") or "",
            )
        elif child_type == "folder":
            yield from _walk_urls(child, path + [child.get("name") or "未命名"])


def extract_bookmarks_under_path(data: Dict[str, Any], folder_path: List[str]) -> List[Bookmark]:
    if not folder_path:
        raise ValueError("Bookmark folder path must not be empty")
    current = _find_root_folder(data, folder_path[0])
    if current is None:
        raise ValueError(f"Bookmark folder not found: {' / '.join(folder_path)}")
    for part in folder_path[1:]:
        current = _find_child_folder(current, part)
        if current is None:
            raise ValueError(f"Bookmark folder not found: {' / '.join(folder_path)}")
    return [bookmark for bookmark in _walk_urls(current, folder_path) if bookmark.url]

