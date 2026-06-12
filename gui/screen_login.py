from __future__ import annotations

import threading
from typing import Callable, Optional

import customtkinter as ctk

from core.auth import BlackboardAuth
from gui.theme import (
    ACCENT, BG_BASE, BG_ELEVATED, BG_HOVER, BORDER,
    DOT_BUSY, DOT_ERROR, DOT_IDLE, DOT_OK,
    FONT_BODY, FONT_SMALL,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY,
    SUCCESS, ERROR, WARNING,
)


class LoginScreen(ctk.CTkFrame):
    """Login ekranı."""

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
        self._build()

    # ── Layout ────────────────────────────────────────────────

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Üst accent şeridi ────────────────────
        ctk.CTkFrame(self, fg_color=ACCENT, corner_radius=0, height=3).grid(
            row=0, column=0, sticky="ew",
        )

        # ── Merkez kapsayıcı ─────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        center = ctk.CTkFrame(body, fg_color="transparent")
        center.grid(row=0, column=0, padx=60)
        center.grid_columnconfigure(0, weight=1)

        r = 0

        # ── Logo ─────────────────────────────────
        logo_wrap = ctk.CTkFrame(center, fg_color="transparent")
        logo_wrap.grid(row=r, column=0, pady=(0, 6)); r += 1

        logo_box = ctk.CTkFrame(
            logo_wrap,
            fg_color=ACCENT,
            corner_radius=12,
            width=52,
            height=52,
        )
        logo_box.pack(anchor="center")
        logo_box.grid_propagate(False)
        ctk.CTkLabel(
            logo_box,
            text="B",
            font=("Inter", 26, "bold"),
            text_color="#ffffff",
        ).place(relx=0.5, rely=0.5, anchor="center")

        # ── Başlık ───────────────────────────────
        ctk.CTkLabel(
            center,
            text="Blackboard Sync",
            font=("Inter", 22, "bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=r, column=0, pady=(10, 2)); r += 1

        ctk.CTkLabel(
            center,
            text="Istinye Üniversitesi  ·  Ders Materyali İndirici",
            font=FONT_SMALL,
            text_color=TEXT_TERTIARY,
        ).grid(row=r, column=0, pady=(0, 28)); r += 1

        # ── Form kartı ───────────────────────────
        card = ctk.CTkFrame(
            center,
            fg_color=BG_ELEVATED,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=r, column=0, sticky="ew", pady=(0, 16)); r += 1
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="Öğrenci Numarası",
            font=("Inter", 11, "bold"),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).grid(row=0, column=0, padx=20, pady=(20, 4), sticky="w")

        self._entry_no = ctk.CTkEntry(
            card,
            placeholder_text="Numaranızı girin (örn. 2200000000)",
            fg_color=BG_BASE,
            border_color=BORDER,
            border_width=1,
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_TERTIARY,
            corner_radius=8,
            font=FONT_BODY,
            height=42,
        )
        self._entry_no.grid(row=1, column=0, padx=20, sticky="ew")
        self._entry_no.bind("<KeyRelease>", self._on_no_change)
        self._entry_no.bind("<Return>",     lambda _: self._start_login())

        self._lbl_email = ctk.CTkLabel(
            card,
            text="",
            font=("Inter", 11),
            text_color=TEXT_TERTIARY,
            anchor="w",
        )
        self._lbl_email.grid(row=2, column=0, padx=20, pady=(5, 0), sticky="w")

        # Ayırıcı
        ctk.CTkFrame(card, height=1, fg_color=BORDER).grid(
            row=3, column=0, padx=20, pady=(16, 0), sticky="ew",
        )

        self._btn_login = ctk.CTkButton(
            card,
            text="🌐  Tarayıcıda Giriş Yap",
            command=self._start_login,
            fg_color=ACCENT,
            hover_color="#6366f1",
            text_color="#ffffff",
            corner_radius=8,
            font=("Inter", 13, "bold"),
            height=44,
        )
        self._btn_login.grid(row=4, column=0, padx=20, pady=(14, 10), sticky="ew")

        # "Tarayıcıyı Göster" butonu — sadece login devam ederken görünür
        self._btn_show_browser = ctk.CTkButton(
            card,
            text="🔍  Tarayıcıyı Göster",
            command=self._show_browser,
            fg_color="transparent",
            hover_color=BG_HOVER,
            text_color=ACCENT,
            corner_radius=8,
            font=("Inter", 12),
            height=34,
            border_width=1,
            border_color=BORDER,
        )
        # Başlangıçta gizli — grid ile yönetilir
        self._btn_show_browser.grid(row=5, column=0, padx=20, pady=(0, 14), sticky="ew")
        self._btn_show_browser.grid_remove()

        # ── Status satırı ────────────────────────
        status_row = ctk.CTkFrame(center, fg_color="transparent")
        status_row.grid(row=r, column=0, sticky="ew"); r += 1
        status_row.grid_columnconfigure(1, weight=1)

        self._dot = ctk.CTkLabel(
            status_row, text="●",
            font=("Inter", 11), text_color=DOT_IDLE, width=14,
        )
        self._dot.grid(row=0, column=0, padx=(0, 6))

        self._lbl_status = ctk.CTkLabel(
            status_row, text="Hazır",
            font=FONT_SMALL, text_color=TEXT_TERTIARY, anchor="w",
        )
        self._lbl_status.grid(row=0, column=1, sticky="w")

        # ── Güvenlik notu ────────────────────────
        ctk.CTkLabel(
            center,
            text="🔒  Şifreniz hiçbir zaman kaydedilmez veya diske yazılmaz",
            font=("Inter", 11),
            text_color=TEXT_TERTIARY,
            justify="center",
        ).grid(row=r, column=0, pady=(18, 0)); r += 1

        # ── Alt accent şeridi ─────────────────────
        ctk.CTkFrame(self, fg_color=BG_ELEVATED, corner_radius=0, height=1).grid(
            row=2, column=0, sticky="ew",
        )

    # ── Event Handlers ────────────────────────────────────────

    def _on_no_change(self, _event=None) -> None:
        no = self._entry_no.get().strip()
        if no:
            self._lbl_email.configure(text=f"→  {no}@stu.istinye.edu.tr")
            valid = no.isdigit()
            self._entry_no.configure(
                border_color=ACCENT if valid else ERROR,
            )
        else:
            self._lbl_email.configure(text="")
            self._entry_no.configure(border_color=BORDER)

    def _start_login(self) -> None:
        if self._login_running:
            return
        no = self._entry_no.get().strip()
        if not no:
            self._set_status("Öğrenci numaranızı girin", DOT_ERROR)
            self._shake_entry()
            return
        if not no.isdigit():
            self._set_status("Numara yalnızca rakam içerebilir", DOT_ERROR)
            self._shake_entry()
            return

        self._login_running = True
        self._btn_login.configure(state="disabled", text="⏳  Bağlanıyor...")
        self._btn_show_browser.grid()          # tarayıcı açılınca göster
        self._set_status("Tarayıcı başlatılıyor...", DOT_BUSY)
        threading.Thread(target=self._run_login, args=(no,), daemon=True).start()

    def _shake_entry(self) -> None:
        self._entry_no.configure(border_color=ERROR)
        self.after(800, lambda: self._entry_no.configure(border_color=BORDER))

    def _show_browser(self) -> None:
        """Playwright tarayıcı penceresini öne çeker."""
        if self._auth:
            self._auth.bring_to_front_sync()

    def _run_login(self, student_no: str) -> None:
        import asyncio
        self._auth = BlackboardAuth()
        loop = asyncio.new_event_loop()
        try:
            session = loop.run_until_complete(
                self._auth.login(
                    student_no,
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
        self._btn_login.configure(state="normal", text="🌐  Tarayıcıda Giriş Yap")
        self._btn_show_browser.grid_remove()
        self._set_status("Giriş başarılı!", DOT_OK)
        self._on_login_success(student_no, session)

    def _login_error(self, msg: str) -> None:
        self._login_running = False
        self._btn_login.configure(state="normal", text="🌐  Tarayıcıda Giriş Yap")
        self._btn_show_browser.grid_remove()
        self._set_status(f"Hata: {msg}", DOT_ERROR)

    def _handle_browser_closed(self) -> None:
        self.after(0, lambda: self._set_status(
            "Tarayıcı kapatıldı — tekrar başlatmak için butona tıklayın", DOT_ERROR,
        ))
        self.after(0, lambda: self._btn_login.configure(
            state="normal", text="🌐  Tarayıcıda Giriş Yap",
        ))
        self.after(0, self._btn_show_browser.grid_remove)
        self._login_running = False

    # ── Status Helpers ────────────────────────────────────────

    def _set_status_thread(self, msg: str) -> None:
        self.after(0, lambda m=msg: self._set_status(m, DOT_BUSY))

    def _set_status(self, msg: str, color: str = DOT_IDLE) -> None:
        self._lbl_status.configure(text=msg, text_color=color)
        self._dot.configure(text_color=color)
        if self._on_status_ext:
            self._on_status_ext(msg)
