import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlsplit, urlunsplit


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    scheme = (parts.scheme or "https").lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") if parts.path != "/" else ""
    return urlunsplit((scheme, netloc, path, parts.query, ""))


class ImportRegistry:
    def __init__(self, path: Path, records: Dict[str, Dict[str, Any]]):
        self.path = path
        self.records = records

    @classmethod
    def load(cls, path: Path) -> "ImportRegistry":
        if not path.exists():
            return cls(path, {})
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(path, data.get("records", {}))

    def has_imported(self, url: str) -> bool:
        record = self.records.get(normalize_url(url))
        return bool(record and record.get("status") == "imported")

    def mark_imported(self, url: str, source_note: str, category: str, content_hash: str) -> None:
        key = normalize_url(url)
        existing = self.records.get(key, {})
        first_imported_at = existing.get("first_imported_at") or now_iso()
        self.records[key] = {
            "status": "imported",
            "original_url": url,
            "normalized_url": key,
            "source_note": source_note,
            "category": category,
            "content_hash": content_hash,
            "first_imported_at": first_imported_at,
            "last_checked_at": now_iso(),
            "summary_version": 1,
        }

    def mark_failed(self, url: str, reason: str) -> None:
        key = normalize_url(url)
        self.records[key] = {
            "status": "failed",
            "original_url": url,
            "normalized_url": key,
            "failure_reason": reason,
            "last_checked_at": now_iso(),
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"records": dict(sorted(self.records.items()))}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

