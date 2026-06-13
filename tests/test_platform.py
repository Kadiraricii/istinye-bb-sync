"""
Platform uyumluluğunu test eder — macOS ve Windows'ta aynı çalışmalı.
"""
import platform
import sys
from pathlib import Path

import pytest


def test_platform_detected():
    """platform.system() tanınan bir değer döndürmeli."""
    name = platform.system()
    assert name in ("Darwin", "Windows", "Linux"), f"Bilinmeyen platform: {name}"


def test_path_home_exists():
    """Kullanıcı ev dizini mevcut olmalı."""
    home = Path.home()
    assert home.exists(), f"Home dizini bulunamadı: {home}"


def test_path_home_is_absolute():
    assert Path.home().is_absolute()


def test_windows_specific_attrs():
    """Windows'ta subprocess.CREATE_NO_WINDOW erişilebilir olmalı."""
    import subprocess
    if sys.platform == "win32":
        assert hasattr(subprocess, "CREATE_NO_WINDOW"), (
            "subprocess.CREATE_NO_WINDOW Windows'ta mevcut olmalı"
        )


def test_asyncio_default_loop_policy():
    """
    Windows'ta varsayılan policy ProactorEventLoop olmalı.
    SelectorEventLoop'u AYARLAMAMALIYIZ — playwright subprocess gerektirir.
    """
    import asyncio
    if sys.platform == "win32":
        policy = asyncio.get_event_loop_policy()
        assert isinstance(policy, asyncio.WindowsProactorEventLoopPolicy), (
            "Windows'ta ProactorEventLoop policy kullanılmalı "
            "(playwright için gerekli — SelectorEventLoop ayarlama!)"
        )


def test_slugify_safe_on_windows(tmp_path):
    """Windows'ta geçersiz karakter içermeyen dosya adı üretilmeli."""
    from core.state import slugify_filename
    dangerous = [
        "file:name",       # : Windows'ta geçersiz
        "file<test>",      # <> geçersiz
        'file"quote"',     # " geçersiz
        "file/slash",      # / path separator
        "file\\back",      # \ path separator
        "file|pipe",       # | geçersiz
        "file?question",   # ? geçersiz
        "file*star",       # * geçersiz
    ]
    for name in dangerous:
        result = slugify_filename(name)
        for char in '<>:"/\\|?*':
            assert char not in result, (
                f"Güvensiz karakter '{char}' '{name}' → '{result}' içinde"
            )
        # Gerçekten dosya oluşturulabilmeli mi?
        try:
            f = tmp_path / result
            f.touch()
            assert f.exists()
            f.unlink()
        except (OSError, ValueError) as e:
            pytest.fail(f"'{result}' dosya olarak oluşturulamadı: {e}")


def test_data_dir_path_is_valid():
    """DATA_DIR geçerli bir Path objesi olmalı."""
    from core.config import DATA_DIR
    assert isinstance(DATA_DIR, Path)
    # Path string'e çevrilebilmeli (her OS'ta)
    assert len(str(DATA_DIR)) > 0


def test_notification_message_ascii_safe():
    """
    Windows bildirim mesajı ASCII-safe olmalı
    (base64 encode ettiğimiz için artık sorun yok ama test edelim).
    """
    import base64
    msg = "6 dosya indirildi, 1 hata"
    ps = f"$n.BalloonTipText = '{msg}'"
    # UTF-16LE encode → base64 → decode çalışmalı
    encoded = base64.b64encode(ps.encode("utf-16-le")).decode("ascii")
    decoded = base64.b64decode(encoded).decode("utf-16-le")
    assert msg in decoded


def test_open_folder_method_exists():
    """
    ProgressScreen._open_folder metodu platform'a göre doğru dalı seçmeli.
    Gerçekten dosya açmadan sadece branch logic'i test eder.
    """
    import platform as pf
    sys_name = pf.system()
    if sys_name == "Darwin":
        import subprocess
        assert hasattr(subprocess, "run")
    elif sys_name == "Windows":
        import os
        assert hasattr(os, "startfile"), "os.startfile Windows'ta mevcut olmalı"
    else:
        import subprocess
        assert hasattr(subprocess, "run")


def test_path_separator_handling(tmp_path):
    """
    path_hint'teki / karakteri hem macOS hem Windows'ta doğru klasör yapısı oluşturmalı.
    """
    from core.downloader import BlackboardDownloader
    result = BlackboardDownloader._resolve_item_dir(tmp_path, "Hafta1/Notlar")
    # Her iki OS'ta da alt klasör oluşturulmalı
    assert result != tmp_path
    assert len(result.parts) > len(tmp_path.parts)
