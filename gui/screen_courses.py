from __future__ import annotations

import threading
from pathlib import Path
from tkinter import filedialog
from typing import Callable, Optional

import customtkinter as ctk

from core.models import Course
from gui.theme import (
    ACCENT, BG_BASE, BG_ELEVATED, BG_HOVER, BORDER,
    BTN_GHOST, BTN_PRIMARY, BTN_SECONDARY,
    DOT_BUSY, DOT_ERROR, DOT_OK, DOT_IDLE,
    FONT_BODY, FONT_HEADING, FONT_SMALL, FONT_HERO,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY,
    FRAME_CARD, FRAME_SELECTED,
)

_DEFAULT_DIR = Path.home() / "Downloads" / "Blackboard"


class CoursesScreen(ctk.CTkFrame):
    """
    Ders seçim ekranı.

    Kurs listesi dışarıdan yüklenir (App tarafından crawler çağrılır).
    on_continue(selected_courses, dest_dir) ile filtre ekranına geçilir.
    """

    def __init__(
        self,
        master: ctk.CTk,
        on_continue: Callable,
        on_back: Callable,
    ) -> None:
        super().__init__(master, fg_color=BG_BASE, corner_radius=0)
        self._on_continue  = on_continue
        self._on_back      = on_back
        self._all_courses:  dict[str, Course] = {}
        self._selected:     set[str] = set()
        self._dest_dir:     Path = _DEFAULT_DIR
        self._card_widgets: dict[str, _CourseCard] = {}
        self._filter_text   = ""

        self._build()

    # ── Layout ────────────────────────────────────────────────

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        hdr = ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0, height=56)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)
        hdr.grid_propagate(False)

        ctk.CTkButton(hdr, text="← Geri", command=self._on_back, **BTN_GHOST).grid(
            row=0, column=0, padx=12, pady=8,
        )
        self._lbl_count = ctk.CTkLabel(
            hdr, text="Dersler yükleniyor...",
            font=FONT_HEADING, text_color=TEXT_PRIMARY,
        )
        self._lbl_count.grid(row=0, column=1, padx=8)

        btn_box = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_box.grid(row=0, column=2, padx=12)
        ctk.CTkButton(btn_box, text="Tümünü Seç", command=self._select_all, **BTN_GHOST).pack(side="left", padx=2)
        ctk.CTkButton(btn_box, text="Temizle", command=self._clear_all, **BTN_GHOST).pack(side="left", padx=2)

        # Arama
        search_frame = ctk.CTkFrame(self, fg_color=BG_BASE)
        search_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(14, 0))
        search_frame.grid_columnconfigure(0, weight=1)

        self._entry_search = ctk.CTkEntry(
            search_frame,
            placeholder_text="Ders ara...",
            fg_color=BG_ELEVATED, border_color=BORDER, border_width=1,
            text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_TERTIARY,
            corner_radius=6, font=FONT_BODY, height=36,
        )
        self._entry_search.grid(row=0, column=0, sticky="ew")
        self._entry_search.bind("<KeyRelease>", self._on_search)

        # Kart listesi — scrollable
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG_BASE, scrollbar_button_color=BORDER,
        )
        self._scroll.grid(row=2, column=0, sticky="nsew", padx=20, pady=12)
        self._scroll.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Skeleton loading
        self._show_skeleton()

        # Alt bar
        footer = ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0, height=60)
        footer.grid(row=3, column=0, sticky="ew")
        footer.grid_columnconfigure(1, weight=1)
        footer.grid_propagate(False)

        dir_row = ctk.CTkFrame(footer, fg_color="transparent")
        dir_row.grid(row=0, column=0, padx=12, pady=8, sticky="w")
        self._lbl_dir = ctk.CTkLabel(
            dir_row, text=self._short_path(self._dest_dir),
            font=FONT_SMALL, text_color=TEXT_TERTIARY,
        )
        self._lbl_dir.pack(side="left", padx=(0, 6))
        ctk.CTkButton(dir_row, text="Değiştir", command=self._pick_dir, **BTN_GHOST).pack(side="left")

        self._lbl_summary = ctk.CTkLabel(
            footer, text="0 ders seçili",
            font=FONT_SMALL, text_color=TEXT_SECONDARY,
        )
        self._lbl_summary.grid(row=0, column=1)

        self._btn_continue = ctk.CTkButton(
            footer, text="Devam →", command=self._continue,
            state="disabled", **BTN_PRIMARY,
        )
        self._btn_continue.grid(row=0, column=2, padx=12, pady=10)

    # ── Public API ────────────────────────────────────────────

    def load_courses(self, courses: dict[str, Course]) -> None:
        """App tarafından crawler bitince çağrılır."""
        self._all_courses = courses
        self.after(0, self._render_cards)

    def set_loading(self, loading: bool) -> None:
        if loading:
            self._show_skeleton()
            self._lbl_count.configure(text="Dersler alınıyor...")
        else:
            self._lbl_count.configure(text=f"{len(self._all_courses)} ders bulundu")

    # ── Kart Render ───────────────────────────────────────────

    def _show_skeleton(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()
        for i in range(6):
            col = i % 2
            row = i // 2
            sk = ctk.CTkFrame(self._scroll, fg_color=BG_ELEVATED, corner_radius=8, height=88)
            sk.grid(row=row, column=col, padx=6, pady=6, sticky="ew")

    def _render_cards(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()
        self._card_widgets.clear()

        filtered = self._filtered_courses()
        for i, (cid, course) in enumerate(filtered.items()):
            col = i % 2
            row = i // 2
            card = _CourseCard(
                self._scroll,
                course=course,
                selected=(cid in self._selected),
                on_toggle=lambda c=cid: self._toggle(c),
            )
            card.grid(row=row, column=col, padx=6, pady=6, sticky="ew")
            self._card_widgets[cid] = card

        self._lbl_count.configure(text=f"{len(self._all_courses)} ders bulundu")
        self._update_summary()

    def _filtered_courses(self) -> dict[str, Course]:
        q = self._filter_text.lower()
        if not q:
            return self._all_courses
        return {
            cid: c for cid, c in self._all_courses.items()
            if q in c.name.lower() or q in (c.course_code or "").lower()
        }

    # ── Seçim ─────────────────────────────────────────────────

    def _toggle(self, cid: str) -> None:
        if cid in self._selected:
            self._selected.discard(cid)
        else:
            self._selected.add(cid)
        if cid in self._card_widgets:
            self._card_widgets[cid].set_selected(cid in self._selected)
        self._update_summary()

    def _select_all(self) -> None:
        for cid in self._filtered_courses():
            self._selected.add(cid)
        self._refresh_card_states()
        self._update_summary()

    def _clear_all(self) -> None:
        self._selected.clear()
        self._refresh_card_states()
        self._update_summary()

    def _refresh_card_states(self) -> None:
        for cid, card in self._card_widgets.items():
            card.set_selected(cid in self._selected)

    def _update_summary(self) -> None:
        n = len(self._selected)
        total_mb = sum(
            self._all_courses[c].total_size_bytes
            for c in self._selected if c in self._all_courses
        ) / 1_048_576
        size_str = f" · ~{total_mb:.0f} MB" if total_mb > 0 else ""
        self._lbl_summary.configure(text=f"{n} ders seçili{size_str}")
        self._btn_continue.configure(state="normal" if n > 0 else "disabled")

    # ── Arama / Klasör ────────────────────────────────────────

    def _on_search(self, _event=None) -> None:
        self._filter_text = self._entry_search.get().strip()
        self._render_cards()

    def _pick_dir(self) -> None:
        path = filedialog.askdirectory(initialdir=self._dest_dir)
        if path:
            self._dest_dir = Path(path)
            self._lbl_dir.configure(text=self._short_path(self._dest_dir))

    @staticmethod
    def _short_path(p: Path) -> str:
        try:
            return str(p.relative_to(Path.home().parent.parent)) if len(str(p)) > 40 else str(p)
        except ValueError:
            return str(p)[-40:]

    # ── Devam ─────────────────────────────────────────────────

    def _continue(self) -> None:
        selected = {cid: self._all_courses[cid] for cid in self._selected if cid in self._all_courses}
        self._on_continue(selected, self._dest_dir)


# ── Kurs Kartı ────────────────────────────────────────────────

class _CourseCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        course: Course,
        selected: bool,
        on_toggle: Callable,
    ) -> None:
        super().__init__(master, **FRAME_CARD, cursor="hand2")
        self._course    = course
        self._on_toggle = on_toggle
        self._selected  = selected
        self._build()
        self.bind("<Button-1>", lambda _: on_toggle())
        for child in self.winfo_children():
            child.bind("<Button-1>", lambda _: on_toggle())

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, padx=12, pady=(10, 2), sticky="ew")
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top,
            text=self._course.course_code or "",
            font=FONT_SMALL,
            text_color=ACCENT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self._chk = ctk.CTkLabel(
            top,
            text="☑" if self._selected else "☐",
            font=("Inter", 16),
            text_color=ACCENT if self._selected else TEXT_TERTIARY,
        )
        self._chk.grid(row=0, column=1)

        ctk.CTkLabel(
            self,
            text=self._course.name,
            font=FONT_BODY,
            text_color=TEXT_PRIMARY,
            anchor="w",
            wraplength=200,
        ).grid(row=1, column=0, padx=12, sticky="w")

        # stats
        parts = []
        if self._course.file_count:
            parts.append(f"{self._course.file_count} dosya")
        if self._course.video_count:
            parts.append(f"{self._course.video_count} video")
        if self._course.link_count:
            parts.append(f"{self._course.link_count} link")
        mb = self._course.total_size_bytes / 1_048_576
        if mb > 0:
            parts.append(f"~{mb:.0f} MB")

        ctk.CTkLabel(
            self,
            text="  ·  ".join(parts) if parts else "—",
            font=FONT_SMALL,
            text_color=TEXT_TERTIARY,
            anchor="w",
        ).grid(row=2, column=0, padx=12, pady=(2, 10), sticky="w")

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._chk.configure(
            text="☑" if selected else "☐",
            text_color=ACCENT if selected else TEXT_TERTIARY,
        )
        self.configure(border_color=ACCENT if selected else BORDER)
