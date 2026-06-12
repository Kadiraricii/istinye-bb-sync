from pathlib import Path

# ── Paths ────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
DATA_DIR      = BASE_DIR / "data"
DOWNLOADS_DIR = DATA_DIR / "downloads"
MANIFEST_FILE = DATA_DIR / "manifest.json"
PROGRESS_FILE = DATA_DIR / "progress.json"
REMEMBER_FILE = DATA_DIR / "remember.json"

# ── Blackboard ───────────────────────────────────────────────
BB_BASE         = "https://istinye.blackboard.com"
BB_ULTRA        = "https://istinye.blackboard.com/ultra"
BB_API          = "https://istinye.blackboard.com/learn/api/public/v1"
EMAIL_DOMAIN    = "@stu.istinye.edu.tr"

# ── HTTP ─────────────────────────────────────────────────────
REQUEST_DELAY_MIN  = 0.5   # saniye — istekler arası minimum bekleme
REQUEST_DELAY_MAX  = 1.5   # saniye — istekler arası maksimum bekleme
MAX_RETRIES        = 3
REQUEST_TIMEOUT    = 30    # saniye
DOWNLOAD_CHUNK     = 65536 # 64 KB

# ── İndirme ──────────────────────────────────────────────────
DEFAULT_CONCURRENT = 2     # varsayılan eş zamanlı indirme sayısı
LARGE_FILE_MB      = 50    # bu MB üzerindeki dosyalar için uyarı

# Boş/bozuk dosya koruması — minimum kabul edilebilir boyutlar (byte)
MIN_FILE_SIZES = {
    "pdf":   1_024,    # 1 KB
    "pptx":  5_120,    # 5 KB
    "ppt":   5_120,
    "docx":  1_024,
    "doc":   1_024,
    "xlsx":  1_024,
    "xls":   1_024,
    "zip":   512,
    "rar":   512,
    "video": 102_400,  # 100 KB
    "image": 512,
    "other": 512,
}

# ── Video ─────────────────────────────────────────────────────
SHAREPOINT_DOMAINS = ["sharepoint.com", "microsoftstream.com"]
VIDEO_QUALITIES    = ["best", "1080", "720", "worst"]
DEFAULT_QUALITY    = "720"

# ── GUI Renk Paleti (Deep Navy + Emerald) ─────────────────────
BG_BASE      = "#070a12"   # gece mavisi
BG_ELEVATED  = "#0d1120"   # koyu lacivert kart
BG_HOVER     = "#131828"   # hover lacivert
BORDER       = "#1c2440"   # çelik mavi kenarlık
BORDER_FAINT = "#111830"   # çok ince kenarlık

TEXT_PRIMARY   = "#e2eaf6"   # mavi-beyaz
TEXT_SECONDARY = "#526d8a"   # çelik mavi
TEXT_TERTIARY  = "#2a3d55"   # çok soluk

ACCENT     = "#10b981"   # emerald-500
ACCENT_BG  = "#052e1c"   # koyu emerald arka plan
SUCCESS    = "#34d399"   # emerald-400
WARNING    = "#f59e0b"   # amber
ERROR      = "#f43f5e"   # gül kırmızı
INFO       = "#60a5fa"   # blue-400

# ── GUI Boyutlar ──────────────────────────────────────────────
WINDOW_WIDTH   = 720
WINDOW_HEIGHT  = 700
COMPACT_HEIGHT = 48
CORNER_RADIUS  = 6
