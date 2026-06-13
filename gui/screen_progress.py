from __future__ import annotations

import time
import tkinter as tk
from typing import Callable, Optional

import customtkinter as ctk

from core.models import Course, Item
from gui.theme import (
    ACCENT, ACCENT_BG, BG_BASE, BG_ELEVATED, BG_HOVER, BORDER, BORDER_FAINT,
    BTN_GHOST, BTN_PRIMARY, BTN_SECONDARY,
    ERROR, FONT_BODY, FONT_HEADING, FONT_HERO, FONT_MONO, FONT_SMALL,
    SUCCESS, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY, WARNING,
)

_MAX_LOG = 800


class ProgressScreen(ctk.CTkFrame):

    def __init__(
        self,
        master:    ctk.CTk,
        on_pause:  Callable,
        on_resume: Callable,
        on_cancel: Callable,
        on_finish: Optional[Callable] = None,
    ) -> None:
        super().__init__(master, fg_color=BG_BASE, corner_radius=0)
        self._master    = master
        self._on_pause  = on_pause
        self._on_resume = on_resume
        self._on_cancel = on_cancel
        self._on_finish = on_finish

        self._paused        = False
        self._compact       = False
        self._on_top        = True
        self._finished      = False
        self._done          = 0
        self._total         = 0
        self._success_count = 0
        self._error_count   = 0
        self._skipped_count = 0
        self._start_ts      = time.time()
        self._log_count     = 0

        # course card widgets: cid → (dot, code_lbl, title_lbl, count_lbl, bar)
        self._course_cards:   dict[str, tuple] = {}
        self._name_to_id:     dict[str, str]   = {}
        self._id_to_cid:      dict[str, str]   = {}
        self._course_display: dict[str, str]   = {}
        self._course_totals:  dict[str, int]   = {}

        self._build()

    # ── Layout ────────────────────────────────────────────────

    def _build(self) -> None:
        self.pack_propagate(False)

        # Compact bar (hidden by default)
        self._compact_bar = ctk.CTkFrame(
            self, fg_color=BG_ELEVATED, corner_radius=0, height=48,
        )
        self._compact_bar.pack_propagate(False)
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
            self._compact_bar, text="↑ Genişlet",
            command=self._toggle_compact, **BTN_GHOST,
        ).grid(row=0, column=2, padx=8)

        # Main body
        self._body = ctk.CTkFrame(self, fg_color=BG_BASE, corner_radius=0)
        self._body.pack(fill="both", expand=True)
        self._body.grid_columnconfigure(0, weight=1)
        self._body.grid_rowconfigure(3, weight=1)  # log expands

        self._build_nav()
        self._build_hero()
        self._build_cards_row()
        self._build_log()
        self._build_stats_bar()

    # ── Nav bar ───────────────────────────────────────────────

    def _build_nav(self) -> None:
        nav = ctk.CTkFrame(
            self._body, fg_color=BG_ELEVATED, corner_radius=0, height=52,
        )
        nav.grid(row=0, column=0, sticky="ew")
        nav.grid_columnconfigure(1, weight=1)
        nav.grid_propagate(False)

        # ── Left: back button ─────────────────────────────────
        self._btn_back = ctk.CTkButton(
            nav, text="← Geri",
            command=self._go_back,
            fg_color="transparent", hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY, border_color=BORDER, border_width=1,
            corner_radius=8, font=("Inter", 12), height=34, width=84,
        )
        self._btn_back.grid(row=0, column=0, padx=(12, 0), pady=9, sticky="w")

        # ── Center: app badge ─────────────────────────────────
        center = ctk.CTkFrame(nav, fg_color="transparent")
        center.grid(row=0, column=1)
        badge = ctk.CTkFrame(center, fg_color=BG_BASE, corner_radius=20)
        badge.pack()
        ctk.CTkLabel(
            badge, text="● BLACKBOARD SYNC",
            font=("Inter", 10, "bold"), text_color=ACCENT,
        ).pack(padx=14, pady=6)

        # ── Right: control pill + cancel ──────────────────────
        right = ctk.CTkFrame(nav, fg_color="transparent")
        right.grid(row=0, column=2, padx=(0, 12), pady=9, sticky="e")

        pill = ctk.CTkFrame(right, fg_color=BG_BASE, corner_radius=8,
                            border_width=1, border_color=BORDER)
        pill.pack(side="left", padx=(0, 8))

        self._btn_pin = ctk.CTkButton(
            pill, text="📌  Sabitle", command=self._toggle_top,
            fg_color="transparent", hover_color=BG_HOVER,
            text_color=TEXT_TERTIARY, corner_radius=6,
            font=("Inter", 11), height=34, width=90,
        )
        self._btn_pin.pack(side="left")

        ctk.CTkFrame(pill, fg_color=BORDER, width=1, height=18).pack(side="left")

        self._btn_compact = ctk.CTkButton(
            pill, text="⬛  Küçült", command=self._toggle_compact,
            fg_color="transparent", hover_color=BG_HOVER,
            text_color=TEXT_TERTIARY, corner_radius=6,
            font=("Inter", 11), height=34, width=90,
        )
        self._btn_compact.pack(side="left")

        ctk.CTkFrame(pill, fg_color=BORDER, width=1, height=18).pack(side="left")

        self._btn_pause = ctk.CTkButton(
            pill, text="⏸  Duraklat", command=self._pause_resume,
            fg_color="transparent", hover_color=BG_HOVER,
            text_color=TEXT_TERTIARY, corner_radius=6,
            font=("Inter", 11), height=34, width=100,
        )
        self._btn_pause.pack(side="left")

        self._btn_cancel = ctk.CTkButton(
            right, text="✕ İptal", command=self._confirm_cancel,
            fg_color="#3b0a0a", hover_color="#450a0a",
            text_color="#fca5a5", border_color="#7f1d1d", border_width=1,
            corner_radius=8, font=("Inter", 11), height=34, width=80,
        )
        self._btn_cancel.pack(side="left")

        ctk.CTkFrame(nav, fg_color=BORDER, height=1, corner_radius=0).place(
            relx=0, rely=1.0, relwidth=1.0, anchor="sw",
        )

        # Tooltips
        _Tooltip(self._btn_back,    "Kurs listesine geri dön  [Esc]")
        _Tooltip(self._btn_pin,     "Pencereyi her zaman üstte tut / serbest bırak")
        _Tooltip(self._btn_compact, "Küçük bara daralt / genişlet")
        _Tooltip(self._btn_pause,   "İndirmeyi duraklat veya devam ettir")
        _Tooltip(self._btn_cancel,  "İndirmeyi tamamen iptal et")

    # ── Hero: counter + bar + status ──────────────────────────

    def _build_hero(self) -> None:
        hero = ctk.CTkFrame(self._body, fg_color=BG_ELEVATED, corner_radius=0)
        hero.grid(row=1, column=0, sticky="ew")
        hero.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(hero, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=(18, 16))
        inner.grid_columnconfigure(0, weight=1)

        # Counter row
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top.grid_columnconfigure(0, weight=1)

        self._lbl_counter = ctk.CTkLabel(
            top, text="0 / 0 dosya",
            font=("Inter", 26, "bold"), text_color=TEXT_PRIMARY, anchor="w",
        )
        self._lbl_counter.grid(row=0, column=0, sticky="w")

        self._lbl_pct = ctk.CTkLabel(
            top, text="",
            font=("Inter", 22, "bold"), text_color=ACCENT, anchor="e",
        )
        self._lbl_pct.grid(row=0, column=1, sticky="e")

        # Progress bar — thick
        self._progress_bar = ctk.CTkProgressBar(
            inner, progress_color=ACCENT,
            fg_color=BORDER, height=10, corner_radius=5,
        )
        self._progress_bar.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self._progress_bar.set(0)

        # Status + ETA row
        bot = ctk.CTkFrame(inner, fg_color="transparent")
        bot.grid(row=2, column=0, sticky="ew")
        bot.grid_columnconfigure(0, weight=1)

        self._lbl_current = ctk.CTkLabel(
            bot, text="Başlatılıyor...",
            font=FONT_BODY, text_color=TEXT_SECONDARY, anchor="w",
        )
        self._lbl_current.grid(row=0, column=0, sticky="w")

        self._lbl_eta = ctk.CTkLabel(
            bot, text="",
            font=FONT_SMALL, text_color=TEXT_TERTIARY, anchor="e",
        )
        self._lbl_eta.grid(row=0, column=1, sticky="e", padx=(12, 0))

        ctk.CTkFrame(hero, fg_color=BORDER, height=1, corner_radius=0).pack(
            fill="x", side="bottom",
        )

    # ── Course cards row ──────────────────────────────────────

    def _build_cards_row(self) -> None:
        wrapper = ctk.CTkFrame(self._body, fg_color="transparent")
        wrapper.grid(row=2, column=0, sticky="ew", padx=16, pady=(12, 0))

        self._cards_scroll = ctk.CTkScrollableFrame(
            wrapper, fg_color="transparent",
            orientation="horizontal", height=90,
        )
        self._cards_scroll.pack(fill="x")

    # ── Log panel (full width) ────────────────────────────────

    def _build_log(self) -> None:
        log_card = ctk.CTkFrame(
            self._body, fg_color=BG_ELEVATED, corner_radius=8,
            border_width=1, border_color=BORDER,
        )
        log_card.grid(row=3, column=0, sticky="nsew", padx=16, pady=(8, 4))
        log_card.grid_columnconfigure(0, weight=1)
        log_card.grid_rowconfigure(2, weight=1)

        # Header row
        hdr = ctk.CTkFrame(log_card, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 0))
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr, text="AKTİVİTE",
            font=("Inter", 10, "bold"), text_color=TEXT_TERTIARY, anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            hdr, text="Temizle", command=self._clear_log, **BTN_GHOST,
        ).grid(row=0, column=1)

        ctk.CTkFrame(log_card, fg_color=BORDER, height=1).grid(
            row=1, column=0, sticky="ew", pady=(6, 0),
        )

        self._log_box = ctk.CTkTextbox(
            log_card, font=("JetBrains Mono", 11),
            fg_color="transparent", text_color=TEXT_SECONDARY,
            state="disabled", wrap="char",
        )
        self._log_box.grid(row=2, column=0, sticky="nsew", padx=8, pady=(4, 6))

        tb = self._log_box._textbox
        tb.tag_configure("success", foreground=SUCCESS)
        tb.tag_configure("error",   foreground=ERROR)
        tb.tag_configure("warning", foreground=WARNING)
        tb.tag_configure("accent",  foreground=ACCENT)
        tb.tag_configure("dim",     foreground=TEXT_TERTIARY)
        tb.tag_configure("header",
                         foreground=ACCENT,
                         font=("JetBrains Mono", 11, "bold"),
                         spacing1=6, spacing3=4)

    # ── Stats bar ─────────────────────────────────────────────

    def _build_stats_bar(self) -> None:
        bar = ctk.CTkFrame(
            self._body, fg_color=BG_ELEVATED, corner_radius=0, height=36,
        )
        bar.grid(row=4, column=0, sticky="ew")
        bar.grid_propagate(False)

        ctk.CTkFrame(bar, fg_color=BORDER, height=1, corner_radius=0).place(
            relx=0, rely=0, relwidth=1.0,
        )

        row = ctk.CTkFrame(bar, fg_color="transparent")
        row.place(relx=0.5, rely=0.65, anchor="center")

        self._lbl_ok = ctk.CTkLabel(
            row, text="✓  0 indirildi",
            font=FONT_SMALL, text_color=TEXT_TERTIARY,
        )
        self._lbl_ok.pack(side="left")

        ctk.CTkLabel(row, text="  ·  ", font=FONT_SMALL, text_color=BORDER).pack(side="left")

        self._lbl_err = ctk.CTkLabel(
            row, text="✗  0 hata",
            font=FONT_SMALL, text_color=TEXT_TERTIARY,
        )
        self._lbl_err.pack(side="left")

        ctk.CTkLabel(row, text="  ·  ", font=FONT_SMALL, text_color=BORDER).pack(side="left")

        self._lbl_rem = ctk.CTkLabel(
            row, text="○  0 bekliyor",
            font=FONT_SMALL, text_color=TEXT_TERTIARY,
        )
        self._lbl_rem.pack(side="left")

    # ── Public API ────────────────────────────────────────────

    def set_courses(self, courses: dict[str, Course], total: Optional[int] = None) -> None:
        for cid, course in courses.items():
            code  = course.friendly_code or "–"
            title = course.friendly_title or course.name

            self._name_to_id[course.name]  = cid
            self._id_to_cid[course.id]     = cid
            self._course_totals[cid]       = len(course.items)
            self._course_display[cid] = f"{code} · {title}" if code != "–" else title

            self._make_course_card(cid, code, title, len(course.items))

        self._total = total if total is not None else sum(
            len(c.items) for c in courses.values()
        )
        self._lbl_rem.configure(text=f"○  {self._total} bekliyor")
        self._lbl_counter.configure(text=f"0 / {self._total} dosya")

    def _make_course_card(self, cid: str, code: str, title: str, total: int = 0) -> None:
        card = ctk.CTkFrame(
            self._cards_scroll,
            fg_color=BG_ELEVATED, corner_radius=8,
            border_width=1, border_color=BORDER,
            width=180,
        )
        card.pack(side="left", padx=(0, 10), fill="y")
        card.pack_propagate(False)
        card.grid_columnconfigure(0, weight=1)

        # Top row: dot + code + count
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 2))
        top.grid_columnconfigure(1, weight=1)

        dot = ctk.CTkLabel(
            top, text="○", font=("Inter", 14),
            text_color=TEXT_TERTIARY, width=20, anchor="w",
        )
        dot.grid(row=0, column=0)

        code_lbl = ctk.CTkLabel(
            top, text=code,
            font=("Inter", 12, "bold"), text_color=TEXT_TERTIARY, anchor="w",
        )
        code_lbl.grid(row=0, column=1, sticky="w", padx=(4, 0))

        count_lbl = ctk.CTkLabel(
            top, text=f"0/{total}" if total else "0/–",
            font=("Inter", 10), text_color=TEXT_TERTIARY, anchor="e",
        )
        count_lbl.grid(row=0, column=2, sticky="e")

        # Title
        title_lbl = ctk.CTkLabel(
            card, text=title,
            font=("Inter", 10), text_color=TEXT_TERTIARY,
            anchor="w", wraplength=156,
        )
        title_lbl.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 6))

        # Mini progress bar
        bar = ctk.CTkProgressBar(
            card, progress_color=ACCENT, fg_color=BORDER, height=3, corner_radius=0,
        )
        bar.grid(row=2, column=0, sticky="ew", padx=0, pady=(0, 0))
        bar.set(0)

        self._course_cards[cid] = (dot, code_lbl, title_lbl, count_lbl, bar)

    def update_course_status(self, course_id: str, status: str) -> None:
        cid = self._id_to_cid.get(course_id, course_id)
        w = self._course_cards.get(cid)
        if not w:
            return
        dot, code_lbl, title_lbl, count_lbl, bar = w

        if status == "active":
            dot.configure(text="●", text_color=ACCENT)
            code_lbl.configure(text_color=ACCENT)
            title_lbl.configure(text_color=TEXT_SECONDARY)
            # Highlight card border
            dot.master.master.configure(border_color=ACCENT)
            # Log header
            display = self._course_display.get(cid, cid)
            n = self._course_totals.get(cid, 0)
            suffix = f"  ({n} öğe)" if n else ""
            self._log_insert(f"\n  ▸  {display}{suffix}\n", "header")

        elif status == "done":
            dot.configure(text="✓", text_color=SUCCESS)
            code_lbl.configure(text_color=SUCCESS)
            title_lbl.configure(text_color=TEXT_TERTIARY)
            dot.master.master.configure(border_color=BORDER)
            bar.set(1)

    def update_progress(self, course_name: str, done: int, total: int) -> None:
        self._done += 1
        fraction = self._done / self._total if self._total else 0
        pct      = int(fraction * 100)

        self._progress_bar.set(fraction)
        self._cbar_prog.set(fraction)
        self._lbl_counter.configure(text=f"{self._done} / {self._total} dosya")
        self._lbl_pct.configure(text=f"%{pct}")
        self._lbl_ok.configure(text=f"✓  {self._success_count} indirildi", text_color=SUCCESS)

        rem = max(0, self._total - self._done)
        self._lbl_rem.configure(text=f"○  {rem} bekliyor")

        # Per-course card update
        cid = self._name_to_id.get(course_name)
        if cid and cid in self._course_cards:
            _, _, _, count_lbl, bar = self._course_cards[cid]
            count_lbl.configure(text=f"{done}/{total}")
            bar.set(done / total if total else 0)

        elapsed = time.time() - self._start_ts
        if fraction > 0.02 and elapsed > 1:
            eta_s = int(elapsed / fraction * (1 - fraction))
            m, s  = divmod(eta_s, 60)
            self._lbl_eta.configure(text=f"~{m}d {s}s kaldı" if m else f"~{s}s kaldı")

    def on_file_done(self, item: Item, success: bool) -> None:
        if success:
            self._success_count += 1
            self._lbl_ok.configure(
                text=f"✓  {self._success_count} indirildi", text_color=SUCCESS,
            )
        else:
            self._error_count += 1
            self._lbl_err.configure(
                text=f"✗  {self._error_count} hata", text_color=ERROR,
            )

        tag    = "success" if success else "error"
        prefix = "✓" if success else "✗"
        self._log_insert(f"    {prefix}  ", "dim")
        self._log_insert(f"{item.name}\n", tag)
        self._lbl_current.configure(text=item.name)
        self._cbar_lbl.configure(text=item.name[:60])

    def add_log(self, message: str, tag: str = "") -> None:
        self._log_insert(message + "\n", tag or "dim")

    def _log_insert(self, text: str, tag: str = "") -> None:
        self._log_count += 1
        tb = self._log_box._textbox
        self._log_box.configure(state="normal")

        if self._log_count > _MAX_LOG:
            tb.delete("1.0", "3.0")
            self._log_count = max(0, self._log_count - 2)

        if tag:
            tb.insert("end", text, (tag,))
        else:
            tb.insert("end", text)

        tb.see("end")
        self._log_box.configure(state="disabled")

    # ── Geri Dön / Finish ─────────────────────────────────────

    def _finish(self) -> None:
        self._finished = True
        if self._on_finish:
            self._on_finish()

    def _go_back(self) -> None:
        if self._finished:
            self._finish()
            return
        popup = ctk.CTkToplevel(self._master)
        popup.title("Geri Dön")
        popup.geometry("360x200")
        popup.resizable(False, False)
        popup.grab_set()
        popup.attributes("-topmost", True)
        popup.configure(fg_color=BG_ELEVATED)

        ctk.CTkFrame(popup, fg_color=WARNING, corner_radius=0, height=4).pack(fill="x")

        ctk.CTkLabel(
            popup, text="⚠  İndirme Devam Ediyor",
            font=("Inter", 14, "bold"), text_color=WARNING,
        ).pack(pady=(18, 4))

        ctk.CTkLabel(
            popup,
            text="Geri dönerseniz indirme işlemi kesilecek.\nDevam etmek istiyor musunuz?",
            font=FONT_BODY, text_color=TEXT_SECONDARY, justify="center",
        ).pack(padx=24, pady=(0, 18))

        r = ctk.CTkFrame(popup, fg_color="transparent")
        r.pack(padx=24, fill="x")
        r.grid_columnconfigure(0, weight=1)
        r.grid_columnconfigure(1, weight=1)

        def _do():
            popup.destroy()
            self._on_cancel()
            self._finish()

        ctk.CTkButton(
            r, text="Evet, kes ve geri dön", command=_do,
            fg_color="#3b0a0a", hover_color="#450a0a",
            text_color="#fca5a5", border_color="#7f1d1d", border_width=1,
            corner_radius=8, font=FONT_SMALL, height=36,
        ).grid(row=0, column=0, padx=(0, 4), sticky="ew")
        ctk.CTkButton(
            r, text="Devam et", command=popup.destroy, **BTN_PRIMARY,
        ).grid(row=0, column=1, padx=(4, 0), sticky="ew")
        self._master.attributes("-topmost", False)
        popup.after(50, lambda: (popup.lift(), popup.focus_force()))
        popup.bind("<Destroy>", lambda _: self._master.attributes("-topmost", self._on_top), add="+")

    # ── Summary popup ─────────────────────────────────────────

    def show_summary(self, downloaded: int, failed: int, skipped: int) -> None:
        self._finished = True
        try:
            self._btn_cancel.pack_forget()
            self._btn_back.configure(text="← Kurs Listesine Dön")
        except Exception:
            pass

        popup = ctk.CTkToplevel(self._master)
        popup.title("İndirme Tamamlandı")
        popup.geometry("380x400")
        popup.resizable(False, False)
        popup.grab_set()
        popup.attributes("-topmost", True)
        popup.configure(fg_color=BG_ELEVATED)

        ctk.CTkFrame(popup, fg_color=ACCENT, corner_radius=0, height=4).pack(fill="x")

        ctk.CTkLabel(
            popup, text="✓",
            font=("Inter", 44, "bold"), text_color=SUCCESS,
        ).pack(pady=(16, 2))

        ctk.CTkLabel(
            popup, text="İndirme Tamamlandı",
            font=("Inter", 17, "bold"), text_color=TEXT_PRIMARY,
        ).pack()

        ctk.CTkLabel(
            popup, text=f"{downloaded + failed + skipped} öğe işlendi",
            font=FONT_SMALL, text_color=TEXT_TERTIARY,
        ).pack(pady=(4, 12))

        card = ctk.CTkFrame(popup, fg_color=BG_BASE, corner_radius=8, border_width=1, border_color=BORDER)
        card.pack(fill="x", padx=28)

        for color, icon, value, label in [
            (SUCCESS,                                    "✓", str(downloaded), "dosya indirildi"),
            (ERROR if failed else TEXT_TERTIARY,         "✗", str(failed),    "hata"),
            (TEXT_TERTIARY,                              "↷", str(skipped),   "atlandı"),
        ]:
            r = ctk.CTkFrame(card, fg_color="transparent")
            r.pack(fill="x", padx=16, pady=5)
            ctk.CTkLabel(r, text=icon, font=("Inter", 14), text_color=color, width=24, anchor="center").pack(side="left")
            ctk.CTkLabel(r, text=value, font=("Inter", 14, "bold"), text_color=TEXT_PRIMARY, width=40, anchor="w").pack(side="left", padx=(8, 4))
            ctk.CTkLabel(r, text=label, font=FONT_BODY, text_color=TEXT_SECONDARY, anchor="w").pack(side="left")

        btn_row = ctk.CTkFrame(popup, fg_color="transparent")
        btn_row.pack(fill="x", padx=28, pady=(14, 20))
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)

        def _done():
            popup.destroy()
            self._finish()

        ctk.CTkButton(btn_row, text="Geri Dön", command=_done, **BTN_SECONDARY).grid(row=0, column=0, padx=(0, 4), sticky="ew")
        ctk.CTkButton(btn_row, text="Kapat",    command=_done, **BTN_PRIMARY).grid(row=0, column=1, padx=(4, 0), sticky="ew")
        self._master.attributes("-topmost", False)
        popup.after(50, lambda: (popup.lift(), popup.focus_force()))
        popup.bind("<Destroy>", lambda _: self._master.attributes("-topmost", self._on_top), add="+")

    # ── Controls ──────────────────────────────────────────────

    def _pause_resume(self) -> None:
        self._paused = not self._paused
        if self._paused:
            self._btn_pause.configure(text="▶  Devam Et")
            self._on_pause()
            self._log_insert("⏸  Duraklatıldı\n", "warning")
        else:
            self._btn_pause.configure(text="⏸  Duraklat")
            self._on_resume()
            self._log_insert("▶  Devam edildi\n", "accent")

    def _confirm_cancel(self) -> None:
        popup = ctk.CTkToplevel(self._master)
        popup.title("İptal")
        popup.geometry("300x160")
        popup.resizable(False, False)
        popup.grab_set()
        popup.attributes("-topmost", True)
        popup.configure(fg_color=BG_ELEVATED)

        ctk.CTkLabel(
            popup, text="İndirmeyi iptal et?",
            font=FONT_BODY, text_color=TEXT_PRIMARY,
        ).pack(padx=24, pady=(28, 16))

        r = ctk.CTkFrame(popup, fg_color="transparent")
        r.pack()

        def _do():
            popup.destroy()
            self._on_cancel()
            self._finish()

        ctk.CTkButton(
            r, text="Evet, iptal et", command=_do,
            fg_color="#7f1d1d", hover_color="#450a0a",
            text_color="#fca5a5", corner_radius=6, font=FONT_SMALL, height=36, width=140,
        ).pack(side="left", padx=6)
        ctk.CTkButton(r, text="Devam et", command=popup.destroy, **BTN_SECONDARY).pack(side="left", padx=6)
        self._master.attributes("-topmost", False)
        popup.after(50, lambda: (popup.lift(), popup.focus_force()))
        popup.bind("<Destroy>", lambda _: self._master.attributes("-topmost", self._on_top), add="+")

    def _toggle_top(self) -> None:
        self._on_top = not self._on_top
        self._master.attributes("-topmost", self._on_top)
        self._btn_pin.configure(
            text="📌  Sabitle" if self._on_top else "📌  Serbest",
            text_color=ACCENT if self._on_top else TEXT_TERTIARY,
        )

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


class _Tooltip:
    """Hover tooltip — CTkButton iç canvas hiyerarşisine uyumlu."""

    _TIP_BG  = "#0d1120"
    _TIP_FG  = "#94a3b8"
    _TIP_BD  = "#1e2a3a"

    def __init__(self, widget: ctk.CTkBaseClass, text: str) -> None:
        self._widget   = widget
        self._text     = text
        self._win: tk.Toplevel | None = None
        self._after_id: Optional[str] = None
        self._bind_tree(widget)

    def _bind_tree(self, w) -> None:
        """Widget ve tüm child'larına event binding yap (CTk iç canvas için)."""
        try:
            w.bind("<Enter>",       self._on_enter, add="+")
            w.bind("<Leave>",       self._on_leave, add="+")
            w.bind("<ButtonPress>", self._hide,     add="+")
            for child in w.winfo_children():
                self._bind_tree(child)
        except Exception:
            pass

    def _on_enter(self, _event=None) -> None:
        if self._after_id:
            self._widget.after_cancel(self._after_id)
        self._after_id = self._widget.after(350, self._show)

    def _on_leave(self, event=None) -> None:
        # Cursor hâlâ ana widget sınırları içindeyse gizleme (iç canvas'a geçiş)
        try:
            if event:
                w = self._widget
                wx, wy = w.winfo_rootx(), w.winfo_rooty()
                if wx <= event.x_root <= wx + w.winfo_width() and \
                   wy <= event.y_root <= wy + w.winfo_height():
                    return
        except Exception:
            pass
        if self._after_id:
            self._widget.after_cancel(self._after_id)
            self._after_id = None
        self._hide()

    def _show(self, _event=None) -> None:
        self._after_id = None
        if self._win:
            return
        w = self._widget
        x = w.winfo_rootx() + w.winfo_width() // 2
        y = w.winfo_rooty() + w.winfo_height() + 6

        self._win = tk.Toplevel(w)
        self._win.wm_overrideredirect(True)
        self._win.attributes("-topmost", True)
        self._win.configure(background=self._TIP_BD)

        inner = tk.Frame(self._win, background=self._TIP_BG, bd=0)
        inner.pack(padx=1, pady=1)
        tk.Label(
            inner, text=self._text,
            background=self._TIP_BG, foreground=self._TIP_FG,
            font=("Inter", 10), padx=10, pady=5,
        ).pack()

        self._win.update_idletasks()
        tw = self._win.winfo_width()
        self._win.geometry(f"+{x - tw // 2}+{y}")
        self._win.lift()

    def _hide(self, _event=None) -> None:
        self._after_id = None
        if self._win:
            self._win.destroy()
            self._win = None
