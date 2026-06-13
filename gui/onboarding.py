from __future__ import annotations

import tkinter as tk
from typing import Callable

import customtkinter as ctk

from core.config import WINDOW_WIDTH
from gui.theme import (
    ACCENT, BG_BASE, BG_ELEVATED, BG_HOVER, BORDER,
    BTN_PRIMARY,
    FONT_BODY, FONT_SMALL,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY,
    SUCCESS,
)

_CARD = "#0d1120"

_SLIDES = [
    {
        "id":    "welcome",
        "icon":  "B",
        "color": ACCENT,
        "title": "Blackboard Sync'e\nHoş Geldiniz 👋",
        "body":  (
            "Istinye Üniversitesi Blackboard'undaki tüm ders\n"
            "materyallerini otomatik olarak bilgisayarına indir.\n\n"
            "Tek seferlik kurulum — sonra her şey otomatik."
        ),
    },
    {
        "id":    "how",
        "icon":  "?",
        "color": "#06b6d4",
        "title": "Nasıl Çalışır?",
        "steps": [
            ("🔐", "Giriş Yap",  "Microsoft hesabınla\ngüvenli giriş"),
            ("📚", "Ders Seç",   "İstediğin dersleri\nseç, gerisini atla"),
            ("⬇",  "İndir",      "Tüm materyaller\nklasörüne iner"),
        ],
    },
    {
        "id":    "features",
        "icon":  "✦",
        "color": "#8b5cf6",
        "title": "Neler İndirebilirsin?",
        "features": [
            ("📄", "PDF",     "Ders notları"),
            ("📊", "Sunum",   "PowerPoint"),
            ("📝", "Belge",   "Word dosyaları"),
            ("📗", "Tablo",   "Excel dosyaları"),
            ("🎬", "Video",   "Linkler kaydedilir"),
            ("📦", "Arşiv",   "ZIP / RAR"),
            ("🔄", "Akıllı",  "Tekrarı atlar"),
            ("⚡", "Hızlı",   "Eş zamanlı indir"),
        ],
    },
    {
        "id":    "ready",
        "icon":  "✓",
        "color": SUCCESS,
        "title": "Her Şey Hazır!",
        "body":  (
            "Giriş yaptıktan sonra derslerini seç ve\n"
            "indirme filtrelerini ayarla.\n\n"
            "Birkaç dakika içinde tüm materyaller\n"
            "bilgisayarında hazır olacak."
        ),
    },
]


class OnboardingScreen(ctk.CTkFrame):

    def __init__(self, master: ctk.CTk, on_done: Callable) -> None:
        super().__init__(master, fg_color=BG_BASE, corner_radius=0)
        self._on_done   = on_done
        self._slide_idx = 0
        self._animating = False
        self._frames:   list[ctk.CTkFrame] = []
        self._dot_lbls: list[ctk.CTkLabel] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_content_area()
        self._build_footer()

        # Widgetlar render olduktan sonra slaytları yerleştir
        self.after(80, self._init_slides)

    # ── Layout ────────────────────────────────────────────────

    def _build_header(self) -> None:
        hdr = ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0, height=56)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)
        hdr.grid_propagate(False)

        logo = ctk.CTkFrame(hdr, fg_color=ACCENT, corner_radius=10, width=34, height=34)
        logo.grid(row=0, column=0, padx=16, pady=11)
        logo.grid_propagate(False)
        ctk.CTkLabel(logo, text="B", font=("Inter", 16, "bold"),
                     text_color="#ffffff").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(hdr, text="Blackboard Sync",
                     font=("Inter", 14, "bold"), text_color=TEXT_PRIMARY,
                     anchor="w").grid(row=0, column=1, sticky="w")

        ctk.CTkButton(hdr, text="Atla →", command=self._finish,
                      fg_color="transparent", hover_color=BG_HOVER,
                      text_color=TEXT_TERTIARY, font=FONT_SMALL,
                      corner_radius=6, width=64,
                      ).grid(row=0, column=2, padx=16)

        ctk.CTkFrame(hdr, fg_color=BORDER, height=1,
                     corner_radius=0).place(relx=0, rely=1, relwidth=1, anchor="sw")

    def _build_content_area(self) -> None:
        # tk.Frame kullanıyoruz — CTkFrame place() içinde relwidth/relheight sorun çıkarabilir
        self._area = tk.Frame(self, bg=BG_BASE)
        self._area.grid(row=1, column=0, sticky="nsew")

    def _build_footer(self) -> None:
        ftr = ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0, height=72)
        ftr.grid(row=2, column=0, sticky="ew")
        ftr.grid_columnconfigure(1, weight=1)
        ftr.grid_propagate(False)

        ctk.CTkFrame(ftr, fg_color=BORDER, height=1,
                     corner_radius=0).place(relx=0, rely=0, relwidth=1)

        self._btn_back = ctk.CTkButton(
            ftr, text="← Geri", command=self._go_prev,
            fg_color="transparent", hover_color=BG_HOVER,
            text_color=TEXT_TERTIARY, border_color=BORDER, border_width=1,
            corner_radius=8, font=FONT_BODY, width=100,
        )
        self._btn_back.grid(row=0, column=0, padx=16, pady=17, sticky="w")

        dots_row = ctk.CTkFrame(ftr, fg_color="transparent")
        dots_row.grid(row=0, column=1)
        for i in range(len(_SLIDES)):
            d = ctk.CTkLabel(dots_row, text="●", font=("Inter", 10),
                             text_color=ACCENT if i == 0 else BORDER)
            d.grid(row=0, column=i, padx=4)
            self._dot_lbls.append(d)

        self._btn_next = ctk.CTkButton(
            ftr, text="İleri →", command=self._go_next,
            **BTN_PRIMARY, width=130,
        )
        self._btn_next.grid(row=0, column=2, padx=16, pady=17, sticky="e")

    # ── Slayt oluşturma ───────────────────────────────────────

    def _init_slides(self) -> None:
        W = WINDOW_WIDTH

        for i, slide in enumerate(_SLIDES):
            frame = self._make_slide_frame(slide)
            # relwidth/relheight: her zaman area boyutunu doldur; x ile kaydırılır
            frame.place(x=i * W, y=0, relwidth=1, relheight=1)
            self._frames.append(frame)

        self._update_ui()

    def _make_slide_frame(self, slide: dict) -> tk.Frame:
        # Slayt kapsayıcı olarak tk.Frame kullan (place width/height kısıtı yok)
        frame = tk.Frame(self._area, bg=BG_BASE)

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        color = slide["color"]

        # ── İkon dairesi (canvas) ────────────────────────────
        cv = tk.Canvas(inner, width=80, height=80, bg=BG_BASE, highlightthickness=0)
        cv.pack(pady=(0, 18))

        for j in range(6):
            r   = 42 + j * 6
            val = max(0, 20 - j * 4)
            br  = int(color[1:3], 16) * val // 255
            bg_ = int(color[3:5], 16) * val // 255
            bb  = int(color[5:7], 16) * val // 255
            col = f"#{max(br,2):02x}{max(bg_,4):02x}{max(bb,2):02x}"
            cv.create_oval(40 - r, 40 - r, 40 + r, 40 + r, fill=col, outline="")

        cv.create_oval(6, 6, 74, 74, fill=_CARD, outline=color, width=2)
        cv.create_text(40, 41, text=slide["icon"],
                       font=("Inter", 24, "bold"), fill=color)

        # ── Başlık ───────────────────────────────────────────
        ctk.CTkLabel(inner, text=slide["title"],
                     font=("Inter", 21, "bold"), text_color=TEXT_PRIMARY,
                     justify="center").pack(pady=(0, 12))

        # ── İçerik ───────────────────────────────────────────
        sid = slide["id"]
        if sid == "how":
            self._build_steps(inner, slide["steps"])
        elif sid == "features":
            self._build_features(inner, slide["features"])
        else:
            ctk.CTkLabel(inner, text=slide["body"],
                         font=FONT_BODY, text_color=TEXT_SECONDARY,
                         justify="center").pack()

        if sid == "ready":
            ctk.CTkFrame(inner, fg_color="transparent", height=14).pack()
            ctk.CTkButton(inner, text="Başlayalım  →",
                          command=self._finish,
                          **BTN_PRIMARY, width=200).pack()

        return frame

    def _build_steps(self, parent, steps: list) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(pady=(0, 6))

        for i, (icon, title, desc) in enumerate(steps):
            if i > 0:
                ctk.CTkLabel(row, text="→", font=("Inter", 16),
                             text_color=BORDER).grid(row=0, column=i * 2 - 1, padx=6)

            card = ctk.CTkFrame(row, fg_color=_CARD, corner_radius=12,
                                border_width=1, border_color=BORDER,
                                width=152, height=108)
            card.grid(row=0, column=i * 2, padx=4)
            card.grid_propagate(False)

            inn = ctk.CTkFrame(card, fg_color="transparent")
            inn.place(relx=0.5, rely=0.5, anchor="center")

            num = ctk.CTkFrame(inn, fg_color=ACCENT, corner_radius=10,
                               width=22, height=22)
            num.pack(pady=(0, 8))
            num.pack_propagate(False)
            ctk.CTkLabel(num, text=str(i + 1), font=("Inter", 11, "bold"),
                         text_color="#ffffff").place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkLabel(inn, text=f"{icon}  {title}",
                         font=("Inter", 12, "bold"),
                         text_color=TEXT_PRIMARY).pack()
            ctk.CTkLabel(inn, text=desc, font=("Inter", 10),
                         text_color=TEXT_TERTIARY, justify="center").pack(pady=(4, 0))

    def _build_features(self, parent, features: list) -> None:
        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack()

        for i, (icon, title, desc) in enumerate(features):
            r, c = divmod(i, 4)
            card = ctk.CTkFrame(grid, fg_color=_CARD, corner_radius=10,
                                border_width=1, border_color=BORDER,
                                width=146, height=70)
            card.grid(row=r, column=c, padx=4, pady=4)
            card.grid_propagate(False)

            inn = ctk.CTkFrame(card, fg_color="transparent")
            inn.place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkLabel(inn, text=icon, font=("Inter", 17)).pack()
            ctk.CTkLabel(inn, text=title, font=("Inter", 11, "bold"),
                         text_color=TEXT_PRIMARY).pack()
            ctk.CTkLabel(inn, text=desc, font=("Inter", 9),
                         text_color=TEXT_TERTIARY).pack()

    # ── Animasyon ─────────────────────────────────────────────

    def _go_next(self) -> None:
        if self._animating or self._slide_idx >= len(_SLIDES) - 1:
            return
        self._animate_slide(self._slide_idx, self._slide_idx + 1, direction=1)

    def _go_prev(self) -> None:
        if self._animating or self._slide_idx <= 0:
            return
        self._animate_slide(self._slide_idx, self._slide_idx - 1, direction=-1)

    def _animate_slide(self, from_idx: int, to_idx: int, direction: int) -> None:
        if not self._frames:
            return
        self._animating = True
        W = WINDOW_WIDTH

        from_frame = self._frames[from_idx]
        to_frame   = self._frames[to_idx]

        to_frame.place(x=direction * W, y=0, relwidth=1, relheight=1)
        to_frame.lift()

        from_x = [0.0]
        to_x   = [float(direction * W)]

        def _step() -> None:
            diff_from = (-direction * W) - from_x[0]
            diff_to   = 0.0 - to_x[0]

            if abs(diff_to) < 2.0:
                from_frame.place(x=-direction * W, y=0, relwidth=1, relheight=1)
                to_frame.place(x=0, y=0, relwidth=1, relheight=1)
                self._slide_idx = to_idx
                self._animating  = False
                self._update_ui()
                return

            from_x[0] += diff_from * 0.22
            to_x[0]   += diff_to   * 0.22
            from_frame.place(x=int(from_x[0]), y=0, relwidth=1, relheight=1)
            to_frame.place(x=int(to_x[0]),     y=0, relwidth=1, relheight=1)
            self.after(14, _step)

        _step()

    def _update_ui(self) -> None:
        idx = self._slide_idx
        n   = len(_SLIDES)

        for i, dot in enumerate(self._dot_lbls):
            dot.configure(text_color=ACCENT if i == idx else BORDER)

        self._btn_back.configure(
            state="normal"   if idx > 0 else "disabled",
            text_color=TEXT_SECONDARY if idx > 0 else BORDER,
        )

        if idx == n - 1:
            self._btn_next.configure(state="disabled", fg_color=BORDER,
                                     text_color=TEXT_TERTIARY)
        else:
            self._btn_next.configure(state="normal", fg_color=ACCENT,
                                     text_color="#ffffff")

    def _finish(self) -> None:
        self._on_done()
