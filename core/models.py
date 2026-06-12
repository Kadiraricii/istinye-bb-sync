from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ItemType(Enum):
    PDF              = "pdf"
    PPTX             = "pptx"
    DOCX             = "docx"
    XLSX             = "xlsx"
    IMAGE            = "image"
    VIDEO_SHAREPOINT = "video_sharepoint"
    VIDEO_OTHER      = "video_other"
    LINK             = "link"
    SCORM            = "scorm"
    HTML             = "html"
    ARCHIVE          = "archive"
    OTHER            = "other"


class DownloadStatus(Enum):
    PENDING     = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED  = "downloaded"
    FAILED      = "failed"
    SKIPPED     = "skipped"


class CourseStatus(Enum):
    DISCOVERED   = "discovered"
    CRAWLING     = "crawling"
    CRAWLED      = "crawled"
    CRAWL_FAILED = "crawl_failed"


# Blackboard contentHandler.id → ItemType eşleştirmesi
CONTENT_HANDLER_MAP: dict[str, ItemType] = {
    "resource/x-bb-folder":       ItemType.OTHER,       # klasör — item değil
    "resource/x-bb-document":     ItemType.HTML,
    "resource/x-bb-file":         ItemType.OTHER,       # attachment'tan tip belirlenir
    "resource/x-bb-externallink": ItemType.LINK,
    "resource/x-bb-assignment":   ItemType.OTHER,
    "resource/x-bb-blti-link":    ItemType.LINK,
}

EXTENSION_MAP: dict[str, ItemType] = {
    ".pdf":  ItemType.PDF,
    ".pptx": ItemType.PPTX,  ".ppt": ItemType.PPTX,
    ".docx": ItemType.DOCX,  ".doc": ItemType.DOCX,
    ".xlsx": ItemType.XLSX,  ".xls": ItemType.XLSX,
    ".jpg":  ItemType.IMAGE, ".jpeg": ItemType.IMAGE,
    ".png":  ItemType.IMAGE, ".gif":  ItemType.IMAGE,
    ".svg":  ItemType.IMAGE, ".webp": ItemType.IMAGE,
    ".zip":  ItemType.ARCHIVE, ".rar": ItemType.ARCHIVE,
    ".7z":   ItemType.ARCHIVE, ".tar": ItemType.ARCHIVE,
    ".mp4":  ItemType.VIDEO_OTHER, ".mov": ItemType.VIDEO_OTHER,
    ".avi":  ItemType.VIDEO_OTHER, ".mkv": ItemType.VIDEO_OTHER,
    ".html": ItemType.HTML,  ".htm": ItemType.HTML,
}


@dataclass
class Item:
    id:          str
    name:        str
    type:        ItemType
    url:         str
    size_bytes:  Optional[int]  = None
    path_hint:   str            = ""   # "Hafta 1 / Ders Notları"
    uploaded_at: Optional[str]  = None # ISO 8601
    status:      DownloadStatus = DownloadStatus.PENDING
    local_path:  Optional[str]  = None
    error:       Optional[str]  = None
    attempts:    int            = 0

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "name":        self.name,
            "type":        self.type.value,
            "url":         self.url,
            "size_bytes":  self.size_bytes,
            "path_hint":   self.path_hint,
            "uploaded_at": self.uploaded_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Item:
        return cls(
            id=d["id"],
            name=d["name"],
            type=ItemType(d["type"]),
            url=d["url"],
            size_bytes=d.get("size_bytes"),
            path_hint=d.get("path_hint", ""),
            uploaded_at=d.get("uploaded_at"),
        )


@dataclass
class Course:
    id:          str
    name:        str
    url:         str
    course_code: str          = ""
    status:      CourseStatus = CourseStatus.DISCOVERED
    items:       dict         = field(default_factory=dict)   # item_id → Item
    instructors: list         = field(default_factory=list)   # ["Ad Soyad", ...]

    # ── Derived fields ────────────────────────────────────────

    @property
    def friendly_code(self) -> str:
        """'BIL210 - Ders Adı' → 'BIL210'"""
        return self.name.split(" - ")[0].strip() if " - " in self.name else ""

    @property
    def friendly_title(self) -> str:
        """'BIL210 - Ders Adı (1)' → 'Ders Adı'"""
        import re
        if " - " in self.name:
            title = " - ".join(self.name.split(" - ")[1:]).strip()
            return re.sub(r"\s*\(\d+\)\s*$", "", title).strip()
        return self.name

    @property
    def semester(self) -> str:
        """'2025-2026-2-10094-1' → 'Bahar 2025-2026'"""
        parts = self.course_code.split("-")
        if len(parts) >= 3 and parts[0].isdigit() and parts[1].isdigit():
            sem_map = {"1": "Güz", "2": "Bahar", "3": "Yaz"}
            label = sem_map.get(parts[2], "")
            if label:
                return f"{label} {parts[0]}-{parts[1]}"
        return ""

    # ── Counts ────────────────────────────────────────────────

    @property
    def file_count(self) -> int:
        return sum(
            1 for i in self.items.values()
            if i.type not in (ItemType.VIDEO_SHAREPOINT, ItemType.VIDEO_OTHER,
                              ItemType.LINK, ItemType.SCORM)
        )

    @property
    def video_count(self) -> int:
        return sum(
            1 for i in self.items.values()
            if i.type in (ItemType.VIDEO_SHAREPOINT, ItemType.VIDEO_OTHER)
        )

    @property
    def link_count(self) -> int:
        return sum(1 for i in self.items.values() if i.type == ItemType.LINK)

    @property
    def total_size_bytes(self) -> int:
        return sum(i.size_bytes or 0 for i in self.items.values())

    # ── Serialisation ─────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "name":        self.name,
            "url":         self.url,
            "course_code": self.course_code,
            "status":      self.status.value,
            "instructors": self.instructors,
            "items":       {k: v.to_dict() for k, v in self.items.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> Course:
        course = cls(
            id=d["id"],
            name=d["name"],
            url=d["url"],
            course_code=d.get("course_code", ""),
            status=CourseStatus(d.get("status", "discovered")),
            instructors=d.get("instructors", []),
        )
        for item_id, item_data in d.get("items", {}).items():
            course.items[item_id] = Item.from_dict(item_data)
        return course


@dataclass
class DownloadFilter:
    # Dosya türleri
    include_pdf:      bool = True
    include_pptx:     bool = True
    include_docx:     bool = True
    include_xlsx:     bool = True
    include_images:   bool = True
    include_archives: bool = True
    include_scorm:    bool = False
    include_other:    bool = True
    video_mode:       str  = "link"     # "download" | "link" | "skip"
    video_quality:    str  = "720"

    # Boyut filtresi (MB)
    min_size_mb: Optional[float] = None
    max_size_mb: Optional[float] = None

    # Tarih filtresi
    only_new:  bool            = False
    date_from: Optional[str]   = None
    date_to:   Optional[str]   = None

    # İsim filtresi
    keyword: Optional[str] = None

    # Eş zamanlı indirme
    concurrent: int = 2

    def allows_type(self, item_type: ItemType) -> bool:
        mapping = {
            ItemType.PDF:              self.include_pdf,
            ItemType.PPTX:             self.include_pptx,
            ItemType.DOCX:             self.include_docx,
            ItemType.XLSX:             self.include_xlsx,
            ItemType.IMAGE:            self.include_images,
            ItemType.ARCHIVE:          self.include_archives,
            ItemType.SCORM:            self.include_scorm,
            ItemType.HTML:             self.include_other,
            ItemType.OTHER:            self.include_other,
            ItemType.LINK:             False,  # linkler ayrı kaydedilir
            ItemType.VIDEO_SHAREPOINT: self.video_mode != "skip",
            ItemType.VIDEO_OTHER:      self.video_mode != "skip",
        }
        return mapping.get(item_type, False)

    def allows_item(self, item: Item) -> bool:
        if not self.allows_type(item.type):
            return False
        if self.min_size_mb and item.size_bytes:
            if item.size_bytes < self.min_size_mb * 1_048_576:
                return False
        if self.max_size_mb and item.size_bytes:
            if item.size_bytes > self.max_size_mb * 1_048_576:
                return False
        if self.keyword:
            if self.keyword.lower() not in item.name.lower():
                return False
        return True
