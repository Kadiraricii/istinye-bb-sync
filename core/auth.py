from __future__ import annotations

import asyncio
from typing import Callable, Optional

import requests
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
)

from core.config import BB_ULTRA, EMAIL_DOMAIN, REQUEST_TIMEOUT


# Desteklenen login sayfası URL pattern'leri
_LOGIN_PATTERNS   = ["login.microsoftonline.com", "webapps/login", "webapps/bb-auth"]
_SUCCESS_PATTERN  = "/ultra/"

# Microsoft login form selectors
_MS_EMAIL_SEL    = 'input[type="email"], input[name="loginfmt"]'
_MS_PASSWORD_SEL = 'input[type="password"], input[name="passwd"]'
_MS_SUBMIT_SEL   = 'input[type="submit"], button[type="submit"]'

# Blackboard local login selectors (fallback)
_BB_USER_SEL     = '#user_id, input[name="user_id"]'
_BB_PASS_SEL     = '#password, input[name="password"]'
_BB_SUBMIT_SEL   = '#entry-login, input[type="submit"]'


class BlackboardAuth:
    """
    Playwright tabanlı Blackboard login yöneticisi.

    Kullanım:
        auth = BlackboardAuth()
        session = await auth.login("2200000000", on_status=callback)
        # session: hazır requests.Session (BbRouter cookie ile)
    """

    def __init__(self) -> None:
        self._pw:       Optional[Playwright]     = None
        self._browser:  Optional[Browser]        = None
        self._context:  Optional[BrowserContext] = None
        self._page:     Optional[Page]           = None
        self._session:  Optional[requests.Session] = None
        self._on_status:         Optional[Callable[[str], None]] = None
        self._on_browser_closed: Optional[Callable[[], None]]   = None

    # ── Public API ────────────────────────────────────────────

    async def login(
        self,
        student_no: str,
        on_status: Optional[Callable[[str], None]] = None,
        on_browser_closed: Optional[Callable[[], None]] = None,
    ) -> requests.Session:
        """
        Login akışını yürütür. Başarılı olunca hazır requests.Session döner.
        on_status   : GUI'ye durum mesajı iletmek için callback
        on_browser_closed : Tarayıcı kapatılınca çağrılır (GUI uyarısı için)
        """
        self._on_status         = on_status
        self._on_browser_closed = on_browser_closed

        self._status("Tarayıcı başlatılıyor...")
        await self._launch_browser()

        self._status("Blackboard'a bağlanılıyor...")
        await self._navigate(BB_ULTRA)

        self._status("Giriş formu dolduruluyor...")
        await self._fill_credentials(student_no)

        self._status("Giriş bekleniyor...")
        await self._wait_for_dashboard()

        self._status("Cookie'ler alınıyor...")
        self._session = await self._build_session()

        self._status("Giriş başarılı!")
        return self._session

    async def reopen_browser(self, student_no: str) -> requests.Session:
        """Kapatılan tarayıcıyı yeniden aç ve kaldığı yerden devam et."""
        await self.close()
        return await self.login(
            student_no,
            on_status=self._on_status,
            on_browser_closed=self._on_browser_closed,
        )

    def get_session(self) -> Optional[requests.Session]:
        return self._session

    async def close(self) -> None:
        try:
            if self._browser:
                await self._browser.close()
            if self._pw:
                await self._pw.stop()
        except Exception:
            pass
        finally:
            self._browser = self._context = self._page = self._pw = None

    # ── İç metodlar ──────────────────────────────────────────

    async def _launch_browser(self) -> None:
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(
            headless=False,
            args=["--start-maximized"],
        )
        self._context = await self._browser.new_context(no_viewport=True)
        self._page    = await self._context.new_page()

        # Tarayıcı kapatılma olayı
        self._browser.on("disconnected", self._handle_browser_closed)

    async def _navigate(self, url: str) -> None:
        await self._page.goto(url, wait_until="domcontentloaded",
                              timeout=REQUEST_TIMEOUT * 1000)

    async def _fill_credentials(self, student_no: str) -> None:
        email = f"{student_no}{EMAIL_DOMAIN}"

        # Microsoft SSO sayfasına yönlenene kadar bekle
        await self._wait_for_login_page()

        current = self._page.url

        if "microsoftonline.com" in current:
            await self._fill_microsoft_login(email)
        else:
            await self._fill_blackboard_login(email)

    async def _wait_for_login_page(self) -> None:
        """Login sayfası yüklenene kadar bekle (SSO redirect dahil)."""
        deadline = asyncio.get_event_loop().time() + REQUEST_TIMEOUT * 2
        while asyncio.get_event_loop().time() < deadline:
            url = self._page.url
            if any(p in url for p in _LOGIN_PATTERNS):
                return
            if _SUCCESS_PATTERN in url:
                return  # Zaten giriş yapılmış
            await asyncio.sleep(0.5)

    async def _fill_microsoft_login(self, email: str) -> None:
        """Microsoft login sayfasında email doldurur, şifreyi kullanıcıya bırakır."""
        try:
            await self._page.wait_for_selector(
                _MS_EMAIL_SEL, timeout=REQUEST_TIMEOUT * 1000
            )
            email_field = self._page.locator(_MS_EMAIL_SEL).first
            await email_field.fill(email)
            self._status(f"Email girildi: {email}")

            # "Next" butonuna tıkla (Microsoft login akışı)
            submit = self._page.locator(_MS_SUBMIT_SEL).first
            await submit.click()

            self._status("Şifre bekleniyor (tarayıcıya girin)...")
        except Exception:
            self._status("Email alanı bulunamadı — lütfen tarayıcıda kendiniz girin")

    async def _fill_blackboard_login(self, email: str) -> None:
        """Blackboard yerel login formunu doldurur."""
        try:
            await self._page.wait_for_selector(
                _BB_USER_SEL, timeout=REQUEST_TIMEOUT * 1000
            )
            await self._page.locator(_BB_USER_SEL).first.fill(email)
            await self._page.locator(_BB_PASS_SEL).first.focus()
            self._status("Şifre bekleniyor (tarayıcıya girin)...")
        except Exception:
            self._status("Giriş formu bulunamadı — lütfen tarayıcıda kendiniz girin")

    async def _wait_for_dashboard(self) -> None:
        """URL /ultra/ içerene kadar bekle (login tamamlandı sinyali)."""
        await self._page.wait_for_url(
            f"**{_SUCCESS_PATTERN}**",
            timeout=300_000,  # 5 dakika — MFA için yeterli süre
            wait_until="domcontentloaded",
        )

    async def _build_session(self) -> requests.Session:
        """Playwright cookie'lerini requests.Session'a aktar."""
        cookies = await self._context.cookies()
        session = requests.Session()
        for c in cookies:
            session.cookies.set(
                c["name"],
                c["value"],
                domain=c.get("domain", ""),
            )
        session.headers.update({
            "User-Agent": await self._page.evaluate("navigator.userAgent"),
        })
        return session

    def _handle_browser_closed(self, _: Browser) -> None:
        """Playwright disconnected event handler."""
        if self._on_browser_closed:
            self._on_browser_closed()

    def _status(self, message: str) -> None:
        if self._on_status:
            self._on_status(message)
