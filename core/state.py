from __future__ import annotations
import json
import random
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.config import DATA_DIR, DOWNLOADS_DIR, MANIFEST_FILE, PROGRESS_FILE
from core.models import Course, Item, DownloadStatus, CourseStatus


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)


# ── Manifest ─────────────────────────────────────────────────

def save_manifest(courses: dict[str, Course]) -> None:
    ensure_dirs()
    data = {
        "generated_at": datetime.now().isoformat(),
        "courses": {cid: c.to_dict() for cid, c in courses.items()},
    }
    MANIFEST_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def load_manifest() -> dict[str, Course]:
    if not MANIFEST_FILE.exists():
        return {}
    data = json.loads(MANIFEST_FILE.read_text())
    return {
        cid: Course.from_dict(cd)
        for cid, cd in data.get("courses", {}).items()
    }


def update_course_status(course_id: str, status: CourseStatus) -> None:
    courses = load_manifest()
    if course_id in courses:
        courses[course_id].status = status
        save_manifest(courses)


# ── Progress ─────────────────────────────────────────────────

def load_progress() -> dict[str, dict]:
    if not PROGRESS_FILE.exists():
        return {}
    data = json.loads(PROGRESS_FILE.read_text())
    return data.get("items", {})


def save_progress(items: dict[str, dict]) -> None:
    ensure_dirs()
    existing = {}
    if PROGRESS_FILE.exists():
        existing = json.loads(PROGRESS_FILE.read_text()).get("items", {})
    existing.update(items)

    downloaded = sum(1 for v in existing.values() if v.get("status") == "downloaded")
    failed     = sum(1 for v in existing.values() if v.get("status") == "failed")
    skipped    = sum(1 for v in existing.values() if v.get("status") == "skipped")

    data = {
        "last_run": datetime.now().isoformat(),
        "stats": {
            "total":      len(existing),
            "downloaded": downloaded,
            "failed":     failed,
            "skipped":    skipped,
        },
        "items": existing,
    }
    PROGRESS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def mark_downloaded(item_id: str, local_path: str) -> None:
    save_progress({
        item_id: {
            "status":        "downloaded",
            "local_path":    local_path,
            "downloaded_at": datetime.now().isoformat(),
        }
    })


def mark_failed(item_id: str, error: str, attempts: int) -> None:
    save_progress({
        item_id: {
            "status":   "failed",
            "error":    error,
            "attempts": attempts,
        }
    })


def mark_skipped(item_id: str, reason: str) -> None:
    save_progress({
        item_id: {
            "status": "skipped",
            "reason": reason,
        }
    })


def get_pending_items(courses: dict[str, Course]) -> list[Item]:
    progress = load_progress()
    pending = []
    for course in courses.values():
        for item in course.items.values():
            status = progress.get(item.id, {}).get("status")
            if status not in ("downloaded", "skipped"):
                pending.append(item)
    return pending


def get_stats() -> dict:
    if not PROGRESS_FILE.exists():
        return {"total": 0, "downloaded": 0, "failed": 0, "skipped": 0}
    data = json.loads(PROGRESS_FILE.read_text())
    return data.get("stats", {})


# ── Yardımcı ─────────────────────────────────────────────────

async def request_delay() -> None:
    """Sunucu yükünü azaltmak için rastgele bekleme."""
    from core.config import REQUEST_DELAY_MIN, REQUEST_DELAY_MAX
    delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
    await asyncio.sleep(delay)


def slugify_filename(name: str, ext: str = "") -> str:
    """Türkçe karakterleri ASCII'ye çevir, güvenli dosya adı üret."""
    from slugify import slugify
    slug = slugify(name, separator="_", lowercase=False)
    if not slug:
        slug = "dosya"
    return f"{slug}{ext}"


def unique_path(directory: Path, filename: str) -> Path:
    """Aynı isimde dosya varsa _2, _3 şeklinde benzersiz yol döndür."""
    target = directory / filename
    if not target.exists():
        return target
    stem = target.stem
    suffix = target.suffix
    counter = 2
    while True:
        candidate = directory / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
