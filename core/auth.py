from __future__ import annotations

import asyncio
import shutil
import tempfile
from typing import Callable, Optional

import requests
from playwright.async_api import (
    async_playwright,
    BrowserContext,
    Page,
    Playwright,
)

from core.config import BB_ULTRA, EMAIL_DOMAIN, REQUEST_TIMEOUT


_LOGIN_PATTERNS  = ["login.microsoftonline.com", "webapps/login", "webapps/bb-auth"]
_SUCCESS_PATTERN = "/ultra/"

_MS_EMAIL_SEL    = 'input[type="email"], input[name="loginfmt"]'
_MS_PASSWORD_SEL = 'input[type="password"], input[name="passwd"]'
_MS_SUBMIT_SEL   = 'input[type="submit"], button[type="submit"]'

_BB_USER_SEL     = '#user_id, input[name="user_id"]'
_BB_PASS_SEL     = '#password, input[name="password"]'
_BB_SUBMIT_SEL   = '#entry-login, input[type="submit"]'


class BlackboardAuth:
    """
    Playwright tabanlı Blackboard login yöneticisi.

    Kalıcı tarayıcı profili: aynı uygulama oturumunda tarayıcı kapansa bile
    Microsoft SSO oturumu korunur — yeniden açılınca şifre sorulmaz.
    Uygulama kapanınca profil klasörü silinir (cookie disk'te kalmaz).
    """

    def __init__(self) -> None:
        self._pw:       Optional[Playwright]     = None
        self._context:  Optional[BrowserContext] = None
        self._page:     Optional[Page]           = None
        self._session:  Optional[requests.Session] = None
        self._loop:     Optional[asyncio.AbstractEventLoop] = None
        self._password: Optional[str] = None   # bellekte tutulur, kullanıldıktan sonra silinir
        self._on_status:         Optional[Callable[[str], None]] = None
        self._on_browser_closed: Optional[Callable[[], None]]   = None
        # Geçici profil — aynı oturumda tarayıcı kapansa Microsoft login korunur
        self._user_data_dir: str = tempfile.mkdtemp(prefix="bb_sync_profile_")

    # ── Public API ────────────────────────────────────────────

    async def login(
        self,
        student_no: str,
        password: Optional[str] = None,
        on_status: Optional[Callable[[str], None]] = None,
        on_browser_closed: Optional[Callable[[], None]] = None,
    ) -> requests.Session:
        self._on_status         = on_status
        self._on_browser_closed = on_browser_closed
        self._loop              = asyncio.get_event_loop()
        self._password          = password

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
        """Kapatılan tarayıcıyı yeniden aç; kalıcı profil sayesinde devam eder."""
        try:
            if self._context:
                await self._context.close()
            if self._pw:
                await self._pw.stop()
        except Exception:
            pass
        finally:
            self._context = self._page = self._pw = None

        return await self.login(
            student_no,
            on_status=self._on_status,
            on_browser_closed=self._on_browser_closed,
        )

    def bring_to_front_sync(self) -> None:
        """GUI thread'den çağrılır: Playwright tarayıcı penceresini öne alır."""
        if self._page and self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self._page.bring_to_front(), self._loop,
            )

    def get_session(self) -> Optional[requests.Session]:
        return self._session

    async def close(self) -> None:
        """Sadece tarayıcıyı kapatır; profil klasörü korunur."""
        try:
            if self._context:
                await self._context.close()
            if self._pw:
                await self._pw.stop()
        except Exception:
            pass
        finally:
            self._context = self._page = self._pw = None

    def cleanup(self) -> None:
        """Uygulama kapanınca çağrılır: geçici profil klasörünü siler."""
        shutil.rmtree(self._user_data_dir, ignore_errors=True)

    # ── İç metodlar ──────────────────────────────────────────

    async def _launch_browser(self) -> None:
        self._pw = await async_playwright().start()
        # Kalıcı context — aynı oturumdaki tarayıcı restartlarında
        # Microsoft SSO cookie'leri korunur
        self._context = await self._pw.chromium.launch_persistent_context(
            self._user_data_dir,
            headless=False,
            args=["--start-maximized"],
            no_viewport=True,
        )
        self._page = await self._context.new_page()
        self._context.on("close", self._handle_browser_closed)

    async def _navigate(self, url: str) -> None:
        await self._page.goto(url, wait_until="domcontentloaded",
                              timeout=REQUEST_TIMEOUT * 1000)

    async def _fill_credentials(self, student_no: str) -> None:
        email = f"{student_no}{EMAIL_DOMAIN}"
        await self._wait_for_login_page()
        current = self._page.url
        if "microsoftonline.com" in current:
            await self._fill_microsoft_login(email)
        else:
            await self._fill_blackboard_login(email)

    async def _wait_for_login_page(self) -> None:
        deadline = asyncio.get_event_loop().time() + REQUEST_TIMEOUT * 2
        while asyncio.get_event_loop().time() < deadline:
            url = self._page.url
            if any(p in url for p in _LOGIN_PATTERNS):
                return
            if _SUCCESS_PATTERN in url:
                return
            await asyncio.sleep(0.5)

    async def _fill_microsoft_login(self, email: str) -> None:
        try:
            await self._page.wait_for_selector(
                _MS_EMAIL_SEL, timeout=REQUEST_TIMEOUT * 1000
            )
            await self._page.locator(_MS_EMAIL_SEL).first.fill(email)
            self._status(f"Email girildi: {email}")
            await self._page.locator(_MS_SUBMIT_SEL).first.click()

            if self._password:
                try:
                    # Şifre alanı çıkana kadar bekle
                    await self._page.wait_for_selector(
                        _MS_PASSWORD_SEL, timeout=15_000
                    )
                    await self._page.locator(_MS_PASSWORD_SEL).first.fill(self._password)
                    self._password = None  # bellekten hemen sil
                    self._status("Şifre girildi, giriş bekleniyor...")
                    await self._page.locator(_MS_SUBMIT_SEL).first.click()
                    # Hata mesajı çıktı mı kontrol et (yanlış şifre)
                    await asyncio.sleep(2.0)
                    await self._check_password_error()
                except Exception:
                    self._password = None
                    self._status("Şifre alanı bulunamadı — lütfen tarayıcıda girin")
            else:
                self._status("Şifre bekleniyor (tarayıcıya girin)...")
        except Exception:
            self._password = None
            self._status("Email alanı bulunamadı — lütfen tarayıcıda kendiniz girin")

    async def _fill_blackboard_login(self, email: str) -> None:
        try:
            await self._page.wait_for_selector(
                _BB_USER_SEL, timeout=REQUEST_TIMEOUT * 1000
            )
            await self._page.locator(_BB_USER_SEL).first.fill(email)
            if self._password:
                await self._page.locator(_BB_PASS_SEL).first.fill(self._password)
                self._password = None
                self._status("Bilgiler girildi, giriş bekleniyor...")
                await self._page.locator(_BB_SUBMIT_SEL).first.click()
            else:
                await self._page.locator(_BB_PASS_SEL).first.focus()
                self._status("Şifre bekleniyor (tarayıcıda girin)...")
        except Exception:
            self._password = None
            self._status("Giriş formu bulunamadı — lütfen tarayıcıda kendiniz girin")

    # Microsoft hata selektörleri — yanlış şifre sonrası gösterilen element
    _MS_ERROR_SELS = [
        "#passwordError",
        "#usernameError",
        "[data-bind*='sErrorText']",
        ".alert-error",
    ]

    async def _check_password_error(self) -> None:
        """Şifre submit'inden sonra MS hata mesajı var mı kontrol eder."""
        try:
            for sel in self._MS_ERROR_SELS:
                el = self._page.locator(sel).first
                if await el.count() > 0 and await el.is_visible():
                    self._password = None
                    self._status(
                        "⚠️ Hatalı şifre — lütfen tarayıcıda doğru şifreyi girin"
                    )
                    return
        except Exception:
            pass

    # Tüm "Hayır" / "No" selektör alternatifleri
    _HAYIR_SELECTORS = [
        "input[value='Hayır']",
        "input[value='No']",
        "button:has-text('Hayır')",
        "button:has-text('No')",
        "[id*='idBtn_Back']",          # Microsoft KMSI "No" button id
    ]

    async def _wait_for_dashboard(self) -> None:
        deadline = asyncio.get_event_loop().time() + 300
        _last_status = ""
        while asyncio.get_event_loop().time() < deadline:
            url = self._page.url
            if _SUCCESS_PATTERN in url:
                return
            # Blackboard yükleme ekranı (siyah ekran + spinner)
            if "blackboard.com" in url and _SUCCESS_PATTERN not in url and "login" not in url and "microsoftonline" not in url:
                msg = "Blackboard'a bağlanılıyor, lütfen bekleyin..."
                if msg != _last_status:
                    self._status(msg)
                    _last_status = msg
            await self._try_click_hayir()
            await asyncio.sleep(0.6)
        raise TimeoutError("Giriş zaman aşımına uğradı (300s)")

    async def _try_click_hayir(self) -> None:
        """Her iterasyonda 'Oturumunuz açık kalsın mı?' butonunu arar ve tıklar."""
        try:
            for sel in self._HAYIR_SELECTORS:
                el = self._page.locator(sel).first
                if await el.count() > 0 and await el.is_visible():
                    await el.click()
                    self._status("🔒 'Oturumunuz açık kalsın mı?' → Hayır tıklandı ✓")
                    await asyncio.sleep(1.0)  # tıklamadan sonra yönlendirme için bekle
                    return
        except Exception:
            pass

    async def _build_session(self) -> requests.Session:
        cookies = await self._context.cookies()
        session = requests.Session()
        for c in cookies:
            session.cookies.set(
                c["name"], c["value"], domain=c.get("domain", ""),
            )
        session.headers.update({
            "User-Agent": await self._page.evaluate("navigator.userAgent"),
        })
        return session

    def _handle_browser_closed(self, *_) -> None:
        if self._on_browser_closed:
            self._on_browser_closed()

    def _status(self, message: str) -> None:
        if self._on_status:
            self._on_status(message)
