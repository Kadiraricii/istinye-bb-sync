# Blackboard Downloader - Windows Kurulum Scripti
# Kullanim: PowerShell'de sag tikla -> "PowerShell ile Calistir"
# veya: powershell -ExecutionPolicy Bypass -File setup.ps1

$ErrorActionPreference = "Stop"

function Write-Ok($msg)   { Write-Host "[+] $msg" -ForegroundColor Green }
function Write-Info($msg) { Write-Host "[.] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "[x] $msg" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "  Blackboard Downloader - Kurulum" -ForegroundColor Cyan
Write-Host "  --------------------------------"
Write-Host ""

# 1. Python kontrolu
Write-Info "Python kontrol ediliyor..."
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    $py = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $py) {
    Write-Err "Python bulunamadi. https://python.org adresinden Python 3.11+ indirin."
}

$version = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
$parts   = $version -split "\."
if ([int]$parts[0] -lt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -lt 11)) {
    Write-Err "Python 3.11+ gerekli. Mevcut: $version"
}
Write-Ok "Python $version bulundu"

# 2. Virtual environment
Write-Info "Virtual environment olusturuluyor..."
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Ok "Virtual environment olusturuldu (.venv\)"
} else {
    Write-Warn "Virtual environment zaten var, atlanıyor"
}

# 3. Paketler
Write-Info "Bagimliliklar yukleniyor..."
& ".venv\Scripts\pip.exe" install --upgrade pip --quiet
& ".venv\Scripts\pip.exe" install -r requirements.txt --quiet
Write-Ok "Bagimliliklar yuklendi"

# 4. Playwright Chromium
Write-Info "Playwright Chromium tarayicisi yukleniyor..."
& ".venv\Scripts\playwright.exe" install chromium
Write-Ok "Chromium yuklendi"

# 5. Klasor yapisi
Write-Info "Klasor yapisi olusturuluyor..."
New-Item -ItemType Directory -Force -Path "data\downloads" | Out-Null
Write-Ok "data\downloads\ hazir"

# Tamamlandi
Write-Host ""
Write-Host "  ----------------------------------------" -ForegroundColor Green
Write-Ok "Kurulum tamamlandi!"
Write-Host ""
Write-Host "  Uygulamayi baslatmak icin: run.bat" -ForegroundColor White
Write-Host ""
