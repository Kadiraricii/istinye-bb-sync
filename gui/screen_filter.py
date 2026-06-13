from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from core.models import Course, DownloadFilter, Item, ItemType
from gui.theme import (
    ACCENT, BG_BASE,
    BTN_GHOST, BTN_PRIMARY,
    FONT_HEADING,
    SUCCESS, TEXT_PRIMARY,
)

_DEFAULT_DIR = Path.home() / "Downloads" / "Blackboard"

# Renk sabitleri
_ON_BG   = "#061a10"
_ON_BDR  = "#10b981"
_ON_TXT  = "#34d399"
_OFF_BG  = "#0b1422"
_OFF_BDR = "#1a2d44"
_OFF_TXT = "#4a6888"
_HOV_BG  = "#0e1e30"

# Tree renkleri
_TREE_BG     = "#080e1a"
_TREE_SEL_BG = "#061a10"
_TREE_SEL_FG = "#34d399"

# Chip'te gösterilecek dosya türleri (SCORM yok)
_TYPE_CHIPS = [
    ("📄", "PDF",    ItemType.PDF),
    ("📊", "Sunum",  ItemType.PPTX),
    ("📝", "Belge",  ItemType.DOCX),
    ("📗", "Tablo",  ItemType.XLSX),
    ("🖼",  "Resim",  ItemType.IMAGE),
    ("📦", "Arşiv",  ItemType.ARCHIVE),
    ("🖥",  "Kod",    ItemType.CODE),
    ("📁", "Diğer",  ItemType.OTHER),
]

_TYPE_TO_VAR = {
    ItemType.PDF:     "pdf",
    ItemType.PPTX:    "pptx",
    ItemType.DOCX:    "docx",
    ItemType.XLSX:    "xlsx",
    ItemType.IMAGE:   "img",
    ItemType.ARCHIVE: "arch",
    ItemType.CODE:    "code",
    ItemType.OTHER:   "other",
    ItemType.HTML:    "other",
}

_ITEM_ICON = {
    ItemType.PDF:              "📄",
    ItemType.PPTX:             "📊",
    ItemType.DOCX:             "📝",
    ItemType.XLSX:             "📗",
    ItemType.IMAGE:            "🖼",
    ItemType.ARCHIVE:          "📦",
    ItemType.SCORM:            "🎓",
    ItemType.HTML:             "📁",
    ItemType.OTHER:            "📁",
    ItemType.CODE:             "🖥",
    ItemType.VIDEO_SHAREPOINT: "🎬",
    ItemType.VIDEO_OTHER:      "🎬",
    ItemType.LINK:             "🔗",
}

_SPEED_OPTS = [
    (1, "×1"),
    (2, "×2"),
    (5, "×5"),
]


def _bind_tree(widget, event: str, handler) -> None:
    widget.bind(event, handler)
    for child in widget.winfo_children():
        _bind_tree(child, event, handler)


# ── Toggle Chip ───────────────────────────────────────────────

class _ToggleChip(ctk.CTkFrame):
    def __init__(
        self, master, icon: str, text: str, var: ctk.BooleanVar,
        command: Optional[Callable] = None, disabled: bool = False,
    ) -> None:
        super().__init__(
            master, corner_radius=20, cursor="hand2",
            fg_color=_OFF_BG, border_width=1, border_color=_OFF_BDR,
        )
        self._var = var
        self._command = command
        self._disabled = disabled

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=12, pady=6)

        self._icon_lbl = ctk.CTkLabel(inner, text=icon, font=("Inter", 13), cursor="hand2", text_color=_OFF_TXT)
        self._icon_lbl.pack(side="left", padx=(0, 5))

        self._text_lbl = ctk.CTkLabel(inner, text=text, font=("Inter", 11, "bold"), cursor="hand2", text_color=_OFF_TXT)
        self._text_lbl.pack(side="left")

        for w in (self, inner, self._icon_lbl, self._text_lbl):
            w.bind("<Button-1>", self._on_click)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

        self._refresh()

    def set_disabled(self, disabled: bool) -> None:
        self._disabled = disabled
        self._refresh()

    def _on_click(self, _=None) -> None:
        if self._disabled:
            return
        self._var.set(not self._var.get())
        self._refresh()
        if self._command:
            self._command()

    def _on_enter(self, _=None) -> None:
        if not self._var.get() and not self._disabled:
            self.configure(fg_color=_HOV_BG, border_color="#253a56")

    def _on_leave(self, _=None) -> None:
        if not self._var.get() or self._disabled:
            self.configure(fg_color=_OFF_BG, border_color=_OFF_BDR)

    def _refresh(self) -> None:
        if self._disabled:
            self.configure(fg_color="#0b1422", border_color="#1a2540")
            self._icon_lbl.configure(text_color="#2e4060")
            self._text_lbl.configure(text_color="#2e4060")
        elif self._var.get():
            self.configure(fg_color=_ON_BG, border_color=_ON_BDR)
            self._icon_lbl.configure(text_color=_ON_TXT)
            self._text_lbl.configure(text_color=_ON_TXT)
        else:
            self.configure(fg_color=_OFF_BG, border_color=_OFF_BDR)
            self._icon_lbl.configure(text_color=_OFF_TXT)
            self._text_lbl.configure(text_color=_OFF_TXT)


# ── Video Segment (kompakt) ───────────────────────────────────

class _VideoSegment(ctk.CTkFrame):
    """Segmented control için tek bir video modu butonu."""

    def __init__(
        self, master, icon: str, label: str,
        value: str, var: ctk.StringVar,
        pos: str = "mid",   # "left" | "mid" | "right"
        command: Optional[Callable] = None,
    ) -> None:
        radii = {"left": (10, 0, 0, 10), "mid": (0, 0, 0, 0), "right": (0, 10, 10, 0)}
        r = radii.get(pos, (0, 0, 0, 0))
        super().__init__(
            master, cursor="hand2",
            fg_color=_OFF_BG, border_width=1, border_color=_OFF_BDR,
            corner_radius=0,
        )
        self._value = value
        self._var = var
        self._command = command

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        self._icon_lbl = ctk.CTkLabel(inner, text=icon, font=("Inter", 14), cursor="hand2", text_color=_OFF_TXT)
        self._icon_lbl.pack(side="left", padx=(0, 6))

        self._lbl = ctk.CTkLabel(inner, text=label, font=("Inter", 11, "bold"), cursor="hand2", text_color=_OFF_TXT)
        self._lbl.pack(side="left")

        var.trace_add("write", lambda *_: self._refresh())
        for w in (self, inner, self._icon_lbl, self._lbl):
            w.bind("<Button-1>", self._on_click)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
        self._refresh()

    def _on_click(self, _=None) -> None:
        self._var.set(self._value)
        if self._command:
            self._command()

    def _on_enter(self, _=None) -> None:
        if self._var.get() != self._value:
            self.configure(fg_color=_HOV_BG)

    def _on_leave(self, _=None) -> None:
        if self._var.get() != self._value:
            self.configure(fg_color=_OFF_BG)

    def _refresh(self) -> None:
        if self._var.get() == self._value:
            self.configure(fg_color=_ON_BG, border_color=_ON_BDR)
            self._icon_lbl.configure(text_color=_ON_TXT)
            self._lbl.configure(text_color=_ON_TXT)
        else:
            self.configure(fg_color=_OFF_BG, border_color=_OFF_BDR)
            self._icon_lbl.configure(text_color=_OFF_TXT)
            self._lbl.configure(text_color=_OFF_TXT)


# ── Kalite Pill ───────────────────────────────────────────────

class _QualityPill(ctk.CTkFrame):
    def __init__(self, master, text: str, var: ctk.StringVar) -> None:
        super().__init__(master, corner_radius=14, cursor="hand2",
                         fg_color=_OFF_BG, border_width=1, border_color=_OFF_BDR,
                         height=28, width=58)
        self.grid_propagate(False)
        self._var = var
        self._text = text
        self._lbl = ctk.CTkLabel(self, text=text, font=("Inter", 10, "bold"),
                                  cursor="hand2", text_color=_OFF_TXT)
        self._lbl.place(relx=0.5, rely=0.5, anchor="center")
        var.trace_add("write", lambda *_: self._refresh())
        for w in (self, self._lbl):
            w.bind("<Button-1>", self._on_click)
        self._refresh()

    def _on_click(self, _=None) -> None:
        self._var.set(self._text)

    def _refresh(self) -> None:
        if self._var.get() == self._text:
            self.configure(fg_color=_ON_BG, border_color=_ON_BDR)
            self._lbl.configure(text_color=_ON_TXT)
        else:
            self.configure(fg_color=_OFF_BG, border_color=_OFF_BDR)
            self._lbl.configure(text_color=_OFF_TXT)


# ── Hız Pill (yatay, kompakt) ─────────────────────────────────

class _SpeedPill(ctk.CTkFrame):
    def __init__(self, master, label: str, value: int, var: ctk.IntVar) -> None:
        super().__init__(master, corner_radius=16, cursor="hand2",
                         fg_color=_OFF_BG, border_width=1, border_color=_OFF_BDR,
                         height=32, width=48)
        self.grid_propagate(False)
        self._var = var
        self._value = value

        self._lbl = ctk.CTkLabel(self, text=label, font=("Inter", 12, "bold"),
                                  text_color=_OFF_TXT, cursor="hand2")
        self._lbl.place(relx=0.5, rely=0.5, anchor="center")

        var.trace_add("write", lambda *_: self._refresh())
        for w in (self, self._lbl):
            w.bind("<Button-1>", self._on_click)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
        self._refresh()

    def _on_click(self, _=None) -> None:
        self._var.set(self._value)

    def _on_enter(self, _=None) -> None:
        if self._var.get() != self._value:
            self.configure(fg_color=_HOV_BG, border_color="#253a56")

    def _on_leave(self, _=None) -> None:
        if self._var.get() != self._value:
            self.configure(fg_color=_OFF_BG, border_color=_OFF_BDR)

    def _refresh(self) -> None:
        if self._var.get() == self._value:
            self.configure(fg_color=_ON_BG, border_color=_ON_BDR)
            self._lbl.configure(text_color=_ON_TXT)
        else:
            self.configure(fg_color=_OFF_BG, border_color=_OFF_BDR)
            self._lbl.configure(text_color=_OFF_TXT)


# ── Ana Ekran ─────────────────────────────────────────────────

class FilterScreen(ctk.CTkFrame):

    def __init__(
        self,
        master: ctk.CTk,
        on_start:  Callable[[DownloadFilter], None],
        on_back:   Callable,
        dest_dir:  Optional[Path] = None,
    ) -> None:
        super().__init__(master, fg_color=BG_BASE, corner_radius=0)
        self._on_start = on_start
        self._on_back  = on_back
        self._dest_dir = dest_dir or _DEFAULT_DIR
        self._courses: dict[str, Course] = {}

        # Dosya türü değişkenleri
        self._pdf   = ctk.BooleanVar(value=True)
        self._pptx  = ctk.BooleanVar(value=True)
        self._docx  = ctk.BooleanVar(value=True)
        self._xlsx  = ctk.BooleanVar(value=True)
        self._img   = ctk.BooleanVar(value=True)
        self._arch  = ctk.BooleanVar(value=True)
        self._code  = ctk.BooleanVar(value=True)
        self._other = ctk.BooleanVar(value=True)
        self._link  = ctk.BooleanVar(value=True)

        self._type_vars = {
            "pdf":   self._pdf,
            "pptx":  self._pptx,
            "docx":  self._docx,
            "xlsx":  self._xlsx,
            "img":   self._img,
            "arch":  self._arch,
            "code":  self._code,
            "other": self._other,
            "link":  self._link,
        }

        self._video_enabled = ctk.BooleanVar(value=True)
        self._video_mode    = ctk.StringVar(value="link")
        self._video_quality = ctk.StringVar(value="720")
        self._concurrent    = ctk.IntVar(value=2)

        # Tree state: ID → checked (True=indir, False=atla)
        self._item_checked: dict[str, bool] = {}
        # Tree node ID → item ID
        self._node_to_item: dict[str, str] = {}
        # Tüm item'lar (ID → Item) — tree için flat liste
        self._all_items: dict[str, Item] = {}

        self._chip_widgets: dict[str, _ToggleChip] = {}

        self._build()

    # ── Layout ───────────────────────────────────────────────

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_content()
        self._build_footer()

    def _build_header(self) -> None:
        hdr = ctk.CTkFrame(self, fg_color="#0a0f1e", corner_radius=0, height=56)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)
        hdr.grid_propagate(False)

        ctk.CTkButton(hdr, text="← Geri", command=self._on_back, **BTN_GHOST).grid(
            row=0, column=0, padx=14, pady=12, sticky="w")

        title_row = ctk.CTkFrame(hdr, fg_color="transparent")
        title_row.grid(row=0, column=1)
        ctk.CTkLabel(title_row, text="⚙", font=("Inter", 15), text_color=ACCENT).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(title_row, text="İndirme Ayarları", font=FONT_HEADING, text_color=TEXT_PRIMARY).pack(side="left")

        ctk.CTkButton(hdr, text="Sıfırla", command=self._reset, **BTN_GHOST).grid(row=0, column=2, padx=14)
        ctk.CTkFrame(hdr, height=1, fg_color="#141e32", corner_radius=0).grid(row=1, column=0, columnspan=3, sticky="ew")

    def _build_content(self) -> None:
        scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG_BASE,
            scrollbar_button_color="#1a2d44",
            scrollbar_button_hover_color="#253a56",
        )
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        self._build_controls_card(scroll, row=0)
        self._build_tree_section(scroll, row=1)
        ctk.CTkFrame(scroll, height=16, fg_color="transparent").grid(row=2, column=0)

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color="#0a0f1e", corner_radius=0, height=64)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(1, weight=1)
        footer.grid_propagate(False)

        ctk.CTkFrame(footer, height=1, fg_color="#141e32", corner_radius=0).grid(
            row=0, column=0, columnspan=3, sticky="ew")

        # Sol: hız seçici
        speed_col = ctk.CTkFrame(footer, fg_color="transparent")
        speed_col.grid(row=1, column=0, padx=14, pady=14, sticky="w")

        ctk.CTkLabel(speed_col, text="Eş zamanlı:", font=("Inter", 10),
                     text_color=_OFF_TXT).pack(side="left", padx=(0, 6))
        for val, label in _SPEED_OPTS:
            _SpeedPill(speed_col, label, val, self._concurrent).pack(side="left", padx=2)

        # Orta: özet
        self._lbl_summary = ctk.CTkLabel(
            footer, text="", font=("Inter", 11, "bold"), text_color=SUCCESS,
        )
        self._lbl_summary.grid(row=1, column=1)

        # Sağ: başlat
        ctk.CTkButton(
            footer, text="İndirmeyi Başlat →",
            command=self._start, **BTN_PRIMARY, width=160,
        ).grid(row=1, column=2, padx=12, pady=12)

    # ── Bölüm helper ─────────────────────────────────────────

    def _section(self, parent, title: str, icon: str, row: int) -> ctk.CTkFrame:
        outer = ctk.CTkFrame(parent, fg_color="#0d1120", corner_radius=12,
                             border_width=1, border_color="#141e35")
        outer.grid(row=row, column=0, sticky="ew", padx=18, pady=(14, 0))
        outer.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(outer, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=16, pady=(14, 10), sticky="w")

        ctk.CTkFrame(hdr, width=3, height=14, corner_radius=2, fg_color=ACCENT).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(hdr, text=icon, font=("Inter", 11), text_color=ACCENT).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(hdr, text=title, font=("Inter", 10, "bold"), text_color="#3a5a78").pack(side="left")

        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 16))
        return inner

    # ── Birleşik Kontroller Kartı ─────────────────────────────

    def _build_controls_card(self, parent, row: int) -> None:
        """Dosya türleri + video seçeneği tek kompakt kart."""
        card = ctk.CTkFrame(parent, fg_color="#0d1120", corner_radius=12,
                            border_width=1, border_color="#141e35")
        card.grid(row=row, column=0, sticky="ew", padx=18, pady=(14, 0))
        card.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="ew", padx=14, pady=12)
        inner.grid_columnconfigure(0, weight=1)

        # — Chip grid (5 sütun, 2 satır) —
        # Tüm chip'ler: 8 dosya türü + Video + Link = 10 chip → 5+5
        all_chips = [
            # (icon, label, var_key, command, item_type_or_None)
            ("📄", "PDF",    "pdf",  self._on_type_change,       None),
            ("📊", "Sunum",  "pptx", self._on_type_change,       None),
            ("📝", "Belge",  "docx", self._on_type_change,       None),
            ("📗", "Tablo",  "xlsx", self._on_type_change,       None),
            ("🖼",  "Resim",  "img",  self._on_type_change,       None),
            ("📦", "Arşiv",  "arch", self._on_type_change,       None),
            ("🖥",  "Kod",    "code", self._on_type_change,       None),
            ("📁", "Diğer",  "other",self._on_type_change,       None),
            ("🎬", "Video",  None,   self._on_video_chip_change, "video"),
            ("🔗", "Link",   "link", self._on_type_change,       "link"),
        ]

        COLS = 5
        chips_frame = ctk.CTkFrame(inner, fg_color="transparent")
        chips_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for c in range(COLS):
            chips_frame.grid_columnconfigure(c, weight=1)

        for idx, (icon, label, var_key, cmd, special) in enumerate(all_chips):
            r, c = divmod(idx, COLS)
            if special == "video":
                chip = _ToggleChip(chips_frame, icon, label, self._video_enabled, command=cmd)
            elif var_key:
                chip = _ToggleChip(chips_frame, icon, label, self._type_vars[var_key], command=cmd)
                self._chip_widgets[var_key] = chip
            chip.grid(row=r, column=c, padx=3, pady=3, sticky="ew")

        # — Video alt bölümü (chip seçilince açılır) —
        self._video_section = ctk.CTkFrame(inner, fg_color="transparent")
        self._video_section.grid(row=1, column=0, sticky="ew")
        self._video_section.grid_columnconfigure(0, weight=1)

        # Ayırıcı
        ctk.CTkFrame(self._video_section, height=1, fg_color="#141e35").grid(
            row=0, column=0, sticky="ew", pady=(0, 8))

        vid_row = ctk.CTkFrame(self._video_section, fg_color="transparent")
        vid_row.grid(row=1, column=0, sticky="ew")

        ctk.CTkLabel(vid_row, text="Kayıt", font=("Inter", 10, "bold"),
                     text_color=_OFF_TXT, width=36).pack(side="left", padx=(0, 8))

        seg_wrap = ctk.CTkFrame(vid_row, fg_color="#070d18", corner_radius=8,
                                border_width=1, border_color="#141e35", height=36)
        seg_wrap.pack(side="left", fill="x", expand=True)
        seg_wrap.pack_propagate(False)

        for widget_col, (icon, label, val, pos) in enumerate([
            ("🔗", "Linkleri Kaydet",  "link",     "left"),
            ("⬇",  "yt-dlp ile İndir", "download", "mid"),
            ("⏭",  "Atla",            "skip",     "right"),
        ]):
            seg = _VideoSegment(seg_wrap, icon=icon, label=label, value=val,
                                var=self._video_mode, pos=pos, command=self._on_video_change)
            seg.place(relx=widget_col / 3, rely=0, relwidth=1/3, relheight=1)

        # Kalite satırı
        self._quality_frame = ctk.CTkFrame(self._video_section, fg_color="transparent")
        self._quality_frame.grid(row=2, column=0, sticky="w", pady=(8, 0))

        ctk.CTkLabel(self._quality_frame, text="Kalite", font=("Inter", 10, "bold"),
                     text_color=_OFF_TXT).pack(side="left", padx=(44, 10))
        for q in ("best", "1080", "720", "worst"):
            _QualityPill(self._quality_frame, q, self._video_quality).pack(side="left", padx=3)

        self._on_video_chip_change()

    def _on_type_change(self) -> None:
        self._rebuild_tree()
        self._update_summary()

    def _on_video_chip_change(self) -> None:
        """Video chip açık/kapalı → alt bölümü göster/gizle."""
        if self._video_enabled.get():
            self._video_section.grid()
        else:
            self._video_section.grid_remove()
        self._on_video_change()
        self._rebuild_tree()
        self._update_summary()

    def _on_video_change(self) -> None:
        if self._video_mode.get() == "download":
            self._quality_frame.grid()
        else:
            self._quality_frame.grid_remove()

    # ── Dosya Listesi ─────────────────────────────────────────

    def _build_tree_section(self, parent, row: int) -> None:
        outer = ctk.CTkFrame(parent, fg_color="#0d1120", corner_radius=12,
                             border_width=1, border_color="#141e35")
        outer.grid(row=row, column=0, sticky="ew", padx=18, pady=(14, 0))
        outer.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(outer, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=14, pady=(12, 6), sticky="w")
        ctk.CTkFrame(hdr, width=3, height=14, corner_radius=2, fg_color=ACCENT).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(hdr, text="🗂", font=("Inter", 11), text_color=ACCENT).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(hdr, text="DOSYALAR", font=("Inter", 10, "bold"), text_color="#3a5a78").pack(side="left")

        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 14))
        inner.grid_columnconfigure(0, weight=1)
        outer = inner

        # Dış scroll'a dahil — iç scroll yok, çakışma olmaz
        self._list_frame = ctk.CTkFrame(outer, fg_color="#080e1a", corner_radius=8)
        self._list_frame.grid(row=0, column=0, sticky="ew")
        self._list_frame.grid_columnconfigure(0, weight=1)

        # Satır widget'larını tutacak liste (rebuild için)
        self._list_rows: list[tk.Frame] = []

    def _rebuild_tree(self) -> None:
        """Listeyi mevcut filtre + kurs verisine göre yeniden oluşturur."""
        if not hasattr(self, "_list_frame"):
            return

        # Eski satırları temizle
        for w in self._list_frame.winfo_children():
            w.destroy()
        self._list_rows.clear()
        self._node_to_item.clear()

        active_types = self._active_types()
        row_idx = 0

        for course in self._courses.values():
            visible = sorted(
                [it for it in course.items.values() if it.type in active_types],
                key=lambda x: (x.path_hint, x.name),
            )
            if not visible:
                continue

            # Ders başlığı
            hdr = tk.Frame(self._list_frame, bg="#0a0f1e")
            hdr.grid(row=row_idx, column=0, sticky="ew", pady=(10 if row_idx > 0 else 4, 2))
            tk.Label(hdr, text=f"📚  {course.name}", bg="#0a0f1e",
                     fg="#e2eaf6", font=("Inter", 12, "bold"),
                     anchor="w", padx=12).pack(fill="x")
            row_idx += 1

            # Ayırıcı çizgi
            tk.Frame(self._list_frame, bg="#141e35", height=1).grid(
                row=row_idx, column=0, sticky="ew", padx=10, pady=(0, 4))
            row_idx += 1

            for item in visible:
                checked = self._item_checked.get(item.id, True)
                path_prefix = ""
                if item.path_hint:
                    parts = [p.strip() for p in item.path_hint.split("/") if p.strip()]
                    # Son segment dosya adıyla aynıysa gösterme (crawler tekrarı)
                    if parts and parts[-1] == item.name:
                        parts = parts[:-1]
                    if parts:
                        path_prefix = "  /  ".join(parts) + "  /  "

                row_frame = tk.Frame(self._list_frame, bg="#080e1a", cursor="hand2")
                row_frame.grid(row=row_idx, column=0, sticky="ew")
                row_frame.grid_columnconfigure(1, weight=1)

                # Checkbox
                chk_lbl = tk.Label(
                    row_frame,
                    text="☑" if checked else "☐",
                    bg="#080e1a",
                    fg=_ON_TXT if checked else _OFF_TXT,
                    font=("Inter", 13), cursor="hand2", width=3,
                )
                chk_lbl.grid(row=0, column=0, padx=(10, 4), pady=3)

                # İkon + yol + ad
                icon = _ITEM_ICON.get(item.type, "📁")
                name_lbl = tk.Label(
                    row_frame,
                    text=f"{icon}  {path_prefix}{item.name}",
                    bg="#080e1a",
                    fg="#7a9ab8" if checked else "#253040",
                    font=("Inter", 11), anchor="w", cursor="hand2",
                )
                name_lbl.grid(row=0, column=1, sticky="w", padx=(0, 8))

                # Boyut
                size_lbl = tk.Label(
                    row_frame,
                    text=self._fmt_size(item.size_bytes),
                    bg="#080e1a",
                    fg=_OFF_TXT if checked else "#1a2840",
                    font=("Inter", 10), anchor="e", cursor="hand2",
                )
                size_lbl.grid(row=0, column=2, padx=(0, 12), sticky="e")

                # Hover efekti
                def _enter(e, f=row_frame):
                    for w in f.winfo_children(): w.configure(bg="#0c1628")
                    f.configure(bg="#0c1628")
                def _leave(e, f=row_frame, c=checked):
                    bg = "#080e1a"
                    for w in f.winfo_children(): w.configure(bg=bg)
                    f.configure(bg=bg)

                # Tıklama
                iid = item.id
                def _click(e, item_id=iid, c_lbl=chk_lbl, n_lbl=name_lbl, s_lbl=size_lbl):
                    now = self._item_checked.get(item_id, True)
                    self._item_checked[item_id] = not now
                    new_checked = not now
                    c_lbl.configure(text="☑" if new_checked else "☐",
                                    fg=_ON_TXT if new_checked else _OFF_TXT)
                    n_lbl.configure(fg="#7a9ab8" if new_checked else "#253040")
                    s_lbl.configure(fg=_OFF_TXT if new_checked else "#1a2840")
                    self._update_summary()

                for w in (row_frame, chk_lbl, name_lbl, size_lbl):
                    w.bind("<Enter>", _enter)
                    w.bind("<Leave>", _leave)
                    w.bind("<Button-1>", _click)

                row_idx += 1

        self._update_summary()

    def _active_types(self) -> set[ItemType]:
        """Şu an seçili olan dosya türlerini döner."""
        active = set()
        for icon, label, item_type in _TYPE_CHIPS:
            var_key = _TYPE_TO_VAR.get(item_type, "other")
            if self._type_vars[var_key].get():
                active.add(item_type)
                if item_type == ItemType.OTHER:
                    active.add(ItemType.HTML)
        # Video chip + mod
        if self._video_enabled.get() and self._video_mode.get() != "skip":
            active.add(ItemType.VIDEO_SHAREPOINT)
            active.add(ItemType.VIDEO_OTHER)
        # Link chip
        if self._link.get():
            active.add(ItemType.LINK)
        return active

    # ── Chip'leri derslere göre dinamik güncelle ──────────────

    def _update_chips(self) -> None:
        """Seçili derslerde hangi türler var, olmayanları disabled yap."""
        existing_types: set[ItemType] = set()
        for course in self._courses.values():
            for item in course.items.values():
                existing_types.add(item.type)

        for icon, label, item_type in _TYPE_CHIPS:
            var_key = _TYPE_TO_VAR.get(item_type, "other")
            chip = self._chip_widgets.get(var_key)
            if chip:
                chip.set_disabled(False)

    # ── Özet ─────────────────────────────────────────────────

    def _update_summary(self) -> None:
        lbl = getattr(self, "_lbl_summary", None)
        if lbl is None or not lbl.winfo_exists():
            return
        active_types = self._active_types()
        excluded = {iid for iid, checked in self._item_checked.items() if not checked}
        count = sum(
            1 for c in self._courses.values()
            for it in c.items.values()
            if it.type in active_types and it.id not in excluded
        )
        size_b = sum(
            it.size_bytes or 0
            for c in self._courses.values()
            for it in c.items.values()
            if it.type in active_types and it.id not in excluded
        )
        parts = [f"✦ {count} dosya seçili"]
        if size_b:
            parts.append(f"~{size_b / 1_048_576:.0f} MB")
        lbl.configure(text="  ·  ".join(parts))

    # ── Yardımcılar ───────────────────────────────────────────

    @staticmethod
    def _fmt_size(size_bytes: Optional[int]) -> str:
        if not size_bytes:
            return ""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1_048_576:
            return f"{size_bytes / 1024:.0f} KB"
        return f"{size_bytes / 1_048_576:.1f} MB"

    def _reset(self) -> None:
        for var in self._type_vars.values():
            var.set(True)
        self._link.set(True)
        self._video_enabled.set(True)
        self._video_mode.set("link")
        self._video_quality.set("720")
        self._concurrent.set(2)
        self._item_checked.clear()
        self._on_video_chip_change()
        self._rebuild_tree()

    # ── Public API ────────────────────────────────────────────

    def set_courses(self, courses: dict[str, Course]) -> None:
        self._courses = courses
        self._all_items = {
            it.id: it
            for c in courses.values()
            for it in c.items.values()
        }
        self._update_chips()
        self._rebuild_tree()
        self._update_summary()

    def _build_filter(self) -> DownloadFilter:
        excluded = {iid for iid, checked in self._item_checked.items() if not checked}
        return DownloadFilter(
            include_pdf=self._pdf.get(),
            include_pptx=self._pptx.get(),
            include_docx=self._docx.get(),
            include_xlsx=self._xlsx.get(),
            include_images=self._img.get(),
            include_archives=self._arch.get(),
            include_scorm=False,
            include_code=self._code.get(),
            include_other=self._other.get(),
            include_links=self._link.get(),
            video_mode=self._video_mode.get() if self._video_enabled.get() else "skip",
            video_quality=self._video_quality.get(),
            concurrent=self._concurrent.get(),
            excluded_ids=excluded,
        )

    def _start(self) -> None:
        self._on_start(self._build_filter())
