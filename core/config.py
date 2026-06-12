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

# ── GUI Renk Paleti (Ocean Dark) ──────────────────────────────
BG_BASE      = "#02091a"   # derin uzay mavisi
BG_ELEVATED  = "#071628"   # gece yarısı lacivert
BG_HOVER     = "#0d2040"   # hover lacivert
BORDER       = "#163d6e"   # çelik mavi kenarlık
BORDER_FAINT = "#0b1e38"

TEXT_PRIMARY   = "#dbeafe"   # soğuk beyaz
TEXT_SECONDARY = "#5b8db8"   # pastel mavi
TEXT_TERTIARY  = "#2d5070"   # soluk mavi-gri

ACCENT     = "#0ea5e9"   # gökyüzü mavisi (canlı)
ACCENT_BG  = "#062240"
SUCCESS    = "#10b981"   # zümrüt yeşili
WARNING    = "#f59e0b"   # kehribar
ERROR      = "#f43f5e"   # gül kırmızısı
INFO       = "#38bdf8"   # açık mavi

# ── GUI Boyutlar ──────────────────────────────────────────────
WINDOW_WIDTH   = 720
WINDOW_HEIGHT  = 700
COMPACT_HEIGHT = 48
CORNER_RADIUS  = 6
