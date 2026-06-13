"""
Core veri modellerinin doğru çalıştığını test eder.
"""
import pytest
from core.models import Course, Item, ItemType, DownloadFilter


# ── Course property'leri ──────────────────────────────────────

class TestCourseFriendlyCode:
    def test_standard_format(self):
        c = Course(id="1", name="BIL214 - Sistem Analizi ve Tasarımı", url="")
        assert c.friendly_code == "BIL214"

    def test_no_dash(self):
        c = Course(id="1", name="Matematik", url="")
        assert c.friendly_code == ""

    def test_multiple_dashes(self):
        c = Course(id="1", name="BIL214 - Konu - Alt Konu", url="")
        assert c.friendly_code == "BIL214"


class TestCourseFriendlyTitle:
    def test_strips_number_suffix(self):
        c = Course(id="1", name="BIL214 - Sistem Analizi ve Tasarımı (1)", url="")
        assert c.friendly_title == "Sistem Analizi ve Tasarımı"

    def test_no_code(self):
        c = Course(id="1", name="Matematik", url="")
        assert c.friendly_title == "Matematik"

    def test_multiple_dashes(self):
        c = Course(id="1", name="BIL214 - A - B", url="")
        assert c.friendly_title == "A - B"

    def test_no_number_suffix(self):
        c = Course(id="1", name="BIL214 - Sistem Analizi", url="")
        assert c.friendly_title == "Sistem Analizi"


class TestCourseSemester:
    def test_bahar(self):
        c = Course(id="1", name="X", url="", course_code="2025-2026-2-10094-1")
        assert c.semester == "Bahar 2025-2026"

    def test_guz(self):
        c = Course(id="1", name="X", url="", course_code="2025-2026-1-10094-1")
        assert c.semester == "Güz 2025-2026"

    def test_yaz(self):
        c = Course(id="1", name="X", url="", course_code="2025-2026-3-10094-1")
        assert c.semester == "Yaz 2025-2026"

    def test_invalid(self):
        c = Course(id="1", name="X", url="", course_code="")
        assert c.semester == ""


# ── DownloadFilter ────────────────────────────────────────────

def _item(item_type: ItemType, item_id: str = "i1") -> Item:
    return Item(id=item_id, name="test", type=item_type, url="http://x.com")


class TestDownloadFilter:
    def test_allows_pdf_by_default(self):
        assert DownloadFilter().allows_item(_item(ItemType.PDF))

    def test_blocks_pdf_when_disabled(self):
        assert not DownloadFilter(include_pdf=False).allows_item(_item(ItemType.PDF))

    def test_blocks_excluded_id(self):
        f = DownloadFilter(excluded_ids={"i1"})
        assert not f.allows_item(_item(ItemType.PDF, "i1"))

    def test_allows_non_excluded_id(self):
        f = DownloadFilter(excluded_ids={"i2"})
        assert f.allows_item(_item(ItemType.PDF, "i1"))

    def test_video_skip(self):
        f = DownloadFilter(video_mode="skip")
        assert not f.allows_item(_item(ItemType.VIDEO_SHAREPOINT))
        assert not f.allows_item(_item(ItemType.VIDEO_OTHER))

    def test_video_link(self):
        f = DownloadFilter(video_mode="link")
        assert f.allows_item(_item(ItemType.VIDEO_SHAREPOINT))

    def test_video_download(self):
        f = DownloadFilter(video_mode="download")
        assert f.allows_item(_item(ItemType.VIDEO_OTHER))

    def test_scorm_disabled_by_default(self):
        assert not DownloadFilter().allows_item(_item(ItemType.SCORM))

    def test_link_allowed_by_default(self):
        assert DownloadFilter().allows_item(_item(ItemType.LINK))

    def test_link_disabled(self):
        assert not DownloadFilter(include_links=False).allows_item(_item(ItemType.LINK))

    def test_size_filter_min(self):
        item = Item(id="i1", name="f.pdf", type=ItemType.PDF,
                    url="x", size_bytes=500 * 1024)   # 500 KB
        assert not DownloadFilter(min_size_mb=1.0).allows_item(item)
        assert DownloadFilter(min_size_mb=0.1).allows_item(item)

    def test_size_filter_max(self):
        item = Item(id="i1", name="f.pdf", type=ItemType.PDF,
                    url="x", size_bytes=200 * 1024 * 1024)  # 200 MB
        assert not DownloadFilter(max_size_mb=100.0).allows_item(item)
        assert DownloadFilter(max_size_mb=500.0).allows_item(item)

    def test_keyword_filter(self):
        item = Item(id="i1", name="Hafta5_Ders.pdf", type=ItemType.PDF, url="x")
        assert DownloadFilter(keyword="Hafta5").allows_item(item)
        assert not DownloadFilter(keyword="Hafta6").allows_item(item)


# ── Course serialisation ──────────────────────────────────────

def test_course_to_from_dict():
    c = Course(id="c1", name="BIL214 - Test", url="http://bb.com",
               course_code="2025-2026-2-1-1")
    item = Item(id="i1", name="file.pdf", type=ItemType.PDF, url="http://bb.com/file.pdf")
    c.items["i1"] = item

    d = c.to_dict()
    c2 = Course.from_dict(d)

    assert c2.id == "c1"
    assert c2.name == "BIL214 - Test"
    assert c2.friendly_code == "BIL214"
    assert "i1" in c2.items
    assert c2.items["i1"].type == ItemType.PDF


def test_item_to_from_dict():
    item = Item(
        id="i1", name="lecture.pdf",
        type=ItemType.PDF, url="http://example.com",
        size_bytes=1024, path_hint="Week1/Notes",
    )
    d = item.to_dict()
    item2 = Item.from_dict(d)
    assert item2.id == "i1"
    assert item2.type == ItemType.PDF
    assert item2.path_hint == "Week1/Notes"
