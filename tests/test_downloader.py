"""
Downloader mantığını test eder (gerçek HTTP isteği yapmadan).
"""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.models import Course, Item, ItemType, DownloadFilter
from core.downloader import BlackboardDownloader


def _make_dl(base_dir: Path = Path("/tmp/bb")) -> BlackboardDownloader:
    return BlackboardDownloader(
        session=MagicMock(),
        base_dir=base_dir,
        dl_filter=DownloadFilter(),
    )


# ── _resolve_course_dir ───────────────────────────────────────

class TestResolveCourseDir:
    def test_standard_name(self, tmp_path):
        dl = _make_dl(tmp_path)
        c = Course(id="1", name="BIL214 - Sistem Analizi ve Tasarımı (1)", url="")
        result = dl._resolve_course_dir(c)
        assert result.parent == tmp_path
        assert "BIL214" in result.name
        assert "Sistem_Analizi_ve_Tasarimi" in result.name

    def test_no_code(self, tmp_path):
        dl = _make_dl(tmp_path)
        c = Course(id="1", name="Matematik", url="")
        result = dl._resolve_course_dir(c)
        assert result.parent == tmp_path
        assert result.name == "Matematik"

    def test_turkish_chars_removed(self, tmp_path):
        dl = _make_dl(tmp_path)
        c = Course(id="1", name="BIL214 - Veri Yapıları ve Algoritmalar", url="")
        result = dl._resolve_course_dir(c)
        for char in "şğüöçışŞĞÜÖÇİ":
            assert char not in result.name

    def test_no_internal_id_in_folder_name(self, tmp_path):
        dl = _make_dl(tmp_path)
        c = Course(id="1", name="BIL214 - Test", url="",
                   course_code="2025-2026-2-10094-1")
        result = dl._resolve_course_dir(c)
        # İç ID klasör adında olmamalı
        assert "2025-2026-2-10094-1" not in result.name
        assert "10094" not in result.name


# ── _already_done ─────────────────────────────────────────────

class TestAlreadyDone:
    def test_no_progress(self):
        item = Item(id="i1", name="f.pdf", type=ItemType.PDF, url="")
        assert not BlackboardDownloader._already_done(item, {})

    def test_skipped(self):
        item = Item(id="i1", name="f.pdf", type=ItemType.PDF, url="")
        progress = {"i1": {"status": "skipped"}}
        assert BlackboardDownloader._already_done(item, progress)

    def test_downloaded_file_exists(self, tmp_path):
        f = tmp_path / "file.pdf"
        f.touch()
        item = Item(id="i1", name="f.pdf", type=ItemType.PDF, url="")
        progress = {"i1": {"status": "downloaded", "local_path": str(f)}}
        assert BlackboardDownloader._already_done(item, progress)

    def test_downloaded_file_missing(self, tmp_path):
        item = Item(id="i1", name="f.pdf", type=ItemType.PDF, url="")
        progress = {"i1": {"status": "downloaded",
                           "local_path": str(tmp_path / "gone.pdf")}}
        assert not BlackboardDownloader._already_done(item, progress)

    def test_downloaded_no_path(self):
        item = Item(id="i1", name="f.pdf", type=ItemType.PDF, url="")
        progress = {"i1": {"status": "downloaded", "local_path": ""}}
        assert not BlackboardDownloader._already_done(item, progress)

    def test_failed_is_not_done(self):
        item = Item(id="i1", name="f.pdf", type=ItemType.PDF, url="")
        progress = {"i1": {"status": "failed"}}
        assert not BlackboardDownloader._already_done(item, progress)


# ── _validate ─────────────────────────────────────────────────

class TestValidate:
    def test_missing_file(self, tmp_path):
        ok, reason = BlackboardDownloader._validate(tmp_path / "nope.pdf", ItemType.PDF)
        assert not ok
        assert "yok" in reason

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.pdf"
        f.write_bytes(b"")
        ok, reason = BlackboardDownloader._validate(f, ItemType.PDF)
        assert not ok
        assert "boş" in reason

    def test_html_error_page(self, tmp_path):
        f = tmp_path / "error.pdf"
        f.write_bytes(b"<!DOCTYPE html><html><body>Error 403</body></html>")
        ok, reason = BlackboardDownloader._validate(f, ItemType.PDF)
        assert not ok
        assert "HTML" in reason

    def test_valid_pdf_header(self, tmp_path):
        f = tmp_path / "valid.pdf"
        # Minimal PDF-like content (>1KB)
        f.write_bytes(b"%PDF-1.4" + b"x" * 2048)
        ok, _ = BlackboardDownloader._validate(f, ItemType.PDF)
        assert ok

    def test_too_small(self, tmp_path):
        f = tmp_path / "tiny.pdf"
        f.write_bytes(b"%PDF" + b"x" * 10)  # Sadece 14 byte
        ok, reason = BlackboardDownloader._validate(f, ItemType.PDF)
        assert not ok
        assert "küçük" in reason


# ── _resolve_item_dir ─────────────────────────────────────────

class TestResolveItemDir:
    def test_empty_hint(self, tmp_path):
        result = BlackboardDownloader._resolve_item_dir(tmp_path, "")
        assert result == tmp_path

    def test_with_hint(self, tmp_path):
        result = BlackboardDownloader._resolve_item_dir(tmp_path, "Week1/Notes")
        assert result == tmp_path / "Week1" / "Notes"

    def test_turkish_hint(self, tmp_path):
        result = BlackboardDownloader._resolve_item_dir(tmp_path, "Hafta 1/Ders Notları")
        assert result.parent.parent == tmp_path
        for char in "şğüöçıİŞĞÜÖÇ":
            assert char not in str(result)
