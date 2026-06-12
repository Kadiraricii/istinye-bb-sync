from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from core.models import Course, DownloadFilter
from gui.theme import (
    ACCENT, BG_BASE, BG_ELEVATED, BG_HOVER, BORDER,
    BTN_GHOST, BTN_PRIMARY, BTN_SECONDARY,
    ENTRY, FONT_BODY, FONT_HEADING, FONT_SMALL,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY,
)


class FilterScreen(ctk.CTkFrame):
    """
    Filtre ekranı — 3 sekme: Dosya Türleri / Boyut & Tarih / Video.
    on_start(filter) çağrıldığında indirme başlar.
    """

    def __init__(
        self,
        master: ctk.CTk,
        on_start:  Callable[[DownloadFilter], None],
        on_back:   Callable,
    ) -> None:
        super().__init__(master, fg_color=BG_BASE, corner_radius=0)
        self._on_start = on_start
        self._on_back  = on_back
        self._courses: dict[str, Course] = {}

        # State vars
        self._pdf   = ctk.BooleanVar(value=True)
        self._pptx  = ctk.BooleanVar(value=True)
        self._docx  = ctk.BooleanVar(value=True)
        self._xlsx  = ctk.BooleanVar(value=True)
        self._img   = ctk.BooleanVar(value=True)
        self._arch  = ctk.BooleanVar(value=True)
        self._other = ctk.BooleanVar(value=True)
        self._scorm = ctk.BooleanVar(value=False)

        self._video_mode    = ctk.StringVar(value="link")
        self._video_quality = ctk.StringVar(value="720")
        self._min_mb  = ctk.StringVar(value="")
        self._max_mb  = ctk.StringVar(value="")
        self._keyword = ctk.StringVar(value="")
        self._concurrent = ctk.IntVar(value=2)

        self._active_tab = 0
        self._build()

    # ── Layout ────────────────────────────────────────────────

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        hdr = ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0, height=56)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)
        hdr.grid_propagate(False)

        ctk.CTkButton(hdr, text="← Geri", command=self._on_back, **BTN_GHOST).grid(
            row=0, column=0, padx=12, pady=8,
        )
        ctk.CTkLabel(
            hdr, text="İndirme Filtreleri",
            font=FONT_HEADING, text_color=TEXT_PRIMARY,
        ).grid(row=0, column=1, padx=8)

        ctk.CTkButton(hdr, text="Sıfırla", command=self._reset, **BTN_GHOST).grid(
            row=0, column=2, padx=12,
        )

        # Sekme başlıkları
        self._tab_bar = ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0, height=40)
        self._tab_bar.grid(row=1, column=0, sticky="ew")
        self._tab_bar.grid_propagate(False)

        self._tab_btns: list[ctk.CTkButton] = []
        tab_labels = ["Dosya Türleri", "Boyut & Tarih", "Video"]
        for i, label in enumerate(tab_labels):
            btn = ctk.CTkButton(
                self._tab_bar, text=label,
                command=lambda idx=i: self._switch_tab(idx),
                fg_color="transparent",
                hover_color=BG_HOVER,
                text_color=TEXT_SECONDARY,
                corner_radius=0,
                font=FONT_SMALL,
                height=40, width=140,
            )
            btn.pack(side="left")
            self._tab_btns.append(btn)

        # Sekme içerik alanı
        self._content_frame = ctk.CTkFrame(self, fg_color=BG_BASE)
        self._content_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=12)
        self._content_frame.grid_columnconfigure(0, weight=1)

        # Alt bar
        footer = ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0, height=60)
        footer.grid(row=3, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_propagate(False)

        self._lbl_summary = ctk.CTkLabel(
            footer, text="",
            font=FONT_SMALL, text_color=TEXT_SECONDARY,
        )
        self._lbl_summary.grid(row=0, column=0, padx=16, sticky="w")

        # Bant genişliği
        bw_box = ctk.CTkFrame(footer, fg_color="transparent")
        bw_box.grid(row=0, column=1, padx=16)
        ctk.CTkLabel(bw_box, text="Eş zamanlı:", font=FONT_SMALL, text_color=TEXT_TERTIARY).pack(side="left", padx=(0, 6))
        for val in (1, 2, 5):
            ctk.CTkRadioButton(
                bw_box, text=str(val), variable=self._concurrent, value=val,
                font=FONT_SMALL, text_color=TEXT_SECONDARY,
                fg_color=ACCENT, border_color=BORDER,
            ).pack(side="left", padx=4)

        ctk.CTkButton(
            footer, text="İndirmeyi Başlat", command=self._start,
            **BTN_PRIMARY,
        ).grid(row=0, column=2, padx=12, pady=10)

        self._switch_tab(0)

    # ── Sekme İçerikleri ──────────────────────────────────────

    def _switch_tab(self, idx: int) -> None:
        self._active_tab = idx
        for i, btn in enumerate(self._tab_btns):
            btn.configure(text_color=TEXT_PRIMARY if i == idx else TEXT_SECONDARY)

        for w in self._content_frame.winfo_children():
            w.destroy()

        builders = [self._build_types_tab, self._build_size_tab, self._build_video_tab]
        builders[idx]()
        self._update_summary()

    def _build_types_tab(self) -> None:
        f = self._content_frame
        ctk.CTkLabel(f, text="Hangi dosya türlerini indir?",
                     font=FONT_BODY, text_color=TEXT_SECONDARY).grid(
            row=0, column=0, sticky="w", pady=(0, 12),
        )
        types = [
            ("PDF dosyaları (.pdf)", self._pdf),
            ("Sunumlar (.pptx, .ppt)", self._pptx),
            ("Belgeler (.docx, .doc)", self._docx),
            ("Tablolar (.xlsx, .xls)", self._xlsx),
            ("Resimler (.jpg, .png, ...)", self._img),
            ("Arşivler (.zip, .rar, ...)", self._arch),
            ("Diğer dosyalar", self._other),
            ("SCORM paketleri", self._scorm),
        ]
        for i, (label, var) in enumerate(types):
            ctk.CTkCheckBox(
                f, text=label, variable=var,
                font=FONT_BODY, text_color=TEXT_PRIMARY,
                fg_color=ACCENT, border_color=BORDER,
                command=self._update_summary,
            ).grid(row=i + 1, column=0, sticky="w", pady=4)

    def _build_size_tab(self) -> None:
        f = self._content_frame
        row = 0

        ctk.CTkLabel(f, text="Boyut filtresi (MB)", font=FONT_BODY, text_color=TEXT_SECONDARY).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(0, 8),
        ); row += 1

        size_row = ctk.CTkFrame(f, fg_color="transparent")
        size_row.grid(row=row, column=0, sticky="w"); row += 1
        ctk.CTkLabel(size_row, text="Min:", font=FONT_SMALL, text_color=TEXT_TERTIARY).pack(side="left", padx=(0, 4))
        ctk.CTkEntry(size_row, textvariable=self._min_mb, width=80, **ENTRY).pack(side="left", padx=(0, 16))
        ctk.CTkLabel(size_row, text="Max:", font=FONT_SMALL, text_color=TEXT_TERTIARY).pack(side="left", padx=(0, 4))
        ctk.CTkEntry(size_row, textvariable=self._max_mb, width=80, **ENTRY).pack(side="left")

        ctk.CTkFrame(f, height=1, fg_color=BORDER).grid(row=row, column=0, sticky="ew", pady=16); row += 1

        ctk.CTkLabel(f, text="Anahtar kelime", font=FONT_BODY, text_color=TEXT_SECONDARY).grid(
            row=row, column=0, sticky="w", pady=(0, 4),
        ); row += 1
        ctk.CTkEntry(
            f, textvariable=self._keyword,
            placeholder_text="Dosya adında ara...",
            **ENTRY,
        ).grid(row=row, column=0, sticky="ew", pady=(0, 4)); row += 1

    def _build_video_tab(self) -> None:
        f = self._content_frame
        row = 0

        ctk.CTkLabel(f, text="Videolar için:", font=FONT_BODY, text_color=TEXT_SECONDARY).grid(
            row=row, column=0, sticky="w", pady=(0, 8),
        ); row += 1

        modes = [
            ("link",     "Link olarak kaydet (video_links.txt)"),
            ("download", "yt-dlp ile indir"),
            ("skip",     "Atla"),
        ]
        for val, label in modes:
            ctk.CTkRadioButton(
                f, text=label, variable=self._video_mode, value=val,
                font=FONT_BODY, text_color=TEXT_PRIMARY,
                fg_color=ACCENT, border_color=BORDER,
                command=self._update_summary,
            ).grid(row=row, column=0, sticky="w", pady=4); row += 1

        ctk.CTkFrame(f, height=1, fg_color=BORDER).grid(row=row, column=0, sticky="ew", pady=12); row += 1

        ctk.CTkLabel(f, text="Video kalitesi (yt-dlp)", font=FONT_BODY, text_color=TEXT_SECONDARY).grid(
            row=row, column=0, sticky="w", pady=(0, 8),
        ); row += 1

        q_box = ctk.CTkFrame(f, fg_color="transparent")
        q_box.grid(row=row, column=0, sticky="w"); row += 1
        for q in ("best", "1080", "720", "worst"):
            ctk.CTkRadioButton(
                q_box, text=q, variable=self._video_quality, value=q,
                font=FONT_SMALL, text_color=TEXT_SECONDARY,
                fg_color=ACCENT, border_color=BORDER,
            ).pack(side="left", padx=8)

    # ── Sıfırla / Özet / Başlat ───────────────────────────────

    def _reset(self) -> None:
        for var in (self._pdf, self._pptx, self._docx, self._xlsx,
                    self._img, self._arch, self._other):
            var.set(True)
        self._scorm.set(False)
        self._video_mode.set("link")
        self._video_quality.set("720")
        self._min_mb.set("")
        self._max_mb.set("")
        self._keyword.set("")
        self._concurrent.set(2)
        self._switch_tab(self._active_tab)

    def _update_summary(self) -> None:
        dl_filter = self._build_filter()
        total = sum(
            1 for c in self._courses.values()
            for item in c.items.values()
            if dl_filter.allows_item(item)
        )
        size_b = sum(
            item.size_bytes or 0
            for c in self._courses.values()
            for item in c.items.values()
            if dl_filter.allows_item(item)
        )
        size_str = f" · ~{size_b / 1_048_576:.0f} MB" if size_b else ""
        self._lbl_summary.configure(text=f"{total} öğe indirilecek{size_str}")

    def _build_filter(self) -> DownloadFilter:
        def _safe_float(var: ctk.StringVar):
            try:
                return float(var.get()) or None
            except ValueError:
                return None

        return DownloadFilter(
            include_pdf=self._pdf.get(),
            include_pptx=self._pptx.get(),
            include_docx=self._docx.get(),
            include_xlsx=self._xlsx.get(),
            include_images=self._img.get(),
            include_archives=self._arch.get(),
            include_other=self._other.get(),
            include_scorm=self._scorm.get(),
            video_mode=self._video_mode.get(),
            video_quality=self._video_quality.get(),
            min_size_mb=_safe_float(self._min_mb),
            max_size_mb=_safe_float(self._max_mb),
            keyword=self._keyword.get().strip() or None,
            concurrent=self._concurrent.get(),
        )

    def _start(self) -> None:
        self._on_start(self._build_filter())

    def set_courses(self, courses: dict[str, Course]) -> None:
        self._courses = courses
        self._update_summary()
