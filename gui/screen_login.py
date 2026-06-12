from __future__ import annotations

import threading
from typing import Callable, Optional

import tkinter as tk

import customtkinter as ctk

from core.auth import BlackboardAuth
from core.state import load_remembered_user, clear_remembered_user
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

    _R = 12   # köşe yarıçapı
    _H = 52

    def __init__(self, parent, text: str, command: Callable) -> None:
        super().__init__(parent, bg=_CARD_BG, bd=0, highlightthickness=0)
        self._cmd = command
        self._base_text = text
        self._prog = 0.0
        self._target = 0.0
        self._anim = False

        self._cv = tk.Canvas(
            self, bg=_CARD_BG, bd=0, highlightthickness=0, height=self._H,
        )
        self._cv.pack(fill="both", expand=True)
        self._cv.bind("<Configure>", lambda _e: self._draw())
        self._cv.bind("<Button-1>", self._on_click)

    # ── drawing ──────────────────────────────────────────────

    @staticmethod
    def _rr(x1: float, y1: float, x2: float, y2: float, r: float) -> list:
        """12 kontrol noktası → smooth=True ile mükemmel yuvarlak dikdörtgen."""
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
        pts = self._rr(0, 0, W, H, R)

        # 1. Düzgün yuvarlak arka plan
        cv.create_polygon(pts, smooth=True, fill=BG_BASE, outline="")

        # 2. Su doluyor (alttan üste)
        if p > 0.001:
            fy = H * (1 - p)
            if fy <= R:
                # Üst köşe bölgesine erişti → tam yuvarlak
                cv.create_polygon(pts, smooth=True, fill=ACCENT, outline="")
            else:
                # Düz üst kenarlı dikdörtgen dolgu
                cv.create_rectangle(0, fy, W, H, fill=ACCENT, outline="")
                # Alt köşeleri yuvarlat: dış kare _CARD_BG, iç çeyrek ACCENT
                cv.create_rectangle(0, H - R, R, H, fill=_CARD_BG, outline="")
                cv.create_arc(0, H - 2*R, 2*R, H, start=180, extent=90,
                              fill=ACCENT, outline="", style="pieslice")
                cv.create_rectangle(W - R, H - R, W, H, fill=_CARD_BG, outline="")
                cv.create_arc(W - 2*R, H - 2*R, W, H, start=270, extent=90,
                              fill=ACCENT, outline="", style="pieslice")

        # 3. Border (aynı smooth polygon, sadece outline)
        cv.create_polygon(pts, smooth=True, fill="", outline=ACCENT if p >= 1.0 else BORDER)

        # 4. Metin
        n = round(p * 10)
        if p >= 1.0:
            txt, col = "Devam Et  →", "#ffffff"
        elif p > 0:
            txt = f"Devam Et  {n} / 10"
            col = "#ffffff" if p >= 0.5 else TEXT_SECONDARY
        else:
            txt, col = self._base_text, TEXT_SECONDARY

        cv.create_text(W // 2, H // 2, text=txt, fill=col, font=("Inter", 14, "bold"))

    # ── animation ────────────────────────────────────────────

    def set_progress(self, pct: float) -> None:
        self._target = max(0.0, min(1.0, pct))
        self._cv.configure(cursor="hand2" if self._target >= 1.0 else "")
        if not self._anim:
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
        pass  # CTkButton çağrılarını absorbe et


class LoginScreen(ctk.CTkFrame):
    """İki adımlı login ekranı: adım-1 öğrenci no → adım-2 şifre."""

    def __init__(
        self,
        master: ctk.CTk,
        on_login_success: Callable,
        on_status: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(master, fg_color=BG_BASE, corner_radius=0)
        self._on_login_success = on_login_success
        self._on_status_ext    = on_status
        self._login_running    = False
        self._auth: Optional[BlackboardAuth] = None
        self._student_no_val   = ""   # adım 1'den adım 2'ye taşınır
        self._remembered       = load_remembered_user()
        self._build_outer()
        self._build_step1()

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
        self._center.grid(row=0, column=0, padx=60)
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
        bottom.grid_columnconfigure(1, weight=1)

        # Sol dot
        self._dot = ctk.CTkLabel(
            bottom, text="●",
            font=("Inter", 10), text_color=DOT_IDLE, width=14,
        )
        self._dot.grid(row=0, column=0, padx=(14, 4), pady=10)

        # Status metni
        self._lbl_status = ctk.CTkLabel(
            bottom, text="Hazır",
            font=("Inter", 11), text_color=TEXT_TERTIARY, anchor="w",
        )
        self._lbl_status.grid(row=0, column=1, sticky="w", pady=10)

        # Güvenlik badge
        ctk.CTkLabel(
            bottom,
            text="🔒 Şifre kaydedilmez",
            font=("Inter", 10), text_color=TEXT_TERTIARY,
        ).grid(row=0, column=2, padx=(0, 14), pady=10)

        # Alt çizgi
        ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0, height=1).grid(
            row=2, column=0, sticky="ew",
        )

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
        vcmd = (self.register(self._validate_no_key), "%P")
        self._entry_no = ctk.CTkEntry(
            card,
            placeholder_text="Örn. 2200000000",
            fg_color=BG_BASE, border_color=BORDER, border_width=1,
            text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_TERTIARY,
            corner_radius=10, font=("Inter", 14), height=50,
            validate="key", validatecommand=vcmd,
        )
        self._entry_no.grid(row=r, column=0, padx=26, sticky="ew"); r += 1
        if self._remembered:
            self._entry_no.insert(0, self._remembered["student_no"])
        self._entry_no.bind("<KeyRelease>", self._on_no_change)
        self._entry_no.bind("<Return>", lambda _: self._validate_step1())
        self._entry_no.focus_set()

        # ── E-posta önizleme (chip) ────────────────
        email_wrap = ctk.CTkFrame(card, fg_color="transparent")
        email_wrap.grid(row=r, column=0, padx=26, pady=(8, 0), sticky="w"); r += 1
        email_wrap.grid_columnconfigure(0, weight=0)

        self._lbl_email = ctk.CTkLabel(
            email_wrap, text="",
            font=("Inter", 10), text_color=ACCENT, anchor="w",
        )
        self._lbl_email.pack(side="left")

        if self._remembered:
            self._on_no_change()

        # ── Devam Et butonu (su dolar gibi) ──────
        self._btn_fill = _FillButton(card, "Devam Et  →", self._validate_step1)
        self._btn_fill.grid(row=r, column=0, padx=26, pady=(22, 26), sticky="ew")

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
            fg_color="transparent", hover_color="transparent",
            text_color=TEXT_TERTIARY, font=("Inter", 10),
            corner_radius=0, height=20, width=0,
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

        # ── Üst satır: Geri + kimlik ──────────────
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, padx=20, pady=(16, 12), sticky="ew")
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            top, text="← Geri",
            command=self._go_back,
            fg_color="transparent", hover_color=BG_HOVER,
            text_color=TEXT_TERTIARY, font=("Inter", 11),
            corner_radius=6, height=28, width=60, anchor="w",
        ).grid(row=0, column=0)

        # Kimlik özeti — sağa yaslanmış kompakt chip
        chip = ctk.CTkFrame(top, fg_color=BG_HOVER, corner_radius=20)
        chip.grid(row=0, column=2, sticky="e")

        av = ctk.CTkFrame(chip, fg_color=ACCENT, corner_radius=12, width=24, height=24)
        av.grid(row=0, column=0, padx=(8, 0), pady=6)
        av.grid_propagate(False)
        ctk.CTkLabel(
            av, text=initial,
            font=("Inter", 10, "bold"), text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            chip, text=display,
            font=("Inter", 11, "bold"), text_color=TEXT_PRIMARY,
        ).grid(row=0, column=1, padx=(6, 10), pady=6)

        # ── Şifre label + entry ───────────────────
        lbl_row = ctk.CTkFrame(card, fg_color="transparent")
        lbl_row.grid(row=1, column=0, padx=24, pady=(0, 6), sticky="w")

        ctk.CTkLabel(
            lbl_row, text="Şifre",
            font=("Inter", 12, "bold"), text_color=TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkLabel(
            lbl_row, text="  opsiyonel",
            font=("Inter", 10), text_color=TEXT_TERTIARY,
        ).pack(side="left")

        self._entry_pwd = ctk.CTkEntry(
            card,
            placeholder_text="Microsoft şifreniz",
            show="•",
            fg_color=BG_BASE, border_color=BORDER, border_width=1,
            text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_TERTIARY,
            corner_radius=10, font=("Inter", 13), height=46,
        )
        self._entry_pwd.grid(row=2, column=0, padx=24, sticky="ew")
        self._entry_pwd.bind("<Return>", lambda _: self._start_login())
        self._entry_pwd.focus_set()

        # ── Kısa hint ─────────────────────────────
        ctk.CTkLabel(
            card,
            text="Opsiyonel — girilirse oturum otomatik başlatılır.",
            font=("Inter", 10), text_color=TEXT_TERTIARY,
        ).grid(row=3, column=0, padx=24, pady=(8, 0))

        # ── Giriş Yap butonu ──────────────────────
        self._btn_main = ctk.CTkButton(
            card,
            text="Giriş Yap  ✓",
            command=self._start_login,
            fg_color=ACCENT, hover_color=_ACCENT_HOVER,
            text_color="#ffffff", corner_radius=10,
            font=("Inter", 13, "bold"), height=48,
        )
        self._btn_main.grid(row=4, column=0, padx=24, pady=(16, 20), sticky="ew")

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
            self._set_status("Öğrenci numaranızı girin", DOT_ERROR)
            self._shake(self._entry_no)
            return
        if len(no) != 10:
            self._set_status("Öğrenci numarası tam 10 haneli olmalıdır", DOT_ERROR)
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
                )
            )
            self.after(0, lambda: self._login_done(student_no, session))
        except Exception as exc:
            self.after(0, lambda: self._login_error(str(exc)))
        finally:
            loop.close()

    def _login_done(self, student_no: str, session) -> None:
        self._login_running = False
        self._spinner_active = False
        self._set_status("Giriş başarılı!", DOT_OK)
        self._on_login_success(student_no, session)

    def _login_error(self, msg: str) -> None:
        self._login_running = False
        self._spinner_active = False
        self._set_status(f"Hata: {msg}", DOT_ERROR)
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

    def _switch_account(self) -> None:
        clear_remembered_user()
        self._remembered = None
        self._build_step1()

    def _validate_no_key(self, new_val: str) -> bool:
        """Entry validasyonu: max 10 rakam."""
        if new_val == "":
            return True
        if len(new_val) > 10:
            return False
        return new_val.isdigit()

    def _on_no_change(self, _event=None) -> None:
        no = self._entry_no.get()
        n = len(no)
        if hasattr(self, "_btn_fill"):
            self._btn_fill.set_progress(n / 10)
        if no:
            self._lbl_email.configure(text=f"→  {no}@stu.istinye.edu.tr")
            self._entry_no.configure(border_color=ACCENT if n == 10 else BORDER)
        else:
            self._lbl_email.configure(text="")
            self._entry_no.configure(border_color=BORDER)

    def _shake(self, widget) -> None:
        widget.configure(border_color=ERROR)
        self.after(800, lambda: widget.configure(border_color=BORDER))

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
