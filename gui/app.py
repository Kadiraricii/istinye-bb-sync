from __future__ import annotations

import asyncio
import queue
import threading
from pathlib import Path
from typing import Optional

import customtkinter as ctk
import requests

from core.config import WINDOW_HEIGHT, WINDOW_WIDTH
from core.crawler import BlackboardCrawler, fetch_user_name
from core.state import save_remembered_user, save_cookies, load_manifest
from core.downloader import BlackboardDownloader
from core.models import Course, DownloadFilter, Item
from gui.screen_courses import CoursesScreen
from gui.screen_filter import FilterScreen
from gui.screen_login import LoginScreen
from gui.screen_progress import ProgressScreen
from gui.theme import BG_BASE, CTK_APPEARANCE, CTK_COLOR_THEME


class App:
    """
    Ana uygulama — ekran geçişlerini ve worker thread'i yönetir.

    Mimari:
      • GUI thread: Tkinter main loop
      • Worker thread: asyncio event loop (crawler + downloader)
      • gui_queue: thread-safe mesajlaşma (worker → GUI)
    """

    def __init__(self) -> None:
        ctk.set_appearance_mode(CTK_APPEARANCE)
        ctk.set_default_color_theme(CTK_COLOR_THEME)

        self._root = ctk.CTk()
        self._root.title("Blackboard Sync")
        self._root.resizable(False, False)
        self._root.configure(fg_color=BG_BASE)
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._root.bind("<Escape>", self._on_escape)

        # Tarayıcı açılınca arka plana gitmemesi için her zaman üstte
        self._root.attributes("-topmost", True)
        self._root.update_idletasks()
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        x  = sw - WINDOW_WIDTH - 24
        y  = max(0, (sh - WINDOW_HEIGHT) // 4)
        self._root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

        self._session:    Optional[requests.Session] = None
        self._courses:    dict[str, Course] = {}
        self._selected:   dict[str, Course] = {}
        self._student_name: str = ""
        self._dest_dir: Path = Path.home() / "Downloads" / "Blackboard"
        self._dl_filter: Optional[DownloadFilter] = None
        self._downloader: Optional[BlackboardDownloader] = None
        self._worker_loop: Optional[asyncio.AbstractEventLoop] = None
        self._student_no: str = ""

        self._gui_queue: queue.Queue = queue.Queue()

        self._current_screen: Optional[ctk.CTkFrame] = None
        self._show_login()
        self._root.after(50, self._poll_queue)

    def run(self) -> None:
        self._root.mainloop()

    # ── Ekran Geçişleri ───────────────────────────────────────

    def _show_login(self) -> None:
        self._swap_screen(
            LoginScreen(
                self._root,
                on_login_success=self._on_login_success,
                on_quick_resume=self._on_quick_resume,
            )
        )

    def _show_courses(self) -> None:
        login = self._current_screen
        if hasattr(login, "show_syncing"):
            login.show_syncing()
        self._run_async(self._async_discover_courses())

    def _show_filter(self) -> None:
        screen = FilterScreen(
            self._root,
            on_start=self._on_filter_start,
            on_back=self._show_courses_cached,
            dest_dir=self._dest_dir,
        )
        screen.set_courses(self._selected)
        self._swap_screen(screen)

    def _show_courses_cached(self) -> None:
        """Kurs ekranına geri döner — yeniden tarama yapmaz."""
        courses_screen = CoursesScreen(
            self._root,
            on_continue=self._on_courses_continue,
            on_back=self._show_login,
        )
        self._swap_screen(courses_screen)
        courses_screen.set_student_name(self._student_name)
        courses_screen.load_courses(self._courses)
        courses_screen.set_loading(False)

    def _show_progress(self) -> None:
        screen = ProgressScreen(
            self._root,
            on_pause=lambda: self._downloader and self._downloader.pause(),
            on_resume=lambda: self._downloader and self._downloader.resume(),
            on_cancel=self._cancel_download,
        )
        screen.set_courses(self._selected)
        self._swap_screen(screen)
        self._run_async(self._async_download(screen))

    def _swap_screen(self, screen: ctk.CTkFrame) -> None:
        if self._current_screen:
            self._current_screen.destroy()
        self._current_screen = screen
        screen.pack(fill="both", expand=True)

    # ── Event Handlers ────────────────────────────────────────

    def _on_login_success(self, student_no: str, session: requests.Session) -> None:
        self._student_no = student_no
        self._session    = session
        import threading
        def _fetch():
            self._student_name = fetch_user_name(session)
            save_remembered_user(student_no, self._student_name)
            save_cookies(session)
            self._root.after(0, self._show_courses)
        threading.Thread(target=_fetch, daemon=True).start()

    def _on_quick_resume(self, session: requests.Session) -> None:
        """Kaydedilmiş cookie + mevcut manifest ile login adımını atla."""
        from core.state import load_remembered_user
        remembered = load_remembered_user()
        if remembered:
            self._student_no   = remembered.get("student_no", "")
            self._student_name = remembered.get("name", "")
        self._session  = session
        self._courses  = load_manifest()
        self._selected = {}
        self._show_courses_cached()

    def _on_courses_continue(
        self, selected: dict[str, Course], dest_dir: Path
    ) -> None:
        self._selected = selected
        self._dest_dir = dest_dir
        self._show_filter()

    def _on_filter_start(self, dl_filter: DownloadFilter) -> None:
        self._dl_filter = dl_filter
        self._show_progress()

    def _cancel_download(self) -> None:
        if self._downloader:
            self._downloader.cancel()

    # ── Async Workers ─────────────────────────────────────────

    def _run_async(self, coro) -> None:
        """Verilen coroutine'i ayrı bir thread'de çalıştırır."""
        def _worker():
            loop = asyncio.new_event_loop()
            self._worker_loop = loop
            try:
                loop.run_until_complete(coro)
            finally:
                loop.close()
                self._worker_loop = None

        threading.Thread(target=_worker, daemon=True).start()

    async def _async_discover_courses(self) -> None:
        import threading
        from concurrent.futures import ThreadPoolExecutor

        def status(msg: str) -> None:
            self._gui_queue.put(("status", msg))

        crawler = BlackboardCrawler(self._session, on_status=status)
        try:
            courses = await asyncio.get_event_loop().run_in_executor(
                None, crawler.discover_courses,
            )
            self._courses = courses
            total = len(courses)
            self._gui_queue.put(("sync_total", total))

            done_count = 0
            lock = threading.Lock()
            start_ts = __import__("time").time()

            def crawl_one(course):
                crawler.crawl_course(course, courses)
                nonlocal done_count
                with lock:
                    done_count += 1
                    n = done_count
                elapsed = __import__("time").time() - start_ts
                eta_s = int(elapsed / n * (total - n)) if n > 0 and n < total else 0
                self._gui_queue.put(("sync_progress", (n, total, eta_s)))

            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=8) as pool:
                futs = [loop.run_in_executor(pool, crawl_one, c) for c in courses.values()]
                await asyncio.gather(*futs, return_exceptions=True)

            from core.state import save_manifest
            save_manifest(courses)
            self._gui_queue.put(("courses_done", dict(courses)))
        except Exception as exc:
            self._gui_queue.put(("status", f"Hata: {exc}"))

    async def _async_download(self, screen: ProgressScreen) -> None:
        def status(msg: str) -> None:
            self._gui_queue.put(("log", (msg, None)))

        def progress(course_name: str, done: int, total: int) -> None:
            self._gui_queue.put(("progress", (course_name, done, total)))

        def file_done(item: Item, success: bool) -> None:
            self._gui_queue.put(("file_done", (item, success)))

        def course_status(course_id: str, st: str) -> None:
            self._gui_queue.put(("course_status", (course_id, st)))

        self._downloader = BlackboardDownloader(
            session=self._session,
            base_dir=self._dest_dir,
            dl_filter=self._dl_filter,
            on_status=status,
            on_progress=progress,
            on_file_done=file_done,
            on_course_status=course_status,
        )
        try:
            await self._downloader.run(self._selected)
        except Exception as exc:
            self._gui_queue.put(("log", (f"İndirme hatası: {exc}", None)))
        finally:
            from core.state import get_stats
            stats = get_stats()
            self._gui_queue.put(("download_done", stats))

    # ── GUI Queue Polling ─────────────────────────────────────

    def _poll_queue(self) -> None:
        try:
            while True:
                event, payload = self._gui_queue.get_nowait()
                self._handle_event(event, payload)
        except queue.Empty:
            pass
        self._root.after(50, self._poll_queue)

    def _handle_event(self, event: str, payload) -> None:
        screen = self._current_screen
        if event == "status":
            pass
        elif event == "sync_total":
            if hasattr(screen, "set_sync_total"):
                screen.set_sync_total(payload)
        elif event == "sync_progress":
            done, total, eta_s = payload
            if hasattr(screen, "update_sync_progress"):
                screen.update_sync_progress(done, total, eta_s)
        elif event == "courses_done":
            courses_screen = CoursesScreen(
                self._root,
                on_continue=self._on_courses_continue,
                on_back=self._show_login,
            )
            self._swap_screen(courses_screen)
            courses_screen.set_student_name(self._student_name)
            courses_screen.load_courses(payload)
            courses_screen.set_loading(False)
        elif event == "log" and isinstance(screen, ProgressScreen):
            msg, color = payload
            screen.add_log(msg, color or "")
        elif event == "progress" and isinstance(screen, ProgressScreen):
            course_name, done, total = payload
            screen.update_progress(course_name, done, total)
        elif event == "file_done" and isinstance(screen, ProgressScreen):
            item, success = payload
            screen.on_file_done(item, success)
        elif event == "course_status" and isinstance(screen, ProgressScreen):
            course_id, st = payload
            screen.update_course_status(course_id, st)
        elif event == "download_done" and isinstance(screen, ProgressScreen):
            stats = payload
            screen.show_summary(
                downloaded=stats.get("downloaded", 0),
                failed=stats.get("failed", 0),
                skipped=stats.get("skipped", 0),
            )

    # ── Klavye ───────────────────────────────────────────────

    def _on_escape(self, _event=None) -> None:
        screen = self._current_screen
        if isinstance(screen, CoursesScreen):
            self._show_login()
        elif isinstance(screen, FilterScreen):
            self._show_courses_cached()
        elif isinstance(screen, ProgressScreen):
            screen._confirm_cancel()

    # ── Pencere Kapanma ───────────────────────────────────────

    def _on_close(self) -> None:
        if self._downloader:
            self._downloader.cancel()
        self._cleanup_auth()
        self._root.destroy()

    def _cleanup_auth(self) -> None:
        """Tüm login ekranlarındaki auth profillerini temizle."""
        import glob, shutil, tempfile
        screen = self._current_screen
        if isinstance(screen, LoginScreen) and hasattr(screen, "_auth") and screen._auth:
            screen._auth.cleanup()
        # Önceki çöküşlerden kalan temp profilleri de sil
        tmp = tempfile.gettempdir()
        for d in glob.glob(f"{tmp}/bb_sync_profile_*"):
            shutil.rmtree(d, ignore_errors=True)
