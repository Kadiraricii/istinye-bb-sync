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

_MAX_LOG = 300


class ProgressScreen(ctk.CTkFrame):
    """
    İndirme ilerleme ekranı.

    Kompakt mod: pencere 48 px'e küçülür.
    Always-on-top toggle desteklenir.
    """

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

        self._paused    = False
        self._compact   = False
        self._on_top    = True   # App her zaman üstte başlatır
        self._done      = 0
        self._total     = 0
        self._start_ts  = time.time()
        self._log_lines: list[tuple[str, str]] = []  # (text, color)

        self._build()

    # ── Layout ────────────────────────────────────────────────

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # ── Header ──────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0, height=56)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)
        hdr.grid_propagate(False)

        self._lbl_counter = ctk.CTkLabel(
            hdr, text="0/0 dosya",
            font=FONT_HEADING, text_color=TEXT_PRIMARY,
        )
        self._lbl_counter.grid(row=0, column=1, padx=12)

        btn_box = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_box.grid(row=0, column=2, padx=8)

        self._btn_top = ctk.CTkButton(btn_box, text="📌 Sabitlendi", command=self._toggle_top, **BTN_GHOST)
        self._btn_top.pack(side="left", padx=2)

        self._btn_compact = ctk.CTkButton(btn_box, text="⬛ Kompakt", command=self._toggle_compact, **BTN_GHOST)
        self._btn_compact.pack(side="left", padx=2)

        self._btn_pause = ctk.CTkButton(btn_box, text="⏸ Duraklat", command=self._pause_resume, **BTN_GHOST)
        self._btn_pause.pack(side="left", padx=2)

        ctk.CTkButton(btn_box, text="✕ İptal", command=self._confirm_cancel,
                      fg_color="transparent", hover_color="#450a0a",
                      text_color=ERROR, corner_radius=6, font=FONT_SMALL, height=32,
                      ).pack(side="left", padx=2)

        # ── Genel progress ───────────────────────
        prog_frame = ctk.CTkFrame(self, fg_color=BG_BASE)
        prog_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(14, 0))
        prog_frame.grid_columnconfigure(0, weight=1)

        self._progress_bar = ctk.CTkProgressBar(
            prog_frame,
            progress_color=ACCENT,
            fg_color=BG_ELEVATED,
            height=8,
            corner_radius=4,
        )
        self._progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self._progress_bar.set(0)

        info_row = ctk.CTkFrame(prog_frame, fg_color="transparent")
        info_row.grid(row=1, column=0, sticky="ew")
        info_row.grid_columnconfigure(0, weight=1)

        self._lbl_current_file = ctk.CTkLabel(
            info_row, text="Başlatılıyor...",
            font=FONT_SMALL, text_color=TEXT_SECONDARY, anchor="w",
        )
        self._lbl_current_file.grid(row=0, column=0, sticky="w")

        self._lbl_eta = ctk.CTkLabel(
            info_row, text="",
            font=FONT_SMALL, text_color=TEXT_TERTIARY,
        )
        self._lbl_eta.grid(row=0, column=1, sticky="e")

        # ── Kurs listesi + log ────────────────────
        panes = ctk.CTkFrame(self, fg_color=BG_BASE)
        panes.grid(row=3, column=0, sticky="nsew", padx=20, pady=12)
        panes.grid_columnconfigure(0, weight=1)
        panes.grid_columnconfigure(1, weight=2)
        panes.grid_rowconfigure(0, weight=1)

        # Kurs listesi
        course_frame = ctk.CTkFrame(panes, fg_color=BG_ELEVATED, corner_radius=8)
        course_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        course_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(course_frame, text="Kurslar", font=FONT_SMALL, text_color=TEXT_TERTIARY).grid(
            row=0, column=0, padx=12, pady=(8, 4), sticky="w",
        )
        self._course_scroll = ctk.CTkScrollableFrame(
            course_frame, fg_color="transparent",
        )
        self._course_scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
        self._course_scroll.grid_columnconfigure(0, weight=1)
        self._course_labels: dict[str, ctk.CTkLabel] = {}

        # Log
        log_frame = ctk.CTkFrame(panes, fg_color=BG_ELEVATED, corner_radius=8)
        log_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        log_frame.grid_rowconfigure(1, weight=1)

        log_hdr = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 4))
        log_hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(log_hdr, text="Günlük", font=FONT_SMALL, text_color=TEXT_TERTIARY).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(log_hdr, text="Temizle", command=self._clear_log, **BTN_GHOST).grid(row=0, column=1)

        self._log_box = ctk.CTkTextbox(
            log_frame,
            font=FONT_MONO,
            fg_color="transparent",
            text_color=TEXT_SECONDARY,
            state="disabled",
            wrap="none",
        )
        self._log_box.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))

        # ── Kompakt mod (gizli, toggle ile gösterilir) ──
        self._compact_bar = ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0, height=48)
        self._compact_bar.grid_columnconfigure(1, weight=1)
        # başlangıçta gizli

    # ── Public API ────────────────────────────────────────────

    def set_courses(self, courses: dict[str, Course]) -> None:
        for cid, course in courses.items():
            lbl = ctk.CTkLabel(
                self._course_scroll,
                text=f"○  {course.name}",
                font=FONT_SMALL,
                text_color=TEXT_TERTIARY,
                anchor="w",
            )
            lbl.grid(sticky="w", padx=8, pady=2)
            self._course_labels[cid] = lbl
        total = sum(len(c.items) for c in courses.values())
        self._total = total
        self._lbl_counter.configure(text=f"0/{total} dosya")

    def update_course_status(self, course_id: str, status: str) -> None:
        """status: 'active' | 'done' | 'pending'"""
        lbl = self._course_labels.get(course_id)
        if not lbl:
            return
        if status == "active":
            lbl.configure(text=f"·  {lbl.cget('text')[3:]}", text_color=WARNING)
        elif status == "done":
            lbl.configure(text=f"✓  {lbl.cget('text')[3:]}", text_color=SUCCESS)

    def update_progress(self, course_name: str, done: int, total: int) -> None:
        self._done += 1
        fraction = self._done / self._total if self._total else 0
        self._progress_bar.set(fraction)
        self._lbl_counter.configure(text=f"{self._done}/{self._total} dosya")

        elapsed = time.time() - self._start_ts
        if fraction > 0.01:
            eta = elapsed / fraction * (1 - fraction)
            self._lbl_eta.configure(text=f"~{int(eta // 60)}d {int(eta % 60)}s")

    def on_file_done(self, item: Item, success: bool) -> None:
        color  = SUCCESS if success else ERROR
        prefix = "✓" if success else "✗"
        self.add_log(f"{prefix} {item.name}", color)
        self._lbl_current_file.configure(text=item.name)

    def add_log(self, message: str, color: str = TEXT_SECONDARY) -> None:
        self._log_lines.append((message, color))
        if len(self._log_lines) > _MAX_LOG:
            self._log_lines.pop(0)

        self._log_box.configure(state="normal")
        self._log_box.insert("end", message + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def show_summary(self, downloaded: int, failed: int, skipped: int) -> None:
        total_mb = 0
        msg = (
            f"İndirme tamamlandı!\n\n"
            f"✓ {downloaded} dosya indirildi\n"
            f"✗ {failed} hata\n"
            f"↷ {skipped} atlandı"
        )
        popup = ctk.CTkToplevel(self._master)
        popup.title("Tamamlandı")
        popup.geometry("320x200")
        popup.grab_set()
        ctk.CTkLabel(popup, text=msg, font=FONT_BODY, text_color=TEXT_PRIMARY, justify="left").pack(padx=24, pady=24)
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
        ctk.CTkLabel(
            popup, text="İndirmeyi iptal et?",
            font=FONT_BODY, text_color=TEXT_PRIMARY,
        ).pack(padx=24, pady=(20, 12))
        btn_row = ctk.CTkFrame(popup, fg_color="transparent")
        btn_row.pack()
        ctk.CTkButton(btn_row, text="Evet, iptal et",
                      command=lambda: [popup.destroy(), self._on_cancel()],
                      fg_color="#7f1d1d", hover_color="#450a0a",
                      text_color="#fca5a5", corner_radius=6,
                      font=FONT_SMALL, height=36, width=140,
                      ).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="Devam et",
                      command=popup.destroy, **BTN_SECONDARY,
                      ).pack(side="left", padx=6)

    def _toggle_top(self) -> None:
        self._on_top = not self._on_top
        self._master.attributes("-topmost", self._on_top)
        self._btn_top.configure(text="📌 Sabitlendi" if self._on_top else "📌 Sabitle")

    def _toggle_compact(self) -> None:
        self._compact = not self._compact
        from core.config import COMPACT_HEIGHT, WINDOW_HEIGHT, WINDOW_WIDTH
        if self._compact:
            self._master.geometry(f"{WINDOW_WIDTH}x{COMPACT_HEIGHT}")
            self.grid_remove()
            self._compact_bar.grid(row=0, column=0, sticky="ew")
            self._compact_bar.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(
                self._compact_bar,
                textvariable=ctk.StringVar(value=self._lbl_current_file.cget("text")),
                font=FONT_SMALL, text_color=TEXT_SECONDARY,
            ).grid(row=0, column=1, padx=8)
            ctk.CTkButton(
                self._compact_bar, text="↑", command=self._toggle_compact, **BTN_GHOST,
            ).grid(row=0, column=2, padx=8)
        else:
            self._compact_bar.grid_remove()
            self.grid()
            self._master.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

    def _clear_log(self) -> None:
        self._log_lines.clear()
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")
