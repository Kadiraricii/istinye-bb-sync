from __future__ import annotations

import threading
from typing import Callable, Optional

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
_ACCENT_HOVER = "#0284c7"
_CARD_BG      = "#071628"   # kart arka planı (BG_ELEVATED ile aynı ama sabit)
_STEP_FG      = "#0a1e38"   # adım geçiş rengi


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
        self._entry_no = ctk.CTkEntry(
            card,
            placeholder_text="Örn. 2200000000",
            fg_color=BG_BASE, border_color=BORDER, border_width=1,
            text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_TERTIARY,
            corner_radius=10, font=("Inter", 14), height=50,
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

        # ── Devam Et butonu ───────────────────────
        self._btn_main = ctk.CTkButton(
            card,
            text="Devam Et  →",
            command=self._validate_step1,
            fg_color=ACCENT, hover_color=_ACCENT_HOVER,
            text_color="#ffffff", corner_radius=10,
            font=("Inter", 14, "bold"), height=52,
        )
        self._btn_main.grid(row=r, column=0, padx=26, pady=(22, 26), sticky="ew")

    def _build_welcome_block(self, card: ctk.CTkFrame, start_row: int) -> None:
        """Hatırlanan kullanıcı için kompakt profil satırı."""
        name = self._remembered.get("name", "")
        no   = self._remembered.get("student_no", "")
        initial = name.strip()[0].upper() if name.strip() else "?"

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.grid(row=start_row, column=0, padx=24, pady=(20, 0), sticky="ew")
        row.grid_columnconfigure(1, weight=1)

        # Avatar
        av = ctk.CTkFrame(row, fg_color=ACCENT, corner_radius=20, width=40, height=40)
        av.grid(row=0, column=0, rowspan=2)
        av.grid_propagate(False)
        ctk.CTkLabel(
            av, text=initial,
            font=("Inter", 17, "bold"), text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            row, text=name,
            font=("Inter", 13, "bold"), text_color=TEXT_PRIMARY, anchor="w",
        ).grid(row=0, column=1, padx=(12, 0), sticky="w")

        ctk.CTkLabel(
            row, text=f"{no}@stu.istinye.edu.tr",
            font=("Inter", 10), text_color=TEXT_TERTIARY, anchor="w",
        ).grid(row=1, column=1, padx=(12, 0), sticky="w")

        ctk.CTkButton(
            row, text="Farklı hesap",
            command=self._switch_account,
            fg_color="transparent", hover_color=BG_HOVER,
            text_color=TEXT_TERTIARY, font=("Inter", 10),
            corner_radius=5, height=26, width=88,
        ).grid(row=0, column=2, rowspan=2)

        # Alt çizgi
        ctk.CTkFrame(card, height=1, fg_color=BORDER).grid(
            row=start_row + 1, column=0, padx=24, pady=(14, 0), sticky="ew",
        )

    # ─────────────────────────────────────────────────────────
    # ADIM 2  — Şifre
    # ─────────────────────────────────────────────────────────

    def _build_step2(self) -> None:
        self._clear_card()
        card = self._card

        no   = self._student_no_val
        name = (self._remembered or {}).get("name", "")
        initial = name.strip()[0].upper() if name.strip() else no[:1].upper() if no else "?"

        # ── Geri butonu ───────────────────────────
        ctk.CTkButton(
            card, text="← Geri",
            command=self._go_back,
            fg_color="transparent", hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY, font=("Inter", 12),
            corner_radius=7, height=30, width=74,
            anchor="w",
        ).grid(row=0, column=0, padx=(18, 0), pady=(14, 0), sticky="w")

        # ── Kimlik özeti ───────────────────────────
        id_row = ctk.CTkFrame(card, fg_color=BG_HOVER, corner_radius=10)
        id_row.grid(row=1, column=0, padx=24, pady=(10, 0), sticky="ew")
        id_row.grid_columnconfigure(1, weight=1)

        av = ctk.CTkFrame(id_row, fg_color=ACCENT, corner_radius=18, width=36, height=36)
        av.grid(row=0, column=0, rowspan=2, padx=(14, 0), pady=12)
        av.grid_propagate(False)
        ctk.CTkLabel(
            av, text=initial,
            font=("Inter", 15, "bold"), text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        display = name if name else no
        ctk.CTkLabel(
            id_row, text=display,
            font=("Inter", 12, "bold"), text_color=TEXT_PRIMARY, anchor="w",
        ).grid(row=0, column=1, padx=(10, 14), pady=(12, 2), sticky="w")

        ctk.CTkLabel(
            id_row, text=f"{no}@stu.istinye.edu.tr",
            font=("Inter", 10), text_color=TEXT_TERTIARY, anchor="w",
        ).grid(row=1, column=1, padx=(10, 14), pady=(0, 12), sticky="w")

        # Yeşil "giriş yapılıyor" dot
        dot = ctk.CTkLabel(
            id_row, text="●",
            font=("Inter", 9), text_color=SUCCESS,
        )
        dot.grid(row=0, column=2, padx=(0, 14), pady=(12, 0))

        # ── Separator ─────────────────────────────
        ctk.CTkFrame(card, height=1, fg_color=BORDER).grid(
            row=2, column=0, padx=24, pady=(16, 0), sticky="ew",
        )

        # ── Şifre label ───────────────────────────
        pwd_hdr = ctk.CTkFrame(card, fg_color="transparent")
        pwd_hdr.grid(row=3, column=0, padx=24, pady=(14, 5), sticky="w")

        ctk.CTkLabel(
            pwd_hdr, text="Şifre",
            font=("Inter", 11, "bold"), text_color=TEXT_SECONDARY,
        ).pack(side="left")

        ctk.CTkLabel(
            pwd_hdr, text="  isteğe bağlı  ",
            font=("Inter", 9, "bold"), text_color=TEXT_TERTIARY,
            fg_color=BG_HOVER, corner_radius=4,
        ).pack(side="left", padx=(6, 0))

        # ── Şifre entry ───────────────────────────
        self._entry_pwd = ctk.CTkEntry(
            card,
            placeholder_text="Microsoft şifrenizi girin",
            show="•",
            fg_color=BG_BASE, border_color=BORDER, border_width=1,
            text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_TERTIARY,
            corner_radius=9, font=FONT_BODY, height=44,
        )
        self._entry_pwd.grid(row=4, column=0, padx=24, sticky="ew")
        self._entry_pwd.bind("<Return>", lambda _: self._start_login())
        self._entry_pwd.focus_set()

        # ── Bilgi notu ────────────────────────────
        note = ctk.CTkFrame(card, fg_color="transparent")
        note.grid(row=5, column=0, padx=24, pady=(10, 0), sticky="ew")
        note.grid_columnconfigure(1, weight=1)

        ctk.CTkFrame(note, fg_color=ACCENT, width=2, corner_radius=2).grid(
            row=0, column=0, sticky="ns", padx=(0, 10),
        )
        ctk.CTkLabel(
            note,
            text=(
                "Girilirse Blackboard oturumunuz otomatik açılır.\n"
                "Boş bırakırsanız tarayıcıda manuel giriş yapmanız gerekir."
            ),
            font=("Inter", 10), text_color=TEXT_TERTIARY,
            justify="left", anchor="w", wraplength=380,
        ).grid(row=0, column=1, sticky="w")

        # ── Separator ─────────────────────────────
        ctk.CTkFrame(card, height=1, fg_color=BORDER).grid(
            row=6, column=0, padx=24, pady=(14, 0), sticky="ew",
        )

        # ── Giriş Yap butonu ──────────────────────
        self._btn_main = ctk.CTkButton(
            card,
            text="Giriş Yap  ✓",
            command=self._start_login,
            fg_color=ACCENT, hover_color=_ACCENT_HOVER,
            text_color="#ffffff", corner_radius=9,
            font=("Inter", 13, "bold"), height=46,
        )
        self._btn_main.grid(row=7, column=0, padx=24, pady=(14, 10), sticky="ew")

        # ── Tarayıcıyı Göster (login sırasında) ──
        self._btn_show_browser = ctk.CTkButton(
            card,
            text="🔍  Tarayıcıyı Göster",
            command=self._show_browser,
            fg_color="transparent", hover_color=BG_HOVER,
            text_color=ACCENT, corner_radius=9,
            font=("Inter", 11), height=34,
            border_width=1, border_color=BORDER,
        )
        self._btn_show_browser.grid(row=8, column=0, padx=24, pady=(0, 18), sticky="ew")
        self._btn_show_browser.grid_remove()

    # ─────────────────────────────────────────────────────────
    # ADıM GEÇİŞLERİ
    # ─────────────────────────────────────────────────────────

    def _validate_step1(self) -> None:
        no = self._entry_no.get().strip()
        if not no:
            self._set_status("Öğrenci numaranızı girin", DOT_ERROR)
            self._shake(self._entry_no)
            return
        if not no.isdigit():
            self._set_status("Numara yalnızca rakam içerebilir", DOT_ERROR)
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
        self._entry_pwd.delete(0, "end")

        self._login_running = True
        self._btn_main.configure(state="disabled", text="⏳  Bağlanıyor...")
        self._btn_show_browser.grid()
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
        self._btn_main.configure(state="normal", text="Giriş Yap  ✓")
        self._btn_show_browser.grid_remove()
        self._set_status("Giriş başarılı!", DOT_OK)
        self._on_login_success(student_no, session)

    def _login_error(self, msg: str) -> None:
        self._login_running = False
        self._btn_main.configure(state="normal", text="Giriş Yap  ✓")
        self._btn_show_browser.grid_remove()
        self._set_status(f"Hata: {msg}", DOT_ERROR)

    def _handle_browser_closed(self) -> None:
        self.after(0, lambda: self._set_status(
            "Tarayıcı kapatıldı — tekrar başlatmak için butona tıklayın", DOT_ERROR,
        ))
        self.after(0, lambda: self._btn_main.configure(
            state="normal", text="Giriş Yap  ✓",
        ))
        self.after(0, self._btn_show_browser.grid_remove)
        self._login_running = False

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

    def _on_no_change(self, _event=None) -> None:
        no = self._entry_no.get().strip()
        if no:
            self._lbl_email.configure(text=f"→  {no}@stu.istinye.edu.tr")
            self._entry_no.configure(
                border_color=ACCENT if no.isdigit() else ERROR,
            )
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
        if self._on_status_ext:
            self._on_status_ext(msg)
