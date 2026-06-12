from pathlib import Path

# ── Paths ────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
DATA_DIR      = BASE_DIR / "data"
DOWNLOADS_DIR = DATA_DIR / "downloads"
MANIFEST_FILE = DATA_DIR / "manifest.json"
PROGRESS_FILE = DATA_DIR / "progress.json"

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

# ── GUI Renk Paleti (Dark Precision) ─────────────────────────
BG_BASE      = "#09090b"
BG_ELEVATED  = "#18181b"
BG_HOVER     = "#27272a"
BORDER       = "#3f3f46"
BORDER_FAINT = "#27272a"

TEXT_PRIMARY   = "#fafafa"
TEXT_SECONDARY = "#a1a1aa"
TEXT_TERTIARY  = "#71717a"

ACCENT     = "#818cf8"
ACCENT_BG  = "#1e1b4b"
SUCCESS    = "#4ade80"
WARNING    = "#fbbf24"
ERROR      = "#f87171"
INFO       = "#60a5fa"

# ── GUI Boyutlar ──────────────────────────────────────────────
WINDOW_WIDTH   = 720
WINDOW_HEIGHT  = 700
COMPACT_HEIGHT = 48
CORNER_RADIUS  = 6
