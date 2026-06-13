from __future__ import annotations

import time
from pathlib import PurePosixPath
from typing import Callable, Optional
from urllib.parse import urlparse

import requests

from core.config import (
    BB_API,
    BB_ULTRA,
    MAX_RETRIES,
    REQUEST_DELAY_MIN,
    REQUEST_TIMEOUT,
    SHAREPOINT_DOMAINS,
)
from core.models import (
    CONTENT_HANDLER_MAP,
    EXTENSION_MAP,
    Course,
    CourseStatus,
    Item,
    ItemType,
)
from core.state import save_manifest, update_course_status


def fetch_user_name(session: requests.Session) -> str:
    """Giriş yapan kullanıcının adını Blackboard'dan çeker."""
    try:
        resp = session.get(
            f"{BB_API}/users/me?fields=name.given,name.family",
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            name = resp.json().get("name", {})
            return name.get("given", "").strip() or name.get("family", "").strip()
    except Exception:
        pass
    return ""


class BlackboardCrawler:
    """
    Blackboard REST API üzerinden ders ve içerik keşfi.

    Kullanım:
        crawler = BlackboardCrawler(session, on_status=cb, on_progress=cb)
        courses = crawler.discover_courses()
        for course in courses.values():
            crawler.crawl_course(course, courses)
    """

    def __init__(
        self,
        session: requests.Session,
        on_status:   Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[str, int, int], None]] = None,
    ) -> None:
        self._session    = session
        self._on_status  = on_status
        self._on_progress = on_progress  # (course_name, current, total)

    # ── Aşama 1: Ders Listesi ─────────────────────────────────

    def discover_courses(self) -> dict[str, Course]:
        """Kayıtlı tüm dersleri çeker. Sonuçları manifest'e yazar."""
        self._status("Dersler alınıyor...")
        url = (
            f"{BB_API}/users/me/courses"
            "?limit=100"
            "&fields=courseId,id,course.name,course.courseId,"
            "course.availability,course.ultraStatus,course.contacts"
        )
        courses: dict[str, Course] = {}

        while url:
            data = self._get(url)
            if data is None:
                break

            for entry in data.get("results", []):
                course_data = entry.get("course", {})
                avail = course_data.get("availability", {}).get("available", "No")
                if avail != "Yes":
                    continue

                cid  = course_data.get("courseId") or entry.get("courseId", "")
                name = course_data.get("name", "Bilinmeyen Ders")
                url_path = f"{BB_ULTRA}/courses/{entry.get('id', '')}/outline"

                courses[cid] = Course(
                    id=entry.get("courseId") or entry.get("id", cid),
                    name=name,
                    url=url_path,
                    course_code=course_data.get("courseId", ""),
                )

            url = self._next_page(data)

        self._status(f"{len(courses)} ders bulundu")
        save_manifest(courses)
        return courses

    # ── Aşama 2: İçerik Ağacı ────────────────────────────────

    def crawl_course(self, course: Course, all_courses: dict[str, Course]) -> None:
        """Bir kursun tüm içerik ağacını keşfeder, manifest'i günceller."""
        self._status(f"Taranıyor: {course.name}")
        manifest_key = course.course_code or course.id
        update_course_status(manifest_key, CourseStatus.CRAWLING)

        try:
            items = self._crawl_contents(course.id, parent_hint="")
            course.items = {item.id: item for item in items}
            course.instructors = self._get_instructors(course.course_code or course.id)
            course.status = CourseStatus.CRAWLED
            all_courses[manifest_key] = course
            save_manifest(all_courses)
            self._status(f"{course.name}: {len(items)} içerik bulundu")
        except Exception as exc:
            course.status = CourseStatus.CRAWL_FAILED
            all_courses[manifest_key] = course
            save_manifest(all_courses)
            self._status(f"{course.name}: tarama hatası — {exc}")

    # ── İç: İçerik Recursive Tarama ──────────────────────────

    def _crawl_contents(
        self, course_id: str, parent_content_id: str = "", parent_hint: str = ""
    ) -> list[Item]:
        """İçerik listesini recursive olarak çeker."""
        if parent_content_id:
            url = f"{BB_API}/courses/{course_id}/contents/{parent_content_id}/children?limit=200"
        else:
            url = f"{BB_API}/courses/{course_id}/contents?limit=200"

        items: list[Item] = []

        while url:
            data = self._get(url)
            if data is None:
                break

            for entry in data.get("results", []):
                avail = entry.get("availability", {}).get("available", "No")
                if avail not in ("Yes", "PartiallyVisible"):
                    continue

                handler_id = entry.get("contentHandler", {}).get("id", "")
                title      = entry.get("title", "isimsiz")
                content_id = entry.get("id", "")
                hint       = f"{parent_hint}/{title}".lstrip("/")

                # Klasör → recursive
                if handler_id == "resource/x-bb-folder" or entry.get("hasChildren"):
                    children = self._crawl_contents(course_id, content_id, hint)
                    items.extend(children)
                    continue

                # Harici link
                if handler_id == "resource/x-bb-externallink":
                    ext_url = entry.get("contentHandler", {}).get("url", "")
                    item_type = self._classify_url(ext_url)
                    if ext_url:
                        items.append(Item(
                            id=content_id,
                            name=title,
                            type=item_type,
                            url=ext_url,
                            path_hint=hint,
                        ))
                    continue

                # Dosya attachment'ları
                attachments = self._get_attachments(course_id, content_id)
                items.extend(
                    Item(
                        id=att["id"],
                        name=att["name"],
                        type=att["type"],
                        url=att["url"],
                        size_bytes=att.get("size_bytes"),
                        uploaded_at=att.get("uploaded_at"),
                        path_hint=hint,
                    )
                    for att in attachments
                )

            url = self._next_page(data)

        return items

    _INSTRUCTOR_ROLES = {"Instructor", "TeachingAssistant", "CourseBuilder", "P"}

    def _get_instructors(self, course_id: str) -> list[str]:
        """Hoca adlarını çeker. External ID ise courseId: prefix kullanır, pagination yapar."""
        try:
            prefix = "" if course_id.startswith("_") else "courseId:"
            url: Optional[str] = (
                f"{BB_API}/courses/{prefix}{course_id}/users"
                "?limit=100&expand=user"
            )
            names: list[str] = []
            while url:
                resp = self._session.get(url, timeout=8)
                if resp.status_code != 200:
                    return []
                data = resp.json()
                for entry in data.get("results", []):
                    if entry.get("courseRoleId") not in self._INSTRUCTOR_ROLES:
                        continue
                    user = entry.get("user", {})
                    nm   = user.get("name", {})
                    full = f"{nm.get('given','').strip()} {nm.get('family','').strip()}".strip()
                    if full:
                        names.append(full)
                if names:
                    return names  # Hocaları bulduk, aramaya devam etme
                url = self._next_page(data)
            return names
        except Exception:
            return []

    def _get_attachments(self, course_id: str, content_id: str) -> list[dict]:
        """Bir içeriğin dosya attachment'larını çeker."""
        url  = f"{BB_API}/courses/{course_id}/contents/{content_id}/attachments"
        data = self._get(url)
        if not data:
            return []

        result = []
        for att in data.get("results", []):
            filename = att.get("fileName", "dosya")
            ext      = PurePosixPath(filename).suffix.lower()
            att_id   = att.get("id", "")
            dl_url   = (
                f"{BB_API}/courses/{course_id}/contents/{content_id}"
                f"/attachments/{att_id}/download"
            )
            result.append({
                "id":          att_id,
                "name":        filename,
                "type":        EXTENSION_MAP.get(ext, ItemType.OTHER),
                "url":         dl_url,
                "size_bytes":  att.get("size"),
                "uploaded_at": att.get("uploadDate"),
            })
        return result

    # ── İç: HTTP ─────────────────────────────────────────────

    def _get(self, url: str) -> Optional[dict]:
        """Retry destekli GET isteği. Hata durumunda None döner."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self._session.get(url, timeout=REQUEST_TIMEOUT)
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code == 401:
                    self._status("Oturum süresi dolmuş — yeniden giriş gerekiyor")
                    return None
                if resp.status_code == 403:
                    return None  # yetkisiz endpoint, sessiz geç
                if resp.status_code == 404:
                    return None
            except requests.RequestException as exc:
                if attempt == MAX_RETRIES:
                    self._status(f"İstek hatası ({url}): {exc}")
                    return None
            time.sleep(REQUEST_DELAY_MIN * attempt)
        return None

    @staticmethod
    def _next_page(data: dict) -> Optional[str]:
        """Paging.nextPage varsa tam URL döner."""
        next_path = data.get("paging", {}).get("nextPage")
        if not next_path:
            return None
        parsed = urlparse(BB_API)
        return f"{parsed.scheme}://{parsed.netloc}{next_path}"

    # ── İç: Tip Tespiti ───────────────────────────────────────

    def _classify_url(self, url: str) -> ItemType:
        """URL'e göre ItemType belirler (SharePoint vs diğer)."""
        if not url:
            return ItemType.LINK
        domain = urlparse(url).netloc.lower()
        if any(sp in domain for sp in SHAREPOINT_DOMAINS):
            return ItemType.VIDEO_SHAREPOINT
        ext = PurePosixPath(urlparse(url).path).suffix.lower()
        return EXTENSION_MAP.get(ext, ItemType.LINK)

    def _status(self, message: str) -> None:
        if self._on_status:
            self._on_status(message)
