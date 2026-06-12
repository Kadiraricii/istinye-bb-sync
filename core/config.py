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

# ── GUI Renk Paleti (Midnight Indigo) ─────────────────────────
BG_BASE      = "#0a0a0f"   # near-black, çok hafif indigo tonu
BG_ELEVATED  = "#111118"   # kart yüzeyi
BG_HOVER     = "#18182a"   # hover durumu
BORDER       = "#242438"   # ince kenarlık
BORDER_FAINT = "#16162a"   # çok soluk kenarlık

TEXT_PRIMARY   = "#e8e8f0"   # soğuk beyaz
TEXT_SECONDARY = "#7878a0"   # soluk slate
TEXT_TERTIARY  = "#353550"   # çok soluk

ACCENT     = "#5e6ad2"   # Linear indigo-mavi (2025 trendi)
ACCENT_BG  = "#0a0c28"
SUCCESS    = "#16c784"   # canlı yeşil
WARNING    = "#f7a71c"   # kehribar
ERROR      = "#e54d2e"   # domates kırmızı
INFO       = "#7db0d8"   # pastel mavi

# ── GUI Boyutlar ──────────────────────────────────────────────
WINDOW_WIDTH   = 720
WINDOW_HEIGHT  = 700
COMPACT_HEIGHT = 48
CORNER_RADIUS  = 6
