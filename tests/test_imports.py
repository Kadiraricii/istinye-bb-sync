"""
Tüm modüllerin hatasız import edildiğini doğrular.
Import hatası → eksik paket veya syntax hatası demektir.
"""


def test_import_customtkinter():
    import customtkinter  # noqa: F401


def test_import_httpx():
    import httpx  # noqa: F401


def test_import_aiofiles():
    import aiofiles  # noqa: F401


def test_import_requests():
    import requests  # noqa: F401


def test_import_slugify():
    from slugify import slugify  # noqa: F401


def test_import_playwright():
    from playwright.async_api import async_playwright  # noqa: F401


def test_import_yt_dlp():
    import yt_dlp  # noqa: F401


# ── Core modülleri ────────────────────────────────────────────

def test_import_core_config():
    from core.config import (
        BASE_DIR, DATA_DIR, DOWNLOADS_DIR,
        MANIFEST_FILE, PROGRESS_FILE, REMEMBER_FILE,
        BB_BASE, BB_ULTRA, BB_API, EMAIL_DOMAIN,
        WINDOW_WIDTH, WINDOW_HEIGHT, COMPACT_HEIGHT,
    )
    assert WINDOW_WIDTH > 0
    assert WINDOW_HEIGHT > 0


def test_import_core_models():
    from core.models import (
        ItemType, DownloadStatus, CourseStatus,
        Item, Course, DownloadFilter,
        CONTENT_HANDLER_MAP, EXTENSION_MAP,
    )
    assert len(EXTENSION_MAP) > 0


def test_import_core_state():
    from core.state import (
        save_cookies, load_cookies, delete_cookies,
        save_remembered_user, load_remembered_user, clear_remembered_user,
        save_manifest, load_manifest,
        load_progress, save_progress,
        mark_downloaded, mark_failed, mark_skipped,
        get_stats, check_disk_space,
        clear_progress_for_courses, clear_failed_for_courses,
        slugify_filename, unique_path, request_delay,
        ensure_dirs,
    )


def test_import_core_downloader():
    from core.downloader import BlackboardDownloader  # noqa: F401


def test_import_core_auth():
    from core.auth import BlackboardAuth  # noqa: F401


# ── GUI modülleri ─────────────────────────────────────────────

def test_import_gui_theme():
    from gui.theme import (
        BG_BASE, BG_ELEVATED, BG_HOVER, BORDER,
        ACCENT, SUCCESS, ERROR, WARNING,
        TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY,
        FONT_BODY, FONT_SMALL,
        BTN_PRIMARY, BTN_SECONDARY, BTN_GHOST,
    )
    assert len(ACCENT) > 0


def test_import_gui_screen_login():
    from gui.screen_login import LoginScreen  # noqa: F401


def test_import_gui_screen_courses():
    from gui.screen_courses import CoursesScreen  # noqa: F401


def test_import_gui_screen_filter():
    from gui.screen_filter import FilterScreen  # noqa: F401


def test_import_gui_screen_progress():
    from gui.screen_progress import ProgressScreen  # noqa: F401


def test_import_gui_app():
    from gui.app import App  # noqa: F401
