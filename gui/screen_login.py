from __future__ import annotations

import threading
from typing import Callable, Optional

import customtkinter as ctk

from gui.theme import (
    ACCENT, BG_BASE, BG_ELEVATED, BORDER, BTN_PRIMARY, BTN_SECONDARY,
    CTK_APPEARANCE, CTK_COLOR_THEME, DOT_BUSY, DOT_ERROR, DOT_IDLE, DOT_OK,
    ENTRY, FONT_BODY, FONT_HERO, FONT_SMALL, TEXT_PRIMARY,
    TEXT_SECONDARY, TEXT_TERTIARY,
)


class LoginScreen(ctk.CTkFrame):
    """
    Login ekranı.

    on_login_success(student_no, session) çağrıldığında App bir sonraki
    ekrana geçer.
    """

    def __init__(
        self,
        master: ctk.CTk,
        on_login_success: Callable,
        on_status: Optional[Callable[[str], None]] = None,
    ) -> None:
        super().__init__(master, fg_color=BG_BASE, corner_radius=0)
        self._on_login_success = on_login_success
        self._on_status_ext    = on_status
        self._student_no       = ""
        self._login_running    = False

        self._build()

    # ── Layout ────────────────────────────────────────────────

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        center = ctk.CTkFrame(self, fg_color="transparent")
        center.grid(row=0, column=0, padx=40, pady=40, sticky="nsew")
        center.grid_columnconfigure(0, weight=1)

        row = 0

        # ── Logo / başlık
        logo_frame = ctk.CTkFrame(center, fg_color="transparent")
        logo_frame.grid(row=row, column=0, pady=(0, 4)); row += 1

        ctk.CTkLabel(
            logo_frame,
            text="⬛",
            font=("Inter", 32),
            text_color=ACCENT,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            logo_frame,
            text="Blackboard Sync",
            font=FONT_HERO,
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkLabel(
            center,
            text="Istinye Üniversitesi · Ders Materyali İndirici",
            font=FONT_SMALL,
            text_color=TEXT_TERTIARY,
        ).grid(row=row, column=0, pady=(0, 32)); row += 1

        # ── Öğrenci numarası
        ctk.CTkLabel(
            center, text="Öğrenci Numarası",
            font=FONT_SMALL, text_color=TEXT_SECONDARY,
            anchor="w",
        ).grid(row=row, column=0, sticky="w", pady=(0, 4)); row += 1

        self._entry_no = ctk.CTkEntry(
            center,
            placeholder_text="2200000000",
            **ENTRY,
        )
        self._entry_no.grid(row=row, column=0, sticky="ew", pady=(0, 4)); row += 1
        self._entry_no.bind("<KeyRelease>", self._on_no_change)
        self._entry_no.bind("<Return>", lambda _: self._start_login())

        self._lbl_email = ctk.CTkLabel(
            center, text="",
            font=FONT_SMALL, text_color=TEXT_TERTIARY, anchor="w",
        )
        self._lbl_email.grid(row=row, column=0, sticky="w", pady=(0, 20)); row += 1

        # ── Login butonu
        self._btn_login = ctk.CTkButton(
            center,
            text="Tarayıcıda Giriş Yap",
            command=self._start_login,
            **BTN_PRIMARY,
        )
        self._btn_login.grid(row=row, column=0, sticky="ew", pady=(0, 16)); row += 1

        # ── Ayırıcı
        ctk.CTkFrame(center, height=1, fg_color=BORDER).grid(
            row=row, column=0, sticky="ew", pady=(0, 16),
        ); row += 1

        # ── Status satırı
        status_row = ctk.CTkFrame(center, fg_color="transparent")
        status_row.grid(row=row, column=0, sticky="ew"); row += 1
        status_row.grid_columnconfigure(1, weight=1)

        self._dot = ctk.CTkLabel(
            status_row, text="●", font=("Inter", 12), text_color=DOT_IDLE, width=16,
        )
        self._dot.grid(row=0, column=0, padx=(0, 6))

        self._lbl_status = ctk.CTkLabel(
            status_row, text="Hazır",
            font=FONT_SMALL, text_color=TEXT_TERTIARY, anchor="w",
        )
        self._lbl_status.grid(row=0, column=1, sticky="w")

        # ── Bilgi notu
        ctk.CTkLabel(
            center,
            text="Tarayıcı açılır, siz şifrenizi girersiniz.\nŞifreniz hiçbir zaman kaydedilmez.",
            font=FONT_SMALL,
            text_color=TEXT_TERTIARY,
            justify="center",
        ).grid(row=row, column=0, pady=(20, 0)); row += 1

    # ── Event Handlers ────────────────────────────────────────

    def _on_no_change(self, _event=None) -> None:
        no = self._entry_no.get().strip()
        self._student_no = no
        if no:
            self._lbl_email.configure(text=f"→ {no}@stu.istinye.edu.tr")
        else:
            self._lbl_email.configure(text="")

    def _start_login(self) -> None:
        if self._login_running:
            return
        no = self._entry_no.get().strip()
        if not no:
            self._set_status("Öğrenci numaranızı girin", DOT_ERROR)
            return
        if not no.isdigit():
            self._set_status("Numara yalnızca rakam içerebilir", DOT_ERROR)
            return

        self._login_running = True
        self._btn_login.configure(state="disabled", text="Bağlanıyor...")
        self._set_status("Tarayıcı başlatılıyor...", DOT_BUSY)
        threading.Thread(target=self._run_login, args=(no,), daemon=True).start()

    def _run_login(self, student_no: str) -> None:
        import asyncio
        from core.auth import BlackboardAuth

        auth = BlackboardAuth()
        loop = asyncio.new_event_loop()
        try:
            session = loop.run_until_complete(
                auth.login(
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
        self._btn_login.configure(state="normal", text="Tarayıcıda Giriş Yap")
        self._set_status("Giriş başarılı!", DOT_OK)
        self._on_login_success(student_no, session)

    def _login_error(self, msg: str) -> None:
        self._login_running = False
        self._btn_login.configure(state="normal", text="Tarayıcıda Giriş Yap")
        self._set_status(f"Hata: {msg}", DOT_ERROR)

    def _handle_browser_closed(self) -> None:
        self.after(0, lambda: self._set_status(
            "Tarayıcı kapatıldı — yeniden giriş için butona tıklayın", DOT_ERROR,
        ))
        self.after(0, lambda: self._btn_login.configure(
            state="normal", text="Tarayıcıda Giriş Yap",
        ))
        self._login_running = False

    # ── Status Helpers ────────────────────────────────────────

    def _set_status_thread(self, msg: str) -> None:
        self.after(0, lambda m=msg: self._set_status(m, DOT_BUSY))

    def _set_status(self, msg: str, color: str = DOT_IDLE) -> None:
        self._lbl_status.configure(text=msg, text_color=color)
        self._dot.configure(text_color=color)
        if self._on_status_ext:
            self._on_status_ext(msg)
