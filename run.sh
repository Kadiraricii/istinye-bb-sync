#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
#  Blackboard Downloader — Başlatıcı
#  Kullanım: ./run.sh        → normal başlatma
#           ./run.sh --dev   → kod değişince otomatik yeniden başlatma
# ─────────────────────────────────────────────────────────────

if [[ ! -d ".venv" ]]; then
    echo "[!] .venv bulunamadı. Önce kurulumu yapın: ./setup.sh"
    exit 1
fi

# shellcheck source=/dev/null
source .venv/bin/activate

if [[ "${1:-}" == "--dev" ]]; then
    python dev.py
else
    python main.py "$@"
fi
