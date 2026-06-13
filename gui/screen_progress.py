from __future__ import annotations

import time
from typing import Callable, Optional

import customtkinter as ctk

from core.models import Course, Item
from gui.theme import (
    ACCENT, BG_BASE, BG_ELEVATED, BG_HOVER, BORDER,
    BTN_GHOST, BTN_PRIMARY, BTN_SECONDARY,
    ERROR, FONT_BODY, FONT_HEADING, FONT_MONO, FONT_SMALL,
    SUCCESS, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY, WARNING,
)

_MAX_LOG = 400


class ProgressScreen(ctk.CTkFrame):
    """İndirme ilerleme ekranı."""

    def __init__(
        self,
        master: ctk.CTk,
        on_pause:  Callable,
        on_resume: Callable,
        on_cancel: Callable,
    ) -> None:
        super().__init__(master, fg_color=BG_BASE, corner_radius=0)
        self._master    = master
        self._on_pause  = on_pause
        self._on_resume = on_resume
        self._on_cancel = on_cancel

        self._paused   = False
        self._compact  = False
        self._on_top   = True
        self._done     = 0
        self._total    = 0
        self._start_ts = time.time()
        self._bytes_done = 0
        self._log_count  = 0

        # course_id → label widget
        self._course_labels: dict[str, ctk.CTkLabel] = {}

        self._build()

    # ── Layout ────────────────────────────────────────────────

    def _build(self) -> None:
        self.pack_propagate(False)

        # Compact bar — hidden initially, swapped in for compact mode
        self._compact_bar = ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0, height=48)
        self._compact_bar.grid_columnconfigure(1, weight=1)

        self._cbar_lbl = ctk.CTkLabel(
            self._compact_bar, text="İndiriliyor...",
            font=FONT_SMALL, text_color=TEXT_SECONDARY,
        )
        self._cbar_lbl.grid(row=0, column=1, padx=12, sticky="w")

        self._cbar_prog = ctk.CTkProgressBar(
            self._compact_bar, progress_color=ACCENT,
            fg_color=BORDER, height=3, corner_radius=0,
        )
        self._cbar_prog.grid(row=1, column=0, columnspan=3, sticky="ew")
        self._cbar_prog.set(0)

        ctk.CTkButton(
            self._compact_bar, text="↑ Genişlet", command=self._toggle_compact, **BTN_GHOST,
        ).grid(row=0, column=2, padx=8)

        # Main body
        self._body = ctk.CTkFrame(self, fg_color=BG_BASE, corner_radius=0)
        self._body.pack(fill="both", expand=True)
        self._body.grid_columnconfigure(0, weight=1)
        self._body.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_progress()
        self._build_panes()

    def _build_header(self) -> None:
        hdr = ctk.CTkFrame(self._body, fg_color=BG_ELEVATED, corner_radius=0, height=56)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)
        hdr.grid_propagate(False)

        self._lbl_counter = ctk.CTkLabel(
            hdr, text="0 / 0 dosya",
            font=FONT_HEADING, text_color=TEXT_PRIMARY,
        )
        self._lbl_counter.grid(row=0, column=1, padx=12)

        btns = ctk.CTkFrame(hdr, fg_color="transparent")
        btns.grid(row=0, column=2, padx=8)

        self._btn_pin = ctk.CTkButton(btns, text="📌 Sabit", command=self._toggle_top, **BTN_GHOST)
        self._btn_pin.pack(side="left", padx=2)

        self._btn_compact = ctk.CTkButton(btns, text="⬛ Küçült", command=self._toggle_compact, **BTN_GHOST)
        self._btn_compact.pack(side="left", padx=2)

        self._btn_pause = ctk.CTkButton(btns, text="⏸ Duraklat", command=self._pause_resume, **BTN_GHOST)
        self._btn_pause.pack(side="left", padx=2)

        ctk.CTkButton(
            btns, text="✕ İptal", command=self._confirm_cancel,
            fg_color="transparent", hover_color="#450a0a",
            text_color=ERROR, corner_radius=6, font=FONT_SMALL, height=32,
        ).pack(side="left", padx=2)

    def _build_progress(self) -> None:
        prog_area = ctk.CTkFrame(self._body, fg_color=BG_BASE)
        prog_area.grid(row=1, column=0, sticky="ew", padx=20, pady=(14, 0))
        prog_area.grid_columnconfigure(0, weight=1)

        self._progress_bar = ctk.CTkProgressBar(
            prog_area, progress_color=ACCENT,
            fg_color=BG_ELEVATED, height=8, corner_radius=4,
        )
        self._progress_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self._progress_bar.set(0)

        self._lbl_current = ctk.CTkLabel(
            prog_area, text="Başlatılıyor...",
            font=FONT_SMALL, text_color=TEXT_SECONDARY, anchor="w",
        )
        self._lbl_current.grid(row=1, column=0, sticky="w")

        self._lbl_eta = ctk.CTkLabel(
            prog_area, text="",
            font=FONT_SMALL, text_color=TEXT_TERTIARY, anchor="e",
        )
        self._lbl_eta.grid(row=1, column=1, sticky="e")

    def _build_panes(self) -> None:
        panes = ctk.CTkFrame(self._body, fg_color=BG_BASE)
        panes.grid(row=2, column=0, sticky="nsew", padx=20, pady=12)
        panes.grid_columnconfigure(1, weight=1)
        panes.grid_rowconfigure(0, weight=1)

        # Left: course list
        course_card = ctk.CTkFrame(panes, fg_color=BG_ELEVATED, corner_radius=8,
                                   border_width=1, border_color=BORDER)
        course_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        course_card.grid_rowconfigure(1, weight=1)
        course_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            course_card, text="Kurslar",
            font=FONT_SMALL, text_color=TEXT_TERTIARY,
        ).grid(row=0, column=0, padx=12, pady=(10, 6), sticky="w")

        self._course_scroll = ctk.CTkScrollableFrame(
            course_card, fg_color="transparent", width=190,
        )
        self._course_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
        self._course_scroll.grid_columnconfigure(0, weight=1)

        # Right: log
        log_card = ctk.CTkFrame(panes, fg_color=BG_ELEVATED, corner_radius=8,
                                border_width=1, border_color=BORDER)
        log_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        log_card.grid_rowconfigure(1, weight=1)
        log_card.grid_columnconfigure(0, weight=1)

        log_hdr = ctk.CTkFrame(log_card, fg_color="transparent")
        log_hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        log_hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(log_hdr, text="Günlük", font=FONT_SMALL, text_color=TEXT_TERTIARY).grid(
            row=0, column=0, sticky="w",
        )
        ctk.CTkButton(log_hdr, text="Temizle", command=self._clear_log, **BTN_GHOST).grid(
            row=0, column=1,
        )

        self._log_box = ctk.CTkTextbox(
            log_card, font=FONT_MONO,
            fg_color="transparent", text_color=TEXT_SECONDARY,
            state="disabled", wrap="none",
        )
        self._log_box.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))

    # ── Public API ────────────────────────────────────────────

    def set_courses(self, courses: dict[str, Course]) -> None:
        for cid, course in courses.items():
            lbl = ctk.CTkLabel(
                self._course_scroll,
                text=f"○  {course.name[:30]}",
                font=FONT_SMALL, text_color=TEXT_TERTIARY, anchor="w",
            )
            lbl.grid(sticky="ew", padx=8, pady=2)
            self._course_labels[cid] = lbl
        self._total = sum(len(c.items) for c in courses.values())
        self._lbl_counter.configure(text=f"0 / {self._total} dosya")

    def update_course_status(self, course_id: str, status: str) -> None:
        lbl = self._course_labels.get(course_id)
        if not lbl:
            return
        name = lbl.cget("text")[3:]
        if status == "active":
            lbl.configure(text=f"●  {name}", text_color=ACCENT)
        elif status == "done":
            lbl.configure(text=f"✓  {name}", text_color=SUCCESS)

    def update_progress(self, course_name: str, done: int, total: int) -> None:
        self._done += 1
        fraction = self._done / self._total if self._total else 0
        self._progress_bar.set(fraction)
        self._cbar_prog.set(fraction)
        self._lbl_counter.configure(text=f"{self._done} / {self._total} dosya")

        elapsed = time.time() - self._start_ts
        if fraction > 0.02 and elapsed > 1:
            eta_s = int(elapsed / fraction * (1 - fraction))
            eta_str = f"~{eta_s // 60}d {eta_s % 60}s kaldı"
            self._lbl_eta.configure(text=eta_str)

    def on_file_done(self, item: Item, success: bool) -> None:
        color  = SUCCESS if success else ERROR
        prefix = "✓" if success else "✗"
        self.add_log(f"{prefix} {item.name}", color)
        self._lbl_current.configure(text=item.name)
        self._cbar_lbl.configure(text=item.name[:50])

    def add_log(self, message: str, color: str = "") -> None:
        self._log_count += 1
        self._log_box.configure(state="normal")
        if self._log_count > _MAX_LOG:
            self._log_box.delete("1.0", "2.0")
        self._log_box.insert("end", message + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def show_summary(self, downloaded: int, failed: int, skipped: int) -> None:
        msg = (
            f"İndirme tamamlandı!\n\n"
            f"✓  {downloaded} dosya indirildi\n"
            f"✗  {failed} hata\n"
            f"↷  {skipped} atlandı"
        )
        popup = ctk.CTkToplevel(self._master)
        popup.title("Tamamlandı")
        popup.geometry("320x220")
        popup.grab_set()
        popup.attributes("-topmost", True)
        ctk.CTkLabel(
            popup, text=msg, font=FONT_BODY, text_color=TEXT_PRIMARY, justify="left",
        ).pack(padx=28, pady=24, anchor="w")
        ctk.CTkButton(popup, text="Kapat", command=popup.destroy, **BTN_PRIMARY).pack(pady=(0, 16))

    # ── Kontroller ────────────────────────────────────────────

    def _pause_resume(self) -> None:
        self._paused = not self._paused
        if self._paused:
            self._btn_pause.configure(text="▶ Devam")
            self._on_pause()
            self.add_log("⏸ Duraklatıldı", WARNING)
        else:
            self._btn_pause.configure(text="⏸ Duraklat")
            self._on_resume()
            self.add_log("▶ Devam edildi", SUCCESS)

    def _confirm_cancel(self) -> None:
        popup = ctk.CTkToplevel(self._master)
        popup.title("İptal")
        popup.geometry("300x140")
        popup.grab_set()
        popup.attributes("-topmost", True)
        ctk.CTkLabel(
            popup, text="İndirmeyi iptal et?",
            font=FONT_BODY, text_color=TEXT_PRIMARY,
        ).pack(padx=24, pady=(20, 12))
        row = ctk.CTkFrame(popup, fg_color="transparent")
        row.pack()
        ctk.CTkButton(
            row, text="Evet, iptal et",
            command=lambda: [popup.destroy(), self._on_cancel()],
            fg_color="#7f1d1d", hover_color="#450a0a",
            text_color="#fca5a5", corner_radius=6,
            font=FONT_SMALL, height=36, width=140,
        ).pack(side="left", padx=6)
        ctk.CTkButton(row, text="Devam et", command=popup.destroy, **BTN_SECONDARY).pack(side="left", padx=6)

    def _toggle_top(self) -> None:
        self._on_top = not self._on_top
        self._master.attributes("-topmost", self._on_top)
        self._btn_pin.configure(text="📌 Sabit" if self._on_top else "📌 Sabitle")

    def _toggle_compact(self) -> None:
        from core.config import COMPACT_HEIGHT, WINDOW_HEIGHT, WINDOW_WIDTH
        self._compact = not self._compact
        if self._compact:
            self._body.pack_forget()
            self._compact_bar.pack(fill="x")
            self._master.geometry(f"{WINDOW_WIDTH}x{COMPACT_HEIGHT}")
        else:
            self._compact_bar.pack_forget()
            self._body.pack(fill="both", expand=True)
            self._master.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

    def _clear_log(self) -> None:
        self._log_count = 0
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")
