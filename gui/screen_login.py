from __future__ import annotations

import threading
from typing import Callable, Optional

import tkinter as tk

import customtkinter as ctk

from core.auth import BlackboardAuth
from core.state import load_remembered_user, clear_remembered_user, load_cookies, load_manifest, delete_cookies
from gui.theme import (
    ACCENT, BG_BASE, BG_ELEVATED, BG_HOVER, BORDER,
    DOT_BUSY, DOT_ERROR, DOT_IDLE, DOT_OK,
    FONT_BODY, FONT_SMALL,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY,
    ERROR, SUCCESS,
)

# ── Renk sabitleri ───────────────────────────────────────────
_ACCENT_HOVER = "#059669"   # emerald-600 hover
_CARD_BG      = "#0d1120"   # kart arka planı (BG_ELEVATED)
_STEP_FG      = "#111830"   # adım geçiş rengi


class _FillButton(tk.Frame):
    """Bardağa su dolar gibi alttan dolup boşalan devam butonu."""

    _R = 10   # köşe yarıçapı
    _H = 50   # sabit yükseklik

    def __init__(self, parent, text: str, command: Callable) -> None:
        super().__init__(parent, bg=_CARD_BG, bd=0, highlightthickness=0,
                         height=self._H)
        self.pack_propagate(False)
        self._cmd = command
        self._base_text = text
        self._prog = 0.0
        self._target = 0.0
        self._anim = False
        self._fill_color = ACCENT

        self._cv = tk.Canvas(
            self, bg=_CARD_BG, bd=0, highlightthickness=0,
        )
        self._cv.pack(fill="both", expand=True)
        self._cv.bind("<Configure>", lambda _e: self._draw())
        self._cv.bind("<Button-1>", self._on_click)

    # ── drawing ──────────────────────────────────────────────

    @staticmethod
    def _rr(x1: float, y1: float, x2: float, y2: float, r: float) -> list:
        return [
            x1+r, y1,   x2-r, y1,
            x2,   y1,   x2,   y1+r,
            x2,   y2-r, x2,   y2,
            x2-r, y2,   x1+r, y2,
            x1,   y2,   x1,   y2-r,
            x1,   y1+r, x1,   y1,
        ]

    def _draw(self) -> None:
        cv = self._cv
        W, H = cv.winfo_width(), cv.winfo_height()
        if W <= 1:
            return
        cv.delete("all")
        R = self._R
        p = self._prog
        bg_pts = self._rr(0, 0, W, H, R)

        # 1. Yuvarlak buton arka planı
        cv.create_polygon(bg_pts, smooth=True, fill=BG_BASE, outline="")

        # 2. Su doluyor — fill_color ile tam şekil çiz, sonra üst kısmı maskele
        fc = self._fill_color
        if p > 0.001:
            fy = H * (1 - p)
            # Her zaman tam şekli doldur, sonra boş kısmı maskele
            cv.create_polygon(bg_pts, smooth=True, fill=fc, outline="")
            if fy > 0.5:
                top_mask = [
                    R,    0,    W-R,  0,
                    W,    0,    W,    R,
                    W,    fy,   W,    fy,
                    0,    fy,   0,    fy,
                    0,    R,    0,    0,
                ]
                cv.create_polygon(top_mask, smooth=True, fill=BG_BASE, outline="")

        # 3. Border
        brd = fc if p >= 1.0 else BORDER
        cv.create_polygon(bg_pts, smooth=True, fill="", outline=brd)

        # 4. Metin
        n = round(p * 10)
        if p >= 1.0:
            txt, col = "Devam Et  →", "#ffffff"
        elif p > 0:
            txt = f"Devam Et  {n}/10"
            col = "#ffffff" if p >= 0.5 else TEXT_SECONDARY
        else:
            txt, col = self._base_text, TEXT_SECONDARY

        cv.create_text(W // 2, H // 2, text=txt, fill=col,
                       font=("Inter", 14, "bold"))

    # ── animation ────────────────────────────────────────────

    def set_fill_color(self, color: str) -> None:
        self._fill_color = color
        self._draw()

    def set_progress(self, pct: float, instant: bool = False) -> None:
        self._target = max(0.0, min(1.0, pct))
        self._cv.configure(cursor="hand2" if self._target >= 1.0 else "")
        if instant:
            self._prog = self._target
            self._anim = False
            self._draw()
        elif not self._anim:
            self._tick()

    def _tick(self) -> None:
        diff = self._target - self._prog
        if abs(diff) < 0.005:
            self._prog = self._target
            self._anim = False
            self._draw()
            return
        self._anim = True
        self._prog += diff * 0.28
        self._draw()
        self._cv.after(16, self._tick)

    def _on_click(self, _event) -> None:
        if self._prog >= 1.0:
            self._cmd()

    def configure(self, **_kw) -> None:
        pass


class LoginScreen(ctk.CTkFrame):
    """İki adımlı login ekranı: adım-1 öğrenci no → adım-2 şifre."""

    def __init__(
        self,
        master: ctk.CTk,
        on_login_success: Callable,
        on_status: Optional[Callable[[str], None]] = None,
        on_quick_resume: Optional[Callable] = None,
        on_show_onboarding: Optional[Callable] = None,
    ) -> None:
        super().__init__(master, fg_color=BG_BASE, corner_radius=0)
        self._on_login_success    = on_login_success
        self._on_status_ext       = on_status
        self._on_quick_resume     = on_quick_resume
        self._on_show_onboarding  = on_show_onboarding
        self._login_running    = False
        self._auth: Optional[BlackboardAuth] = None
        self._student_no_val   = ""
        self._remembered       = load_remembered_user()
        self._saved_session    = self._check_saved_session()
        self._build_outer()
        self._build_step1()

    # ─────────────────────────────────────────────────────────
    # KAYITLI OTURUM KONTROLÜ
    # ─────────────────────────────────────────────────────────

    def _check_saved_session(self):
        """Cookie dosyası + manifest varsa (session, saved_at) döner, yoksa None."""
        from datetime import datetime, timezone
        if not load_manifest():
            return None
        result = load_cookies()
        if not result:
            return None
        session, saved_at = result
        age_hours = (datetime.now() - saved_at).total_seconds() / 3600
        if age_hours > 1.0:
            return None
        return session, saved_at

    # ─────────────────────────────────────────────────────────
    # DIŞ KABUK  — logo / başlık / kart referansı / status
    # ─────────────────────────────────────────────────────────

    def _build_outer(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Üst accent şeridi
        ctk.CTkFrame(self, fg_color=ACCENT, corner_radius=0, height=3).grid(
            row=0, column=0, sticky="ew",
        )

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._center = ctk.CTkFrame(body, fg_color="transparent")
        self._center.grid(row=0, column=0, padx=10)
        self._center.grid_columnconfigure(0, weight=1)

        r = 0

        # Logo
        logo_wrap = ctk.CTkFrame(self._center, fg_color="transparent")
        logo_wrap.grid(row=r, column=0, pady=(0, 10)); r += 1

        logo_outer = ctk.CTkFrame(
            logo_wrap, fg_color=BORDER, corner_radius=18, width=68, height=68,
        )
        logo_outer.pack(anchor="center")
        logo_outer.grid_propagate(False)

        logo_inner = ctk.CTkFrame(
            logo_outer, fg_color=ACCENT, corner_radius=14, width=54, height=54,
        )
        logo_inner.place(relx=0.5, rely=0.5, anchor="center")
        logo_inner.grid_propagate(False)
        ctk.CTkLabel(
            logo_inner, text="B",
            font=("Inter", 26, "bold"), text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Başlık
        ctk.CTkLabel(
            self._center, text="Blackboard Sync",
            font=("Inter", 26, "bold"), text_color=TEXT_PRIMARY,
        ).grid(row=r, column=0, pady=(0, 3)); r += 1

        ctk.CTkLabel(
            self._center,
            text="Istinye Üniversitesi  ·  Ders Materyali İndirici",
            font=FONT_SMALL, text_color=TEXT_TERTIARY,
        ).grid(row=r, column=0, pady=(0, 22)); r += 1

        # ── Kart (içeriği adım adım değişir) ────
        self._card = ctk.CTkFrame(
            self._center,
            fg_color=_CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=BORDER,
        )
        self._card.grid(row=r, column=0, sticky="ew"); r += 1
        self._card.grid_columnconfigure(0, weight=1)

        # ── Status + güvenlik notu ───────────────
        bottom = ctk.CTkFrame(
            self._center,
            fg_color=BG_ELEVATED,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        bottom.grid(row=r, column=0, sticky="ew", pady=(16, 0)); r += 1
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=0)

        # Sol: güvenlik
        ctk.CTkLabel(
            bottom, text="🔒 Şifre kaydedilmez",
            font=("Inter", 10), text_color=TEXT_TERTIARY,
        ).grid(row=0, column=0, padx=(14, 0), pady=10, sticky="w")

        # Sağ: Nasıl Çalışır
        if self._on_show_onboarding:
            ctk.CTkButton(
                bottom,
                text="ℹ  Nasıl Çalışır?",
                command=self._on_show_onboarding,
                fg_color="#052e1c", hover_color="#063d25",
                text_color=ACCENT, border_color=ACCENT, border_width=1,
                corner_radius=8, font=("Inter", 10, "bold"),
                width=120, height=26,
            ).grid(row=0, column=1, padx=(0, 12), pady=10, sticky="e")

        # Dot + status — _build_step1 içinde label yanında oluşturulur
        self._dot        = None
        self._lbl_status = None

        # Telif + kullanım notu
        ctk.CTkLabel(
            self,
            text="Kadir Arıcı · 2026 · Kişisel kullanım amaçlı. Akademik dürüstlük kurallarına uygun kullanın.",
            font=("Inter", 12), text_color="#2e4a6a",
        ).grid(row=2, column=0, pady=(4, 8))

    # ─────────────────────────────────────────────────────────
    # ADIM 1  — Öğrenci Numarası
    # ─────────────────────────────────────────────────────────

    def _build_step1(self) -> None:
        self._clear_card()
        card = self._card

        r = 0
        if self._remembered:
            self._build_welcome_block(card, start_row=0)
            r = 3

        # ── Label ─────────────────────────────────
        ctk.CTkLabel(
            card, text="Öğrenci Numarası",
            font=("Inter", 13, "bold"), text_color=TEXT_PRIMARY, anchor="w",
        ).grid(row=r, column=0, padx=26, pady=(26, 7), sticky="w"); r += 1

        # ── Entry ─────────────────────────────────
        self._entry_no = ctk.CTkEntry(
            card,
            placeholder_text="Örn. 2200000000",
            fg_color=BG_BASE, border_color=BORDER, border_width=1,
            text_color=TEXT_PRIMARY, placeholder_text_color="#8aaecf",
            corner_radius=10, font=("Inter", 14), height=50,
        )
        self._entry_no.grid(row=r, column=0, padx=26, sticky="ew"); r += 1
        if self._remembered:
            self._entry_no.insert(0, self._remembered["student_no"])
        self._entry_no.bind("<KeyRelease>", self._on_no_change)
        self._entry_no.bind("<Return>", lambda _: self._validate_step1())
        self._entry_no.focus_set()

        # ── E-posta önizleme ──────────────────────
        self._lbl_email = ctk.CTkLabel(
            card, text="",
            font=("Inter", 11), text_color=ACCENT, anchor="w",
        )
        self._lbl_email.grid(row=r, column=0, padx=26, pady=(6, 0), sticky="w"); r += 1

        # ── Devam Et butonu (su dolar gibi) ──────
        self._btn_fill = _FillButton(card, "Devam Et  →", self._validate_step1)
        self._btn_fill.grid(row=r, column=0, padx=26, pady=(10, 26), sticky="ew")

        if self._remembered:
            no_pre = self._remembered["student_no"]
            self._lbl_email.configure(text=f"→  {no_pre}@stu.istinye.edu.tr")
            self._entry_no.configure(border_color=ACCENT)
            self._btn_fill.set_progress(1.0, instant=True)

        # ── Hızlı Devam — kaydedilmiş oturum varsa ───────────
        if self._saved_session and self._on_quick_resume:
            session, saved_at = self._saved_session
            age_m = int((
                __import__("datetime").datetime.now() - saved_at
            ).total_seconds() / 60)
            age_str = f"{age_m}dk önce" if age_m < 60 else f"{age_m // 60}sa önce"

            sep = tk.Frame(card, bg=_CARD_BG, height=1)
            sep.grid(row=r + 1, column=0, padx=26, sticky="ew")
            tk.Frame(sep, bg=BORDER, height=1).pack(fill="x")

            resume_btn = tk.Frame(
                card, bg=_CARD_BG, cursor="hand2",
            )
            resume_btn.grid(row=r + 2, column=0, padx=26, pady=(8, 20), sticky="ew")
            resume_btn.grid_columnconfigure(1, weight=1)

            tk.Label(
                resume_btn, text="⚡", bg=_CARD_BG,
                font=("Inter", 14), fg=ACCENT,
            ).grid(row=0, column=0, padx=(0, 8))

            info_col = tk.Frame(resume_btn, bg=_CARD_BG)
            info_col.grid(row=0, column=1, sticky="w")
            tk.Label(
                info_col, text="Önceki oturumla devam et",
                bg=_CARD_BG, font=("Inter", 12, "bold"), fg=TEXT_PRIMARY,
            ).pack(anchor="w")
            tk.Label(
                info_col, text=f"Kaydedilmiş oturum · {age_str}",
                bg=_CARD_BG, font=("Inter", 10), fg=TEXT_TERTIARY,
            ).pack(anchor="w")

            def _do_delete():
                delete_cookies()
                self._saved_session = None
                self._build_step1()

            del_btn = tk.Label(
                resume_btn, text="×", bg=_CARD_BG,
                font=("Inter", 16), fg=TEXT_TERTIARY, cursor="hand2",
                padx=4,
            )
            del_btn.grid(row=0, column=2, padx=(4, 0))
            del_btn.bind("<Button-1>", lambda _: _do_delete())

            def _bind_resume(w, skip):
                if w in skip:
                    return
                w.bind("<Button-1>", lambda _: self._do_quick_resume(session))
                for ch in w.winfo_children():
                    _bind_resume(ch, skip)
            _bind_resume(resume_btn, skip={del_btn})

    def _build_welcome_block(self, card: ctk.CTkFrame, start_row: int) -> None:
        """Hatırlanan kullanıcı için tıklanabilir profil kartı."""
        name    = self._remembered.get("name", "")
        no      = self._remembered.get("student_no", "")
        initial = name.strip()[0].upper() if name.strip() else "?"

        def _bind(w) -> None:
            w.configure(cursor="hand2")
            w.bind("<Button-1>", lambda _: self._quick_login_remembered())

        # ── Tıklanabilir profil kartı ──────────────
        row = ctk.CTkFrame(
            card, fg_color=BG_HOVER, corner_radius=10,
            border_width=1, border_color=BORDER,
        )
        row.grid(row=start_row, column=0, padx=24, pady=(20, 0), sticky="ew")
        row.grid_columnconfigure(1, weight=1)
        _bind(row)

        av = ctk.CTkFrame(row, fg_color=ACCENT, corner_radius=20, width=40, height=40)
        av.grid(row=0, column=0, rowspan=2, padx=(14, 0), pady=12)
        av.grid_propagate(False)
        av_lbl = ctk.CTkLabel(av, text=initial, font=("Inter", 17, "bold"), text_color="#ffffff")
        av_lbl.place(relx=0.5, rely=0.5, anchor="center")
        _bind(av); _bind(av_lbl)

        name_lbl = ctk.CTkLabel(row, text=name, font=("Inter", 13, "bold"), text_color=TEXT_PRIMARY, anchor="w")
        name_lbl.grid(row=0, column=1, padx=(12, 0), pady=(12, 2), sticky="w")
        _bind(name_lbl)

        email_lbl = ctk.CTkLabel(row, text=f"{no}@stu.istinye.edu.tr", font=("Inter", 10), text_color=TEXT_TERTIARY, anchor="w")
        email_lbl.grid(row=1, column=1, padx=(12, 0), pady=(0, 12), sticky="w")
        _bind(email_lbl)

        # Şevron — kartın sağında, tıklanabilirliği ifade eder
        chev = ctk.CTkLabel(row, text="›", font=("Inter", 20), text_color=TEXT_TERTIARY)
        chev.grid(row=0, column=2, rowspan=2, padx=(0, 16))
        _bind(chev)

        # ── "Farklı hesap" — kartın altında ayrı link ──
        switch_row = ctk.CTkFrame(card, fg_color="transparent")
        switch_row.grid(row=start_row + 1, column=0, pady=(6, 0), sticky="e", padx=24)

        ctk.CTkButton(
            switch_row, text="Farklı hesap kullan",
            command=self._switch_account,
            fg_color="transparent", hover_color=BG_HOVER,
            text_color=TEXT_TERTIARY, font=("Inter", 10),
            corner_radius=4, height=20, width=0,
        ).pack(side="right")

        # Alt çizgi
        ctk.CTkFrame(card, height=1, fg_color=BORDER).grid(
            row=start_row + 2, column=0, padx=24, pady=(8, 0), sticky="ew",
        )

    # ─────────────────────────────────────────────────────────
    # ADIM 2  — Şifre
    # ─────────────────────────────────────────────────────────

    def _build_step2(self) -> None:
        self._clear_card()
        card = self._card

        no      = self._student_no_val
        name    = (self._remembered or {}).get("name", "")
        initial = name.strip()[0].upper() if name.strip() else no[:1].upper() if no else "?"
        display = name if name else no

        # ── Geri butonu ───────────────────────────
        ctk.CTkButton(
            card, text="← Geri",
            command=self._go_back,
            fg_color="transparent", hover_color=BG_HOVER,
            text_color=TEXT_TERTIARY, font=("Inter", 11),
            corner_radius=6, height=28, width=70, anchor="w",
        ).grid(row=0, column=0, padx=16, pady=(14, 0), sticky="w")

        # ── Kimlik avatar + isim ──────────────────
        id_frame = ctk.CTkFrame(card, fg_color="transparent")
        id_frame.grid(row=1, column=0, padx=28, pady=(10, 0), sticky="w")

        av = ctk.CTkFrame(id_frame, fg_color=ACCENT, corner_radius=20, width=40, height=40)
        av.pack(side="left")
        av.pack_propagate(False)
        ctk.CTkLabel(
            av, text=initial,
            font=("Inter", 16, "bold"), text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        name_col = ctk.CTkFrame(id_frame, fg_color="transparent")
        name_col.pack(side="left", padx=(12, 0))
        ctk.CTkLabel(
            name_col, text=display,
            font=("Inter", 15, "bold"), text_color=TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            name_col, text=f"{no}@stu.istinye.edu.tr",
            font=("Inter", 11), text_color=TEXT_TERTIARY,
            anchor="w",
        ).pack(anchor="w")

        # ── Şifre label ───────────────────────────
        ctk.CTkLabel(
            card, text="Microsoft Şifresi",
            font=("Inter", 13, "bold"), text_color=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=2, column=0, padx=28, pady=(22, 6), sticky="w")

        # ── Şifre entry ───────────────────────────
        self._entry_pwd = ctk.CTkEntry(
            card,
            placeholder_text="Şifrenizi girin",
            show="•",
            fg_color=BG_BASE, border_color=BORDER, border_width=1,
            text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_TERTIARY,
            corner_radius=10, font=("Inter", 14), height=50,
        )
        pwd_error = getattr(self, "_pwd_error", None)
        self._pwd_error = None
        border = ERROR if pwd_error else BORDER
        self._entry_pwd.configure(border_color=border)
        self._entry_pwd.grid(row=3, column=0, padx=28, sticky="ew")
        self._entry_pwd.bind("<Return>", lambda _: self._start_login())
        self._entry_pwd.focus_set()

        if pwd_error:
            ctk.CTkLabel(
                card,
                text=f"⚠  {pwd_error} — lütfen tekrar deneyin",
                font=("Inter", 11), text_color=ERROR, anchor="w",
            ).grid(row=4, column=0, padx=30, pady=(5, 0), sticky="w")

        # ── Opsiyonel bilgi kutusu ────────────────
        info_box = ctk.CTkFrame(
            card,
            fg_color=BG_HOVER, corner_radius=8,
            border_width=1, border_color=BORDER,
        )
        info_box.grid(row=5, column=0, padx=28, pady=(12, 0), sticky="ew")
        info_box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            info_box, text="ⓘ",
            font=("Inter", 15), text_color=TEXT_SECONDARY,
        ).grid(row=0, column=0, padx=(14, 0), pady=12, sticky="n")

        ctk.CTkLabel(
            info_box,
            text="Şifre opsiyoneldir. Girerseniz giriş otomatik tamamlanır;\ngirmezseniz tarayıcı açılır ve siz manuel giriş yaparsınız.",
            font=("Inter", 11), text_color=TEXT_SECONDARY,
            anchor="w", justify="left", wraplength=310,
        ).grid(row=0, column=1, padx=(10, 14), pady=12, sticky="w")

        # ── Giriş Yap butonu ──────────────────────
        self._btn_main = ctk.CTkButton(
            card,
            text="Giriş Yap  →",
            command=self._start_login,
            fg_color=ACCENT, hover_color=_ACCENT_HOVER,
            text_color="#ffffff", corner_radius=10,
            font=("Inter", 14, "bold"), height=50,
        )
        self._btn_main.grid(row=6, column=0, padx=28, pady=(18, 24), sticky="ew")

    # ─────────────────────────────────────────────────────────
    # BAĞLANMA EKRANI
    # ─────────────────────────────────────────────────────────

    def _build_connecting(self) -> None:
        """Giriş sırasında gösterilen animasyonlu bekleme ekranı."""
        self._clear_card()
        self._spinner_active = True
        self._spinner_step   = 0
        card = self._card
        card.grid_columnconfigure(0, weight=1)

        # Dots satırı
        dots_row = ctk.CTkFrame(card, fg_color="transparent")
        dots_row.grid(row=0, column=0, pady=(32, 0))
        self._spinner_dots = []
        for i in range(3):
            d = ctk.CTkLabel(dots_row, text="●", font=("Inter", 18), text_color=TEXT_TERTIARY)
            d.grid(row=0, column=i, padx=5)
            self._spinner_dots.append(d)

        ctk.CTkLabel(
            card, text="Giriş Yapılıyor",
            font=("Inter", 17, "bold"), text_color=TEXT_PRIMARY,
        ).grid(row=1, column=0, pady=(14, 4))

        self._lbl_connecting = ctk.CTkLabel(
            card, text="Tarayıcı başlatılıyor...",
            font=("Inter", 11), text_color=TEXT_SECONDARY,
        )
        self._lbl_connecting.grid(row=2, column=0, pady=(0, 24))

        self._btn_show_browser = ctk.CTkButton(
            card,
            text="Tarayıcıyı Göster  →",
            command=self._show_browser,
            fg_color="transparent", hover_color=BG_HOVER,
            text_color=ACCENT, corner_radius=9,
            font=("Inter", 11), height=36,
            border_width=1, border_color=BORDER,
        )
        self._btn_show_browser.grid(row=3, column=0, padx=24, pady=(0, 30), sticky="ew")

        self._animate_spinner()

    def _animate_spinner(self) -> None:
        if not self._spinner_active:
            return
        if not hasattr(self, "_spinner_dots") or not self._spinner_dots:
            return
        step = self._spinner_step % 3
        for i, dot in enumerate(self._spinner_dots):
            dot.configure(text_color=ACCENT if i == step else TEXT_TERTIARY)
        self._spinner_step += 1
        self.after(380, self._animate_spinner)

    # ─────────────────────────────────────────────────────────
    # ADıM GEÇİŞLERİ
    # ─────────────────────────────────────────────────────────

    def _quick_login_remembered(self) -> None:
        """Profil kartına tıklanınca direkt şifre adımına geç."""
        self._student_no_val = self._remembered["student_no"]
        self._card.configure(border_color=ACCENT)
        self.after(120, self._card_flash_done)

    def _validate_step1(self) -> None:
        no = self._entry_no.get().strip()
        if not no:
            self._lbl_email.configure(text="Öğrenci numaranızı girin", text_color=ERROR)
            self._shake(self._entry_no)
            return
        if not no.isdigit():
            self._lbl_email.configure(text="Sadece sayı kabul ediliyor", text_color=ERROR)
            self._shake(self._entry_no)
            return
        if len(no) != 10:
            diff = len(no) - 10
            msg = f"Tam 10 rakam gerekli — {diff} fazla" if diff > 0 else f"Tam 10 rakam gerekli — şu an {len(no)}"
            self._lbl_email.configure(text=msg, text_color=ERROR)
            self._shake(self._entry_no)
            return
        self._student_no_val = no
        # Kısa border flash geçiş efekti
        self._card.configure(border_color=ACCENT)
        self.after(120, self._card_flash_done)

    def _card_flash_done(self) -> None:
        self._card.configure(border_color=BORDER)
        self.after(60, self._build_step2)

    def _go_back(self) -> None:
        self._card.configure(border_color=ACCENT)
        self.after(120, lambda: [
            self._card.configure(border_color=BORDER),
            self.after(60, self._build_step1),
        ])
        self._set_status("Hazır", DOT_IDLE)

    # ─────────────────────────────────────────────────────────
    # AKSIYON
    # ─────────────────────────────────────────────────────────

    def _do_quick_resume(self, session) -> None:
        if self._on_quick_resume:
            self._on_quick_resume(session)

    def _start_login(self) -> None:
        if self._login_running:
            return
        pwd = self._entry_pwd.get() or None
        self._login_running = True
        self._build_connecting()
        self._set_status("Tarayıcı başlatılıyor...", DOT_BUSY)

        threading.Thread(
            target=self._run_login,
            args=(self._student_no_val, pwd),
            daemon=True,
        ).start()


    def _show_browser(self) -> None:
        if self._auth:
            self._auth.bring_to_front_sync()

    def _run_login(self, student_no: str, password: Optional[str]) -> None:
        import asyncio
        self._auth = BlackboardAuth()
        loop = asyncio.new_event_loop()
        try:
            session = loop.run_until_complete(
                self._auth.login(
                    student_no,
                    password=password,
                    on_status=self._set_status_thread,
                    on_browser_closed=self._handle_browser_closed,
                    on_password_error=self._handle_password_error,
                )
            )
            self.after(0, lambda: self._login_done(student_no, session))
        except Exception as exc:
            msg = str(exc)
            self.after(0, lambda m=msg: self._login_error(m))
        finally:
            loop.close()

    def _login_done(self, student_no: str, session) -> None:
        self._login_running = False
        self._spinner_active = False
        self._set_status("Giriş başarılı!", DOT_OK)
        self._on_login_success(student_no, session)

    def _handle_password_error(self) -> None:
        """Auth thread'den çağrılır — tarayıcı açık kalır, sadece GUI güncellenir."""
        self.after(0, self._show_password_error_on_connecting)

    def _show_password_error_on_connecting(self) -> None:
        lbl = getattr(self, "_lbl_connecting", None)
        if lbl and lbl.winfo_exists():
            lbl.configure(
                text="Hatalı şifre — tarayıcıda doğru şifreyi girin",
                text_color=ERROR,
            )
        self._set_status("Hatalı şifre — tarayıcıda doğru şifreyi girin", DOT_ERROR)
        # Tarayıcıyı göster butonu varsa öne çıkar
        btn = getattr(self, "_btn_show_browser", None)
        if btn and btn.winfo_exists():
            btn.configure(text="Tarayıcıyı Göster  → (şifreyi düzelt)")

    def _login_error(self, msg: str) -> None:
        self._login_running = False
        self._spinner_active = False
        self._pwd_error = msg if "Hatalı şifre" in msg else None
        self._set_status(msg, DOT_ERROR)
        self._build_step2()

    def _handle_browser_closed(self) -> None:
        self._login_running = False
        self._spinner_active = False
        self.after(0, lambda: self._set_status(
            "Tarayıcı kapatıldı — tekrar deneyin", DOT_ERROR,
        ))
        self.after(0, self._build_step2)

    # ─────────────────────────────────────────────────────────
    # YARDIMCILAR
    # ─────────────────────────────────────────────────────────

    def _clear_card(self) -> None:
        for w in self._card.winfo_children():
            w.destroy()
        tk.Frame(self._card, width=460, height=1, bg=_CARD_BG).grid(row=99, column=0)

    def _switch_account(self) -> None:
        clear_remembered_user()
        self._remembered = None
        self._build_step1()

    def _on_no_change(self, _event=None) -> None:
        no    = self._entry_no.get()
        n     = len(no)
        valid = no.isdigit() and n == 10
        dirty = bool(no) and not no.isdigit()

        # Border
        if dirty:
            self._entry_no.configure(border_color=ERROR)
        elif valid:
            self._entry_no.configure(border_color=ACCENT)
        else:
            self._entry_no.configure(border_color=BORDER)

        # Hint — yazarken hata mesajı yok
        if valid:
            self._lbl_email.configure(
                text=f"→  {no}@stu.istinye.edu.tr", text_color=ACCENT,
            )
        elif no:
            self._lbl_email.configure(
                text=f"{n} / 10", text_color=TEXT_TERTIARY,
            )
        else:
            self._lbl_email.configure(text="", text_color=ACCENT)

        # Buton: ilerleme = karakter sayısı/10 (max 10), renk = geçerliliğe göre
        if hasattr(self, "_btn_fill"):
            self._btn_fill.set_fill_color(ACCENT if not dirty else ERROR)
            self._btn_fill.set_progress(min(n, 10) / 10)

    def _shake(self, widget) -> None:
        widget.configure(border_color=ERROR)
        self.after(800, lambda: widget.configure(border_color=BORDER))

    def show_syncing(self) -> None:
        """Login bitti, dersler yüklenirken spinner'ı yeniden canlandır."""
        if hasattr(self, "_lbl_connecting") and self._lbl_connecting.winfo_exists():
            self._lbl_connecting.configure(text="Dersler yükleniyor...")
        self._set_status("Dersler yükleniyor...", DOT_BUSY)
        self._spinner_active = True
        self._animate_spinner()

    def set_sync_total(self, total: int) -> None:
        self._sync_done  = 0
        self._sync_total = total
        self._sync_eta   = 0
        self._sync_tick_running = False
        msg = f"0 / {total} ders tarandı"
        if hasattr(self, "_lbl_connecting") and self._lbl_connecting.winfo_exists():
            self._lbl_connecting.configure(text=msg)
        self._set_status(f"{total} ders bulundu, taranıyor...", DOT_BUSY)

    def update_sync_progress(self, done: int, total: int, eta_s: int = 0) -> None:
        self._sync_done  = done
        self._sync_total = total
        self._sync_eta   = eta_s
        if not getattr(self, "_sync_tick_running", False):
            self._sync_tick_running = True
            self._tick_sync()

    def _tick_sync(self) -> None:
        lbl = getattr(self, "_lbl_connecting", None)
        if lbl is None or not lbl.winfo_exists():
            self._sync_tick_running = False
            return
        done  = getattr(self, "_sync_done",  0)
        total = getattr(self, "_sync_total", 0)
        eta   = getattr(self, "_sync_eta",   0)
        eta_str = f" · ~{eta}s kaldı" if eta > 2 else ""
        msg = f"{done} / {total} ders tarandı{eta_str}"
        lbl.configure(text=msg)
        self._lbl_status.configure(text=msg, text_color=DOT_BUSY)
        self._dot.configure(text_color=DOT_BUSY)
        if eta > 0:
            self._sync_eta = eta - 1
            self.after(1000, self._tick_sync)
        else:
            self._sync_tick_running = False

    def _set_status_thread(self, msg: str) -> None:
        self.after(0, lambda m=msg: self._set_status(m, DOT_BUSY))

    def _set_status(self, msg: str, color: str = DOT_IDLE) -> None:
        self._lbl_status.configure(text=msg, text_color=color)
        self._dot.configure(text_color=color)
        lbl = getattr(self, "_lbl_connecting", None)
        if lbl and lbl.winfo_exists():
            lbl.configure(text=msg, text_color=color)
        if self._on_status_ext:
            self._on_status_ext(msg)
