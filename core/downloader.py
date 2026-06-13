from __future__ import annotations

import asyncio
import tempfile
import threading
from pathlib import Path, PurePosixPath
from typing import Callable, Optional

import aiofiles
import httpx
import requests

from core.config import (
    DOWNLOAD_CHUNK,
    LARGE_FILE_MB,
    MAX_RETRIES,
    MIN_FILE_SIZES,
    REQUEST_TIMEOUT,
)
from core.models import Course, DownloadFilter, Item, ItemType
from core.state import (
    load_progress,
    mark_downloaded,
    mark_failed,
    mark_skipped,
    request_delay,
    slugify_filename,
    unique_path,
)


class BlackboardDownloader:
    """
    Async dosya indirici — httpx stream + yt-dlp video desteği.

    Kullanım:
        dl = BlackboardDownloader(session, base_dir, dl_filter, on_status=cb)
        await dl.run(selected_courses)
    """

    def __init__(
        self,
        session:           requests.Session,
        base_dir:          Path,
        dl_filter:         DownloadFilter,
        on_status:         Optional[Callable[[str], None]] = None,
        on_progress:       Optional[Callable[[str, int, int], None]] = None,
        on_file_done:      Optional[Callable[[Item, bool], None]] = None,
        on_course_status:  Optional[Callable[[str, str], None]] = None,
    ) -> None:
        self._session           = session
        self._base_dir          = base_dir
        self._filter            = dl_filter
        self._on_status         = on_status
        self._on_progress       = on_progress
        self._on_file_done      = on_file_done
        self._on_course_status  = on_course_status
        self._semaphore:   Optional[asyncio.Semaphore] = None
        self._cancelled    = False
        self._paused       = threading.Event()
        self._paused.set()                          # başlangıçta çalışıyor
        self._link_locks:  dict[Path, asyncio.Lock] = {}

    # ── Public API ────────────────────────────────────────────

    async def run(self, courses: dict[str, Course]) -> None:
        """Verilen kurslar için tüm indirme akışını başlatır."""
        self._check_disk(courses)
        self._semaphore = asyncio.Semaphore(self._filter.concurrent)
        await asyncio.gather(
            *(self._download_course(c) for c in courses.values()),
            return_exceptions=True,
        )

    def _check_disk(self, courses: dict[str, Course]) -> None:
        from core.state import check_disk_space
        required = sum(
            item.size_bytes or 0
            for c in courses.values()
            for item in c.items.values()
            if self._filter.allows_item(item)
        )
        ok, free = check_disk_space(self._base_dir, required)
        if not ok:
            free_mb  = free / 1_048_576
            need_mb  = required / 1_048_576
            self._status(
                f"⚠ Disk alanı yetersiz — gerekli: {need_mb:.0f} MB, boş: {free_mb:.0f} MB"
            )

    def cancel(self) -> None:
        self._cancelled = True
        self._paused.set()      # duraklat varsa çıkışı engelleme

    def pause(self) -> None:
        self._paused.clear()

    def resume(self) -> None:
        self._paused.set()

    @staticmethod
    def _already_done(item: Item, progress: dict) -> bool:
        """Daha önce indirilmiş mi? Dosya/klasör hâlâ diskte varsa True."""
        status = progress.get(item.id, {}).get("status")
        if status == "skipped":
            return True
        if status == "downloaded":
            local = progress.get(item.id, {}).get("local_path", "")
            if not local:
                return False
            p = Path(local)
            if item.type in (ItemType.VIDEO_SHAREPOINT, ItemType.VIDEO_OTHER):
                # Videolar için local_path bir klasördür — içinde dosya varsa tamam
                return p.is_dir() and any(p.iterdir())
            return p.exists()
        return False

    # ── Kurs Seviyesi ─────────────────────────────────────────

    async def _download_course(self, course: Course) -> None:
        course_dir = self._resolve_course_dir(course)
        course_dir.mkdir(parents=True, exist_ok=True)

        progress = load_progress()
        raw_list = list(course.items.values())
        raw = len(raw_list)

        items = [
            it for it in raw_list
            if self._filter.allows_item(it)
            and not self._already_done(it, progress)
        ]

        total = len(items)
        done  = 0

        if raw == 0:
            self._status(f"⚠ {course.friendly_title or course.name}: içerik bulunamadı")
        elif total == 0:
            already = sum(
                1 for it in raw_list
                if progress.get(it.id, {}).get("status") in ("downloaded", "skipped")
            )
            if already == raw:
                self._status(f"— {course.friendly_title or course.name}: zaten indirilmiş ({raw} dosya)")
            else:
                self._status(f"⚠ {course.friendly_title or course.name}: hiçbir dosya indirme listesine girmedi")
        # Normal case: course header appears via on_course_status("active")

        if self._on_course_status:
            self._on_course_status(course.id, "active")

        for item in items:
            if self._cancelled:
                break
            # Duraklatma kontrolü — event set olmana kadar async poll
            while not self._paused.is_set():
                await asyncio.sleep(0.05)
            if self._cancelled:
                break
            async with self._semaphore:
                await self._handle_item(item, course_dir)
            done += 1
            if self._on_progress:
                self._on_progress(course.name, done, total)
            await request_delay()

        if self._on_course_status:
            self._on_course_status(course.id, "done")

    # ── Yönlendirme ───────────────────────────────────────────

    async def _handle_item(self, item: Item, course_dir: Path) -> None:
        if item.type == ItemType.LINK:
            await self._append_link(item.name, item.url, course_dir / "links.txt")
            mark_skipped(item.id, "link")
            return

        if item.type == ItemType.SCORM:
            await self._append_link(item.name, item.url, course_dir / "scorm_links.txt")
            mark_skipped(item.id, "scorm")
            return

        if item.type in (ItemType.VIDEO_SHAREPOINT, ItemType.VIDEO_OTHER):
            await self._handle_video(item, course_dir)
            return

        await self._download_file(item, course_dir)

    async def _handle_video(self, item: Item, course_dir: Path) -> None:
        mode = self._filter.video_mode
        if mode == "skip":
            mark_skipped(item.id, "video_skipped")
            return
        if mode == "link":
            await self._append_link(item.name, item.url, course_dir / "video_links.txt")
            mark_skipped(item.id, "video_link")
            return
        dest_dir = self._resolve_item_dir(course_dir, item.path_hint)
        dest_dir.mkdir(parents=True, exist_ok=True)
        await self._download_video_ytdlp(item, dest_dir)

    # ── Dosya İndirme ─────────────────────────────────────────

    async def _download_file(self, item: Item, course_dir: Path) -> None:
        dest_dir = self._resolve_item_dir(course_dir, item.path_hint)
        dest_dir.mkdir(parents=True, exist_ok=True)

        if item.size_bytes and item.size_bytes > LARGE_FILE_MB * 1_048_576:
            self._status(
                f"⚠ Büyük dosya: {item.name} ({item.size_bytes / 1_048_576:.0f} MB)"
            )

        ext      = PurePosixPath(item.name).suffix.lower()
        stem     = PurePosixPath(item.name).stem
        filename = slugify_filename(stem, ext)
        dest     = unique_path(dest_dir, filename)
        tmp      = dest_dir / f".{item.id}.tmp"

        cookies = dict(self._session.cookies)
        headers = dict(self._session.headers)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(
                    cookies=cookies,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT,
                    follow_redirects=True,
                ) as client:
                    await self._stream_to_file(client, item.url, tmp)

                valid, reason = self._validate(tmp, item.type)
                if not valid:
                    tmp.unlink(missing_ok=True)
                    if attempt == MAX_RETRIES:
                        mark_failed(item.id, f"doğrulama: {reason}", attempt)
                        self._status(f"✗ {item.name} — {reason}")
                        if self._on_file_done:
                            self._on_file_done(item, False)
                    continue

                tmp.rename(dest)
                mark_downloaded(item.id, str(dest))
                self._status(f"✓ {item.name}")
                if self._on_file_done:
                    self._on_file_done(item, True)
                return

            except httpx.HTTPStatusError as exc:
                tmp.unlink(missing_ok=True)
                code = exc.response.status_code
                if code in (401, 403):
                    mark_failed(item.id, "auth_error", attempt)
                    self._status("Oturum süresi dolmuş — yeniden giriş gerekiyor")
                    return
                if code == 404:
                    mark_skipped(item.id, "not_found")
                    return
                if attempt == MAX_RETRIES:
                    mark_failed(item.id, f"HTTP {code}", attempt)
                    if self._on_file_done:
                        self._on_file_done(item, False)

            except httpx.RequestError as exc:
                tmp.unlink(missing_ok=True)
                if attempt == MAX_RETRIES:
                    mark_failed(item.id, str(exc), attempt)
                    self._status(f"✗ {item.name}: {exc}")
                    if self._on_file_done:
                        self._on_file_done(item, False)

    @staticmethod
    async def _stream_to_file(
        client: httpx.AsyncClient, url: str, dest: Path
    ) -> None:
        async with client.stream("GET", url) as resp:
            resp.raise_for_status()
            async with aiofiles.open(dest, "wb") as f:
                async for chunk in resp.aiter_bytes(DOWNLOAD_CHUNK):
                    await f.write(chunk)

    # ── Video İndirme (yt-dlp) ────────────────────────────────

    async def _download_video_ytdlp(self, item: Item, dest_dir: Path) -> None:
        quality     = self._filter.video_quality
        fmt         = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best"
        cookie_file = await self._write_cookie_file()

        try:
            loop    = asyncio.get_running_loop()
            success = await loop.run_in_executor(
                None,
                self._ytdlp_sync,
                item.url,
                dest_dir,
                fmt,
                cookie_file,
            )
            if success:
                mark_downloaded(item.id, str(dest_dir))
                self._status(f"✓ video: {item.name}")
                if self._on_file_done:
                    self._on_file_done(item, True)
            else:
                mark_failed(item.id, "yt-dlp hatası", 1)
                if self._on_file_done:
                    self._on_file_done(item, False)
        finally:
            Path(cookie_file).unlink(missing_ok=True)

    def _ytdlp_sync(
        self, url: str, dest_dir: Path, fmt: str, cookie_file: str
    ) -> bool:
        try:
            import yt_dlp
            opts = {
                "outtmpl":     str(dest_dir / "%(title)s.%(ext)s"),
                "format":      fmt,
                "cookiefile":  cookie_file,
                "quiet":       True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            return True
        except Exception as exc:
            self._status(f"yt-dlp: {exc}")
            return False

    async def _write_cookie_file(self) -> str:
        """Session cookie'lerini geçici Netscape cookies dosyasına yazar."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, prefix="bb_ck_"
        ) as f:
            f.write("# Netscape HTTP Cookie File\n")
            for c in self._session.cookies:
                secure = "TRUE" if c.secure else "FALSE"
                expiry = str(int(c.expires)) if c.expires else "0"
                f.write(
                    f"{c.domain}\tTRUE\t{c.path}\t{secure}\t{expiry}\t{c.name}\t{c.value}\n"
                )
            return f.name

    # ── Link / Metin Kaydetme ─────────────────────────────────

    async def _append_link(self, name: str, url: str, dest: Path) -> None:
        if dest not in self._link_locks:
            self._link_locks[dest] = asyncio.Lock()
        async with self._link_locks[dest]:
            async with aiofiles.open(dest, "a", encoding="utf-8") as f:
                await f.write(f"{name}\n{url}\n\n")

    # ── Doğrulama ─────────────────────────────────────────────

    @staticmethod
    def _validate(path: Path, item_type: ItemType) -> tuple[bool, str]:
        if not path.exists():
            return False, "dosya yok"

        size = path.stat().st_size
        if size == 0:
            return False, "boş dosya"

        with path.open("rb") as f:
            header = f.read(512)
        peak = header.lstrip()
        if peak[:9].lower() == b"<!doctype" or peak[:5].lower() == b"<html":
            return False, "HTML hata sayfası"

        type_key_map: dict[ItemType, str] = {
            ItemType.PDF:              "pdf",
            ItemType.PPTX:             "pptx",
            ItemType.DOCX:             "docx",
            ItemType.XLSX:             "xlsx",
            ItemType.IMAGE:            "image",
            ItemType.VIDEO_SHAREPOINT: "video",
            ItemType.VIDEO_OTHER:      "video",
            ItemType.ARCHIVE:          "zip",
        }
        key      = type_key_map.get(item_type, "other")
        min_size = MIN_FILE_SIZES.get(key, MIN_FILE_SIZES["other"])
        if size < min_size:
            return False, f"çok küçük ({size}b, min {min_size}b)"

        return True, ""

    # ── Yol Yardımcıları ──────────────────────────────────────

    def _resolve_course_dir(self, course: Course) -> Path:
        code  = slugify_filename(course.friendly_code)  if course.friendly_code  else ""
        title = slugify_filename(course.friendly_title) if course.friendly_title else ""
        if code and title:
            folder = f"{code}_{title}"
        elif code:
            folder = code
        elif title:
            folder = title
        else:
            folder = slugify_filename(course.name) or course.id
        return self._base_dir / folder

    @staticmethod
    def _resolve_item_dir(course_dir: Path, path_hint: str) -> Path:
        if not path_hint:
            return course_dir
        parts = [slugify_filename(p) for p in path_hint.split("/") if p.strip()]
        return course_dir.joinpath(*parts) if parts else course_dir

    # ── Durum ─────────────────────────────────────────────────

    def _status(self, message: str) -> None:
        if self._on_status:
            self._on_status(message)
