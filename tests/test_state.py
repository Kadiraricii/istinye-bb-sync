"""
State yönetimi (progress, manifest, cookies) fonksiyonlarını test eder.
Tüm dosya I/O tmp_path ile izole edilmiştir — disk kalıcı bir şey bırakmaz.
"""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from core.models import Course, Item, ItemType


# ── Yardımcı ─────────────────────────────────────────────────

def _patch_progress(tmp_path: Path):
    """PROGRESS_FILE'ı tmp_path'e yönlendirir."""
    return patch("core.state.PROGRESS_FILE", tmp_path / "progress.json")


def _patch_manifest(tmp_path: Path):
    return patch("core.state.MANIFEST_FILE", tmp_path / "manifest.json")


def _patch_remember(tmp_path: Path):
    return patch("core.state.REMEMBER_FILE", tmp_path / "remember.json")


def _patch_data_dir(tmp_path: Path):
    return patch("core.state.DATA_DIR", tmp_path)


# ── slugify_filename ──────────────────────────────────────────

class TestSlugifyFilename:
    def test_turkish_chars(self):
        from core.state import slugify_filename
        result = slugify_filename("Türkçe İşlemler")
        for bad in "şğüöçışŞĞÜÖÇİ":
            assert bad not in result

    def test_empty_string(self):
        from core.state import slugify_filename
        assert slugify_filename("") == "dosya"

    def test_with_extension(self):
        from core.state import slugify_filename
        result = slugify_filename("Ders Notu", ".pdf")
        assert result.endswith(".pdf")

    def test_no_filesystem_unsafe_chars(self):
        from core.state import slugify_filename
        result = slugify_filename("file: name <bad>")
        for char in '<>:"/\\|?*':
            assert char not in result

    def test_windows_reserved_names(self):
        from core.state import slugify_filename
        # "CON" is a Windows reserved name — slugify should transform it
        result = slugify_filename("CON")
        assert len(result) > 0  # At minimum, returns something


# ── unique_path ───────────────────────────────────────────────

class TestUniquePath:
    def test_new_file(self, tmp_path):
        from core.state import unique_path
        p = unique_path(tmp_path, "test.pdf")
        assert p == tmp_path / "test.pdf"

    def test_existing_file(self, tmp_path):
        from core.state import unique_path
        (tmp_path / "test.pdf").touch()
        p = unique_path(tmp_path, "test.pdf")
        assert p == tmp_path / "test_2.pdf"

    def test_multiple_existing(self, tmp_path):
        from core.state import unique_path
        (tmp_path / "test.pdf").touch()
        (tmp_path / "test_2.pdf").touch()
        p = unique_path(tmp_path, "test.pdf")
        assert p == tmp_path / "test_3.pdf"


# ── mark_downloaded / mark_failed / mark_skipped ─────────────

class TestMarkProgress:
    def test_mark_downloaded(self, tmp_path):
        from core.state import mark_downloaded, load_progress
        with _patch_progress(tmp_path), _patch_data_dir(tmp_path):
            mark_downloaded("i1", "/path/file.pdf")
            p = load_progress()
        assert p["i1"]["status"] == "downloaded"
        assert p["i1"]["local_path"] == "/path/file.pdf"

    def test_mark_failed(self, tmp_path):
        from core.state import mark_failed, load_progress
        with _patch_progress(tmp_path), _patch_data_dir(tmp_path):
            mark_failed("i2", "HTTP 404", 3)
            p = load_progress()
        assert p["i2"]["status"] == "failed"
        assert p["i2"]["error"] == "HTTP 404"
        assert p["i2"]["attempts"] == 3

    def test_mark_skipped(self, tmp_path):
        from core.state import mark_skipped, load_progress
        with _patch_progress(tmp_path), _patch_data_dir(tmp_path):
            mark_skipped("i3", "link")
            p = load_progress()
        assert p["i3"]["status"] == "skipped"
        assert p["i3"]["reason"] == "link"

    def test_multiple_items_accumulate(self, tmp_path):
        from core.state import mark_downloaded, mark_failed, load_progress
        with _patch_progress(tmp_path), _patch_data_dir(tmp_path):
            mark_downloaded("i1", "/a.pdf")
            mark_failed("i2", "err", 1)
            p = load_progress()
        assert "i1" in p
        assert "i2" in p


# ── clear_failed_for_courses ──────────────────────────────────

class TestClearFailed:
    def _make_course(self, items_map: dict) -> Course:
        c = Course(id="c1", name="Test", url="")
        for iid, itype in items_map.items():
            c.items[iid] = Item(id=iid, name=f"{iid}.pdf", type=itype, url="")
        return c

    def test_clears_only_failed(self, tmp_path):
        from core.state import (
            mark_failed, mark_downloaded, mark_skipped,
            clear_failed_for_courses, load_progress,
        )
        course = self._make_course({"i1": ItemType.PDF, "i2": ItemType.PDF, "i3": ItemType.PDF})
        with _patch_progress(tmp_path), _patch_data_dir(tmp_path):
            mark_failed("i1", "err", 1)
            mark_downloaded("i2", "/f.pdf")
            mark_skipped("i3", "link")
            clear_failed_for_courses({"c1": course})
            p = load_progress()
        assert "i1" not in p           # failed → cleared
        assert p["i2"]["status"] == "downloaded"   # downloaded → kept
        assert p["i3"]["status"] == "skipped"      # skipped → kept

    def test_no_progress_file(self, tmp_path):
        from core.state import clear_failed_for_courses
        course = self._make_course({"i1": ItemType.PDF})
        # Dosya yoksa exception fırlamamalı
        with _patch_progress(tmp_path):
            clear_failed_for_courses({"c1": course})


# ── clear_progress_for_courses ────────────────────────────────

class TestClearProgress:
    def test_clears_all_statuses(self, tmp_path):
        from core.state import (
            mark_downloaded, mark_failed, mark_skipped,
            clear_progress_for_courses, load_progress,
        )
        course = Course(id="c1", name="T", url="")
        for iid in ("i1", "i2", "i3"):
            course.items[iid] = Item(id=iid, name=f"{iid}.pdf", type=ItemType.PDF, url="")

        with _patch_progress(tmp_path), _patch_data_dir(tmp_path):
            mark_downloaded("i1", "/a.pdf")
            mark_failed("i2", "err", 1)
            mark_skipped("i3", "link")
            clear_progress_for_courses({"c1": course})
            p = load_progress()
        assert "i1" not in p
        assert "i2" not in p
        assert "i3" not in p


# ── get_stats ─────────────────────────────────────────────────

def test_get_stats(tmp_path):
    from core.state import mark_downloaded, mark_failed, mark_skipped, get_stats
    with _patch_progress(tmp_path), _patch_data_dir(tmp_path):
        mark_downloaded("i1", "/a.pdf")
        mark_downloaded("i2", "/b.pdf")
        mark_failed("i3", "err", 1)
        mark_skipped("i4", "link")
        stats = get_stats()
    assert stats["downloaded"] == 2
    assert stats["failed"] == 1
    assert stats["skipped"] == 1


# ── remember_user ─────────────────────────────────────────────

def test_save_load_remembered_user(tmp_path):
    from core.state import save_remembered_user, load_remembered_user
    with _patch_remember(tmp_path), _patch_data_dir(tmp_path):
        save_remembered_user("2200001234", "Ali Veli")
        r = load_remembered_user()
    assert r["student_no"] == "2200001234"
    assert r["name"] == "Ali Veli"


def test_load_remembered_user_missing(tmp_path):
    from core.state import load_remembered_user
    with _patch_remember(tmp_path):
        assert load_remembered_user() is None
