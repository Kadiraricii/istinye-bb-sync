#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
#  Blackboard Downloader — Kurulum Scripti
#  Kullanım: ./setup.sh
# ─────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}[•]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo "  ██████╗ ██████╗ ██╗"
echo "  ██╔══██╗██╔══██╗██║"
echo "  ██████╔╝██████╔╝██║"
echo "  ██╔══██╗██╔══██╗██║"
echo "  ██████╔╝██████╔╝███████╗"
echo "  ╚═════╝ ╚═════╝ ╚══════╝  Blackboard Downloader Kurulumu"
echo ""

# ── 1. Python kontrolü ──────────────────────────────────────
info "Python sürümü kontrol ediliyor..."
if ! command -v python3 &>/dev/null; then
    error "Python 3 bulunamadı. https://python.org adresinden indirin."
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [[ "$PYTHON_MAJOR" -lt 3 ]] || [[ "$PYTHON_MAJOR" -eq 3 && "$PYTHON_MINOR" -lt 11 ]]; then
    error "Python 3.11+ gerekli. Mevcut: $PYTHON_VERSION"
fi
success "Python $PYTHON_VERSION bulundu"

# ── 2. Virtual environment ───────────────────────────────────
info "Virtual environment oluşturuluyor..."
if [[ ! -d ".venv" ]]; then
    python3 -m venv .venv
    success "Virtual environment oluşturuldu (.venv/)"
else
    warn "Virtual environment zaten var, atlanıyor"
fi

# ── 3. venv aktivasyonu ──────────────────────────────────────
# shellcheck source=/dev/null
source .venv/bin/activate
success "Virtual environment aktif"

# ── 4. pip güncelleme ────────────────────────────────────────
info "pip güncelleniyor..."
pip install --upgrade pip --quiet
success "pip güncellendi"

# ── 5. Bağımlılıklar ─────────────────────────────────────────
info "Python bağımlılıkları yükleniyor..."
pip install -r requirements.txt --quiet
success "Bağımlılıklar yüklendi"

# ── 6. Playwright tarayıcı ───────────────────────────────────
info "Playwright Chromium tarayıcısı yükleniyor..."
playwright install chromium
success "Chromium yüklendi"

# ── 7. Klasör yapısı ─────────────────────────────────────────
info "Klasör yapısı oluşturuluyor..."
mkdir -p data/downloads
success "data/downloads/ hazır"

# ── 8. yt-dlp kontrolü ───────────────────────────────────────
info "yt-dlp kontrol ediliyor..."
if python3 -c "import yt_dlp" &>/dev/null; then
    YT_VERSION=$(python3 -c "import yt_dlp; print(yt_dlp.version.__version__)")
    success "yt-dlp $YT_VERSION hazır"
else
    warn "yt-dlp yüklenemedi, video indirme çalışmayabilir"
fi

# ── 9. customtkinter kontrolü ────────────────────────────────
info "GUI bağımlılıkları kontrol ediliyor..."
if python3 -c "import customtkinter" &>/dev/null; then
    success "customtkinter hazır"
else
    error "customtkinter yüklenemedi"
fi

# ── Tamamlandı ───────────────────────────────────────────────
echo ""
echo "  ───────────────────────────────────────────"
success "Kurulum tamamlandı!"
echo ""
echo "  Uygulamayı başlatmak için:"
echo ""
echo -e "    ${GREEN}source .venv/bin/activate${NC}"
echo -e "    ${GREEN}python main.py${NC}"
echo ""
echo "  ─────────────────────────────────────────────"
echo ""
