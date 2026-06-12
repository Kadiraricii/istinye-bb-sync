from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from core.models import Course, CourseStatus
from gui.theme import (
    ACCENT, BG_BASE, BG_ELEVATED, BG_HOVER, BORDER,
    FONT_BODY, FONT_SMALL,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY,
)


def _greeting(name: str) -> str:
    hour = datetime.now().hour
    if 6 <= hour < 12:
        prefix = "Günaydın"
    elif 12 <= hour < 17:
        prefix = "İyi günler"
    elif 17 <= hour < 22:
        prefix = "İyi akşamlar"
    else:
        prefix = "İyi geceler"
    return f"{prefix}, {name} 👋" if name else f"{prefix} 👋"


_DEFAULT_DIR = Path.home() / "Downloads" / "Blackboard"


def _tr_fold(s: str) -> str:
    """Türkçe büyük/küçük harf duyarsız karşılaştırma için normalleştirir."""
    return (
        s.replace("İ", "i").replace("I", "i").replace("ı", "i")
         .replace("Ş", "ş").replace("Ğ", "ğ").replace("Ü", "ü")
         .replace("Ö", "ö").replace("Ç", "ç")
         .lower()
    )

_SEM_COLORS = {
    "Güz":   ("#92400e", "#fbbf24"),
    "Bahar": ("#1e3a5f", "#60a5fa"),
    "Yaz":   ("#14532d", "#4ade80"),
}


class CoursesScreen(ctk.CTkFrame):
    """Ders seçim ekranı."""

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
        self._sem_filter    = "Tümü"
        self._build()

    # ── Layout ────────────────────────────────────────────────

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # ── Üst accent şeridi ───────────────────
        ctk.CTkFrame(self, fg_color=ACCENT, corner_radius=0, height=3).grid(
            row=0, column=0, sticky="ew",
        )

        # ── Header ──────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0)
        hdr.grid(row=1, column=0, sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)

        # Geri
        ctk.CTkButton(
            hdr, text="←  Geri",
            command=self._on_back,
            fg_color="transparent", hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY, font=("Inter", 12),
            corner_radius=6, height=32, width=82,
        ).grid(row=0, column=0, padx=(12, 0), pady=(12, 8), sticky="nw")

        # Başlık + karşılama
        head_center = ctk.CTkFrame(hdr, fg_color="transparent")
        head_center.grid(row=0, column=1, padx=10, pady=(10, 8), sticky="w")

        title_row = ctk.CTkFrame(head_center, fg_color="transparent")
        title_row.pack(anchor="w")

        ctk.CTkLabel(
            title_row,
            text="Ders Seçimi",
            font=("Inter", 15, "bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        self._lbl_total = ctk.CTkLabel(
            title_row,
            text="",
            font=("Inter", 10, "bold"),
            text_color=ACCENT,
            fg_color=BG_HOVER,
            corner_radius=8,
            height=18,
        )
        self._lbl_total.pack(side="left", padx=(8, 0))

        self._lbl_greeting = ctk.CTkLabel(
            head_center,
            text="",
            font=("Inter", 11),
            text_color=TEXT_TERTIARY,
        )
        self._lbl_greeting.pack(anchor="w", pady=(2, 0))

        # Aksiyon butonları
        act_box = ctk.CTkFrame(hdr, fg_color="transparent")
        act_box.grid(row=0, column=2, padx=(0, 12), pady=(12, 8), sticky="ne")

        ctk.CTkButton(
            act_box, text="Tümünü seç",
            command=self._select_all,
            fg_color="transparent", hover_color=BG_HOVER,
            text_color=ACCENT, font=("Inter", 11),
            corner_radius=6, height=30,
            border_width=1, border_color=BORDER,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            act_box, text="Temizle",
            command=self._clear_all,
            fg_color="transparent", hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY, font=("Inter", 11),
            corner_radius=6, height=30,
            border_width=1, border_color=BORDER,
        ).pack(side="left")

        # Header alt çizgisi
        ctk.CTkFrame(hdr, height=1, fg_color=BORDER).grid(
            row=1, column=0, columnspan=3, sticky="ew",
        )

        # ── Araç çubuğu ─────────────────────────
        toolbar = ctk.CTkFrame(self, fg_color=BG_BASE)
        toolbar.grid(row=2, column=0, sticky="ew", padx=14, pady=(10, 4))
        toolbar.grid_columnconfigure(0, weight=1)

        self._entry_search = ctk.CTkEntry(
            toolbar,
            placeholder_text="Ders kodu veya adı ara...",
            fg_color=BG_ELEVATED, border_color=BORDER, border_width=1,
            text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_TERTIARY,
            corner_radius=7, font=FONT_BODY, height=36,
        )
        self._entry_search.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._entry_search.bind("<KeyRelease>", self._on_search)

        self._sem_menu = ctk.CTkOptionMenu(
            toolbar,
            values=["Tümü"],
            command=self._on_sem_filter,
            fg_color=BG_ELEVATED,
            button_color=BORDER,
            button_hover_color=BG_HOVER,
            text_color=TEXT_PRIMARY,
            dropdown_fg_color=BG_ELEVATED,
            dropdown_hover_color=BG_HOVER,
            font=FONT_SMALL,
            width=150,
            height=36,
        )
        self._sem_menu.grid(row=0, column=1)

        # ── Kart listesi ─────────────────────────
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG_BASE,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=BG_HOVER,
        )
        self._scroll.grid(row=3, column=0, sticky="nsew", padx=14, pady=(0, 0))
        self._scroll.grid_columnconfigure((0, 1), weight=1)

        self._show_skeleton()

        # ── Footer ayırıcı ──────────────────────
        ctk.CTkFrame(self, fg_color=BORDER, corner_radius=0, height=1).grid(
            row=4, column=0, sticky="ew",
        )

        # ── Footer ──────────────────────────────
        footer = ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0)
        footer.grid(row=5, column=0, sticky="ew")
        footer.grid_columnconfigure(1, weight=1)

        # Klasör seçici
        dir_row = ctk.CTkFrame(footer, fg_color="transparent")
        dir_row.grid(row=0, column=0, padx=14, pady=11, sticky="w")

        ctk.CTkLabel(
            dir_row, text="📁",
            font=("Inter", 13), text_color=TEXT_TERTIARY,
        ).pack(side="left", padx=(0, 5))

        self._lbl_dir = ctk.CTkLabel(
            dir_row, text=self._short_path(self._dest_dir),
            font=("Inter", 11), text_color=TEXT_SECONDARY,
        )
        self._lbl_dir.pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            dir_row, text="Değiştir",
            command=self._pick_dir,
            fg_color="transparent", hover_color=BG_HOVER,
            text_color=ACCENT, font=("Inter", 11),
            corner_radius=5, height=26,
            border_width=1, border_color=BORDER,
        ).pack(side="left")

        # Seçim özeti
        self._lbl_summary = ctk.CTkLabel(
            footer, text="Ders seçilmedi",
            font=("Inter", 12), text_color=TEXT_TERTIARY,
            anchor="center",
        )
        self._lbl_summary.grid(row=0, column=1)

        # Devam →
        self._btn_continue = ctk.CTkButton(
            footer,
            text="Devam  →",
            command=self._continue,
            state="disabled",
            fg_color=ACCENT,
            hover_color="#6366f1",
            text_color="#ffffff",
            corner_radius=8,
            font=("Inter", 13, "bold"),
            height=38,
            width=120,
        )
        self._btn_continue.grid(row=0, column=2, padx=14, pady=10)

    # ── Public API ────────────────────────────────────────────

    def set_student_name(self, name: str) -> None:
        self._lbl_greeting.configure(text=_greeting(name))

    def load_courses(self, courses: dict[str, Course]) -> None:
        self._all_courses = courses
        self._update_sem_options()
        self.after(0, self._render_cards)

    def set_loading(self, loading: bool) -> None:
        if loading:
            self._show_skeleton()
            self._lbl_total.configure(text=" yükleniyor ", text_color=TEXT_TERTIARY)
        else:
            n = len(self._all_courses)
            self._lbl_total.configure(text=f" {n} ders ", text_color=ACCENT)

    # ── Dönem filtresi ────────────────────────────────────────

    def _update_sem_options(self) -> None:
        sems = sorted({
            c.semester for c in self._all_courses.values() if c.semester
        })
        self._sem_menu.configure(values=["Tümü"] + sems)

    def _on_sem_filter(self, value: str) -> None:
        self._sem_filter = value
        self._render_cards()

    # ── Kart render ──────────────────────────────────────────

    def _show_skeleton(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()
        for i in range(6):
            sk = ctk.CTkFrame(
                self._scroll, fg_color=BG_ELEVATED, corner_radius=10, height=96,
            )
            sk.grid(row=i // 2, column=i % 2, padx=6, pady=6, sticky="ew")

    def _render_cards(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()
        self._card_widgets.clear()

        filtered = self._filtered_courses()
        for i, (cid, course) in enumerate(filtered.items()):
            card = _CourseCard(
                self._scroll,
                course=course,
                selected=(cid in self._selected),
                on_toggle=lambda c=cid: self._toggle(c),
            )
            card.grid(row=i // 2, column=i % 2, padx=6, pady=6, sticky="ew")
            self._card_widgets[cid] = card

        total = len(self._all_courses)
        shown = len(filtered)
        if total:
            if shown != total:
                self._lbl_total.configure(
                    text=f" {shown}/{total} ders ", text_color=TEXT_SECONDARY,
                )
            else:
                self._lbl_total.configure(
                    text=f" {total} ders ", text_color=ACCENT,
                )
        self._update_summary()

    def _filtered_courses(self) -> dict[str, Course]:
        q   = _tr_fold(self._filter_text)
        sem = self._sem_filter
        return {
            cid: c for cid, c in self._all_courses.items()
            if (not q or q in _tr_fold(c.name) or q in _tr_fold(c.course_code or ""))
            and (sem == "Tümü" or c.semester == sem)
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
        n  = len(self._selected)
        mb = sum(
            self._all_courses[c].total_size_bytes
            for c in self._selected if c in self._all_courses
        ) / 1_048_576
        if n:
            size_str = f"  ·  ~{mb:.0f} MB" if mb > 0 else ""
            self._lbl_summary.configure(
                text=f"{n} ders seçili{size_str}",
                text_color=TEXT_PRIMARY,
            )
        else:
            self._lbl_summary.configure(
                text="Ders seçilmedi",
                text_color=TEXT_TERTIARY,
            )
        self._btn_continue.configure(state="normal" if n > 0 else "disabled")

    # ── Yardımcılar ───────────────────────────────────────────

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
        s = str(p)
        home = str(Path.home())
        if s.startswith(home):
            s = "~" + s[len(home):]
        return s if len(s) <= 38 else "..." + s[-35:]

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
        super().__init__(
            master,
            fg_color=BG_ELEVATED,
            corner_radius=10,
            border_width=1,
            border_color=ACCENT if selected else BORDER,
            cursor="hand2",
        )
        self._course   = course
        self._selected = selected
        self._build()
        self.bind("<Button-1>", lambda _: on_toggle())
        for child in self.winfo_children():
            child.bind("<Button-1>", lambda _: on_toggle())

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        # ── Üst satır: kod + semester tag + checkbox ──
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, padx=12, pady=(10, 0), sticky="ew")
        top.grid_columnconfigure(1, weight=1)

        code = self._course.friendly_code or self._course.course_code
        ctk.CTkLabel(
            top,
            text=code,
            font=("Inter", 13, "bold"),
            text_color=ACCENT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        sem = self._course.semester
        if sem:
            key = sem.split()[0]
            bg, fg = _SEM_COLORS.get(key, (BG_HOVER, TEXT_TERTIARY))
            ctk.CTkLabel(
                top,
                text=f"  {sem}  ",
                font=("Inter", 10, "bold"),
                text_color=fg,
                fg_color=bg,
                corner_radius=4,
            ).grid(row=0, column=1, sticky="w", padx=(8, 0))

        self._chk = ctk.CTkLabel(
            top,
            text="✓" if self._selected else "",
            font=("Inter", 13, "bold"),
            text_color="#ffffff",
            fg_color=ACCENT if self._selected else BORDER,
            corner_radius=4,
            width=20,
            height=20,
        )
        self._chk.grid(row=0, column=2, padx=(4, 0))

        # ── Ders adı ──────────────────────────────
        title = self._course.friendly_title or self._course.name
        ctk.CTkLabel(
            self,
            text=title,
            font=FONT_BODY,
            text_color=TEXT_PRIMARY,
            anchor="w",
            wraplength=190,
            justify="left",
        ).grid(row=1, column=0, padx=12, pady=(4, 0), sticky="w")

        # ── Hoca adı ─────────────────────────────
        if self._course.instructors:
            ctk.CTkLabel(
                self,
                text="👤 " + "  ·  ".join(self._course.instructors[:2]),
                font=FONT_SMALL,
                text_color=TEXT_SECONDARY,
                anchor="w",
            ).grid(row=2, column=0, padx=12, pady=(3, 0), sticky="w")

        # ── İstatistikler ─────────────────────────
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

        if self._course.status == CourseStatus.CRAWLED:
            stats_text = "  ·  ".join(parts) if parts else "İçerik bulunamadı"
        else:
            stats_text = "⏳ Taranıyor..."

        ctk.CTkLabel(
            self,
            text=stats_text,
            font=FONT_SMALL,
            text_color=TEXT_TERTIARY,
            anchor="w",
        ).grid(row=3, column=0, padx=12, pady=(3, 10), sticky="w")

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._chk.configure(
            text="✓" if selected else "",
            fg_color=ACCENT if selected else BORDER,
        )
        self.configure(border_color=ACCENT if selected else BORDER)
