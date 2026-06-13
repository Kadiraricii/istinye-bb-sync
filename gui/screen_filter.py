from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from core.models import Course, DownloadFilter, ItemType
from gui.theme import (
    ACCENT, ACCENT_BG, BG_BASE, BG_ELEVATED, BG_HOVER, BORDER,
    BTN_GHOST, BTN_PRIMARY,
    ENTRY, FONT_BODY, FONT_HEADING, FONT_SMALL,
    SUCCESS, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY,
)

_DEFAULT_DIR = Path.home() / "Downloads" / "Blackboard"


class _ToggleChip(ctk.CTkFrame):
    """Tıklanabilir toggle chip — dosya türü seçimi için."""

    def __init__(
        self, master, text: str, var: ctk.BooleanVar, command: Optional[Callable] = None,
    ) -> None:
        super().__init__(
            master, corner_radius=6, cursor="hand2",
            fg_color=BG_ELEVATED, border_width=1, border_color=BORDER,
            height=38,
        )
        self._var = var
        self._command = command
        self.grid_columnconfigure(0, weight=1)
        self.grid_propagate(False)

        self._lbl = ctk.CTkLabel(
            self, text=text, font=FONT_SMALL,
            text_color=TEXT_TERTIARY, cursor="hand2",
        )
        self._lbl.grid(row=0, column=0, padx=12, sticky="w")

        self.bind("<Button-1>", self._on_click)
        self._lbl.bind("<Button-1>", self._on_click)
        self._refresh()

    def _on_click(self, _=None) -> None:
        self._var.set(not self._var.get())
        self._refresh()
        if self._command:
            self._command()

    def _refresh(self) -> None:
        if self._var.get():
            self.configure(fg_color=ACCENT_BG, border_color=ACCENT)
            self._lbl.configure(text_color=SUCCESS)
        else:
            self.configure(fg_color=BG_ELEVATED, border_color=BORDER)
            self._lbl.configure(text_color=TEXT_TERTIARY)


class FilterScreen(ctk.CTkFrame):
    """
    İndirme ayarları ekranı — tek sayfa, bölümlü tasarım.
    """

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
        self._min_mb        = ctk.StringVar(value="")
        self._max_mb        = ctk.StringVar(value="")
        self._keyword       = ctk.StringVar(value="")
        self._concurrent    = ctk.IntVar(value=2)

        self._build()

    # ── Layout ────────────────────────────────────────────────

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_content()
        self._build_footer()

    def _build_header(self) -> None:
        hdr = ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0, height=56)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)
        hdr.grid_propagate(False)

        ctk.CTkButton(hdr, text="←  Geri", command=self._on_back, **BTN_GHOST).grid(
            row=0, column=0, padx=12, pady=12, sticky="w",
        )
        ctk.CTkLabel(
            hdr, text="İndirme Ayarları",
            font=FONT_HEADING, text_color=TEXT_PRIMARY,
        ).grid(row=0, column=1)
        ctk.CTkButton(hdr, text="Sıfırla", command=self._reset, **BTN_GHOST).grid(
            row=0, column=2, padx=12,
        )

    def _build_content(self) -> None:
        scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG_BASE,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=BG_HOVER,
        )
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        self._build_types_section(scroll, row=0)
        self._build_video_section(scroll, row=1)
        self._build_search_section(scroll, row=2)

        # Bottom padding
        ctk.CTkFrame(scroll, height=16, fg_color="transparent").grid(row=3, column=0)

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0, height=64)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        footer.grid_propagate(False)

        self._lbl_summary = ctk.CTkLabel(
            footer, text="", font=FONT_SMALL, text_color=TEXT_SECONDARY,
        )
        self._lbl_summary.grid(row=0, column=0, padx=20, sticky="w")

        conc_box = ctk.CTkFrame(footer, fg_color="transparent")
        conc_box.grid(row=0, column=1, padx=12)
        ctk.CTkLabel(
            conc_box, text="Eş zamanlı:", font=FONT_SMALL, text_color=TEXT_TERTIARY,
        ).pack(side="left", padx=(0, 8))
        for val in (1, 2, 5):
            ctk.CTkRadioButton(
                conc_box, text=str(val), variable=self._concurrent, value=val,
                font=FONT_SMALL, text_color=TEXT_SECONDARY,
                fg_color=ACCENT, border_color=BORDER,
            ).pack(side="left", padx=5)

        ctk.CTkButton(
            footer, text="İndirmeyi Başlat",
            command=self._start, **BTN_PRIMARY, width=160,
        ).grid(row=0, column=2, padx=16, pady=12)

    # ── Bölüm yardımcısı ─────────────────────────────────────

    def _card(self, parent, title: str, row: int) -> ctk.CTkFrame:
        outer = ctk.CTkFrame(
            parent, fg_color=BG_ELEVATED, corner_radius=10,
            border_width=1, border_color=BORDER,
        )
        outer.grid(row=row, column=0, sticky="ew", padx=20, pady=(12, 0))
        outer.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            outer, text=title, font=FONT_SMALL, text_color=TEXT_TERTIARY,
        ).grid(row=0, column=0, padx=16, pady=(12, 8), sticky="w")

        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 14))
        inner.grid_columnconfigure((0, 1), weight=1)
        return inner

    # ── Dosya Türleri ─────────────────────────────────────────

    def _build_types_section(self, parent, row: int) -> None:
        inner = self._card(parent, "DOSYA TÜRLERİ", row)
        chips = [
            ("PDF Dosyaları",    self._pdf),
            ("Sunumlar  (PPT)",  self._pptx),
            ("Belgeler  (DOC)",  self._docx),
            ("Tablolar  (XLS)",  self._xlsx),
            ("Resimler",         self._img),
            ("Arşivler",         self._arch),
            ("Diğer Dosyalar",   self._other),
            ("SCORM Paketleri",  self._scorm),
        ]
        for i, (label, var) in enumerate(chips):
            _ToggleChip(inner, label, var, command=self._update_summary).grid(
                row=i // 2, column=i % 2, padx=4, pady=4, sticky="ew",
            )

    # ── Video ─────────────────────────────────────────────────

    def _build_video_section(self, parent, row: int) -> None:
        inner = self._card(parent, "VİDEOLAR", row)

        modes = [
            ("link",     "Linkleri kaydet  (video_links.txt)"),
            ("download", "yt-dlp ile indir"),
            ("skip",     "Atla"),
        ]
        for i, (val, label) in enumerate(modes):
            ctk.CTkRadioButton(
                inner, text=label, variable=self._video_mode, value=val,
                font=FONT_BODY, text_color=TEXT_PRIMARY,
                fg_color=ACCENT, border_color=BORDER,
                command=self._on_video_change,
            ).grid(row=i, column=0, columnspan=2, sticky="w", padx=4, pady=5)

        self._quality_frame = ctk.CTkFrame(inner, fg_color=BG_BASE, corner_radius=6)
        self._quality_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=(6, 0))

        ctk.CTkLabel(
            self._quality_frame, text="Kalite:", font=FONT_SMALL, text_color=TEXT_TERTIARY,
        ).pack(side="left", padx=(12, 10))
        for q in ("best", "1080", "720", "worst"):
            ctk.CTkRadioButton(
                self._quality_frame, text=q, variable=self._video_quality, value=q,
                font=FONT_SMALL, text_color=TEXT_SECONDARY,
                fg_color=ACCENT, border_color=BORDER,
            ).pack(side="left", padx=8, pady=8)

        self._on_video_change()

    def _on_video_change(self) -> None:
        if self._video_mode.get() == "download":
            self._quality_frame.grid()
        else:
            self._quality_frame.grid_remove()
        self._update_summary()

    # ── Arama & Boyut ─────────────────────────────────────────

    def _build_search_section(self, parent, row: int) -> None:
        inner = self._card(parent, "ARAMA & BOYUT", row)

        ctk.CTkLabel(
            inner, text="Dosya adı filtresi", font=FONT_SMALL, text_color=TEXT_TERTIARY,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(0, 4))
        ctk.CTkEntry(
            inner, textvariable=self._keyword,
            placeholder_text="Örn: calculus   (boş bırakırsan hepsini indirir)",
            **ENTRY,
        ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=4)

        ctk.CTkFrame(inner, height=1, fg_color=BORDER).grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=12,
        )

        ctk.CTkLabel(
            inner, text="Boyut filtresi (MB)", font=FONT_SMALL, text_color=TEXT_TERTIARY,
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=4, pady=(0, 4))

        size_row = ctk.CTkFrame(inner, fg_color="transparent")
        size_row.grid(row=4, column=0, columnspan=2, sticky="w", padx=4)
        ctk.CTkLabel(size_row, text="Min:", font=FONT_SMALL, text_color=TEXT_TERTIARY).pack(side="left", padx=(0, 6))
        ctk.CTkEntry(size_row, textvariable=self._min_mb, width=80, **ENTRY).pack(side="left", padx=(0, 16))
        ctk.CTkLabel(size_row, text="Max:", font=FONT_SMALL, text_color=TEXT_TERTIARY).pack(side="left", padx=(0, 6))
        ctk.CTkEntry(size_row, textvariable=self._max_mb, width=80, **ENTRY).pack(side="left")

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
        self._on_video_change()
        self._update_summary()

    def _update_summary(self) -> None:
        dl_filter = self._build_filter()
        file_count = sum(
            1 for c in self._courses.values()
            for it in c.items.values()
            if dl_filter.allows_item(it)
        )
        size_b = sum(
            it.size_bytes or 0
            for c in self._courses.values()
            for it in c.items.values()
            if dl_filter.allows_item(it)
        )
        link_count = sum(
            1 for c in self._courses.values()
            for it in c.items.values()
            if it.type == ItemType.LINK
        )
        parts = [f"{file_count} dosya"]
        if size_b:
            parts.append(f"~{size_b / 1_048_576:.0f} MB")
        if link_count:
            parts.append(f"{link_count} link kaydedilecek")
        self._lbl_summary.configure(text="  ·  ".join(parts))

    def _build_filter(self) -> DownloadFilter:
        def _f(v: ctk.StringVar) -> Optional[float]:
            try:
                return float(v.get()) or None
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
            min_size_mb=_f(self._min_mb),
            max_size_mb=_f(self._max_mb),
            keyword=self._keyword.get().strip() or None,
            concurrent=self._concurrent.get(),
        )

    def _start(self) -> None:
        self._on_start(self._build_filter())

    def set_courses(self, courses: dict[str, Course]) -> None:
        self._courses = courses
        self._update_summary()
