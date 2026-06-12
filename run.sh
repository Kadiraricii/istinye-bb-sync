#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
#  Blackboard Downloader — Başlatıcı
#  Kullanım: ./run.sh
# ─────────────────────────────────────────────────────────────

if [[ ! -d ".venv" ]]; then
    echo "[!] .venv bulunamadı. Önce kurulumu yapın: ./setup.sh"
    exit 1
fi

# shellcheck source=/dev/null
source .venv/bin/activate

python main.py "$@"
