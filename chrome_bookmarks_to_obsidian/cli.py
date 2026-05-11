import argparse
import hashlib
import json
from pathlib import Path
from typing import Optional

from chrome_bookmarks_to_obsidian.bookmarks import extract_bookmarks_under_path, load_bookmark_file
from chrome_bookmarks_to_obsidian.config import DEFAULT_BOOKMARK_FOLDER, DEFAULT_BOOKMARKS_PATHS, DEFAULT_OUTPUT_DIR
from chrome_bookmarks_to_obsidian.fetcher import fetch_url
from chrome_bookmarks_to_obsidian.registry import ImportRegistry
from chrome_bookmarks_to_obsidian.summarize import classify_source, summarize_text
from chrome_bookmarks_to_obsidian.writer import ObsidianWriter


def _target_bookmark_path(bookmark_folder: Optional[str] = None) -> list:
    folder = bookmark_folder or DEFAULT_BOOKMARK_FOLDER
    return [part.strip() for part in folder.split("/") if part.strip()]


def _first_existing_bookmark_file() -> Path:
    for path in DEFAULT_BOOKMARKS_PATHS:
        if path.exists():
            return path
    searched = ", ".join(str(path) for path in DEFAULT_BOOKMARKS_PATHS)
    raise FileNotFoundError(f"No Chrome bookmark file found. Searched: {searched}")


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _source_note_for_registry(note_path: Path, output_root: Path) -> str:
    try:
        return str(note_path.relative_to(output_root.parent))
    except ValueError:
        return str(note_path)


def run_import(
    bookmark_file: Optional[Path] = None,
    output_root: Path = DEFAULT_OUTPUT_DIR,
    dry_run: bool = False,
    limit: int = 0,
    bookmark_folder: Optional[str] = None,
) -> dict:
    bookmark_file = bookmark_file or _first_existing_bookmark_file()
    data = load_bookmark_file(bookmark_file)
    bookmarks = extract_bookmarks_under_path(data, _target_bookmark_path(bookmark_folder))
    selected = bookmarks[:limit] if limit else bookmarks

    writer = ObsidianWriter(output_root)
    registry = ImportRegistry.load(output_root / "_registry.json")
    result = {
        "bookmark_file": str(bookmark_file),
        "output_root": str(output_root),
        "dry_run": dry_run,
        "bookmark_folder": bookmark_folder or DEFAULT_BOOKMARK_FOLDER,
        "total": len(bookmarks),
        "selected": len(selected),
        "imported": 0,
        "failed": 0,
        "skipped": 0,
        "items": [],
    }

    if not dry_run:
        writer.ensure_base()

    for bookmark in selected:
        if registry.has_imported(bookmark.url):
            result["skipped"] += 1
            result["items"].append({"title": bookmark.title, "url": bookmark.url, "status": "skipped"})
            continue

        if dry_run:
            result["items"].append(
                {
                    "title": bookmark.title,
                    "url": bookmark.url,
                    "bookmark_path": " / ".join(bookmark.bookmark_path),
                    "status": "would_process",
                }
            )
            continue

        fetch = fetch_url(bookmark.url)
        if fetch.status != "ok":
            reason = f"{fetch.status}:{fetch.failure_reason}"
            writer.record_failure(bookmark, reason)
            registry.mark_failed(bookmark.url, reason)
            result["failed"] += 1
            result["items"].append({"title": bookmark.title, "url": bookmark.url, "status": fetch.status, "reason": reason})
            continue

        category, confidence = classify_source(f"{bookmark.title}\n{fetch.text}")
        if confidence < 0.5:
            category = "未分类"
        summary = summarize_text(fetch.title or bookmark.title, fetch.text)
        content_hash = _hash_text(fetch.text or bookmark.url)
        note_path = writer.write_imported_source(bookmark, fetch, category, summary, content_hash)
        registry.mark_imported(
            url=bookmark.url,
            source_note=_source_note_for_registry(note_path, output_root),
            category=category,
            content_hash=content_hash,
        )
        result["imported"] += 1
        result["items"].append(
            {
                "title": bookmark.title,
                "url": bookmark.url,
                "status": "imported",
                "category": category,
                "source_note": str(note_path),
                "media_type": fetch.media_type,
                "transcript_status": fetch.transcript_status,
            }
        )

    if not dry_run:
        registry.save()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a Chrome bookmark folder into an Obsidian web knowledge base.")
    parser.add_argument("--bookmark-file", type=Path, default=None)
    parser.add_argument("--bookmark-folder", default=None, help='Folder path such as "Other Bookmarks / Reading List".')
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    result = run_import(args.bookmark_file, args.output_root, args.dry_run, args.limit, args.bookmark_folder)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
