# Blackboard Material Downloader — Plan

## Genel Bakış

Istinye Üniversitesi Blackboard Ultra sistemindeki tüm ders materyallerini
kurs kurs, iteratif ve devam ettirilebilir biçimde indiren bir Python aracı.

---

## GUI Tasarımı

### Tasarım Yönü: "Dark Precision"
Linear, Warp Terminal, Raycast gibi araçların estetik dili.
Gereksiz dekorasyon yok. Her piksel işlevsel. Derinlik border ve ton
farklılıklarıyla oluşuyor, gölge ve efektle değil.

### Renk Paleti — Zinc Scale (Tailwind/shadcn referansı)
```
# Arka planlar (katmanlı derinlik)
BG_BASE      = #09090b   ← neredeyse siyah (zinc-950)
BG_ELEVATED  = #18181b   ← kart/panel zemini (zinc-900)
BG_HOVER     = #27272a   ← hover state (zinc-800)

# Sınırlar
BORDER       = #3f3f46   ← görünür border (zinc-700)
BORDER_FAINT = #27272a   ← ince ayırıcı (zinc-800)

# Metin
TEXT_PRIMARY   = #fafafa  ← başlık ve önemli içerik (zinc-50)
TEXT_SECONDARY = #a1a1aa  ← açıklama ve etiketler (zinc-400)
TEXT_TERTIARY  = #71717a  ← placeholder ve soluk bilgi (zinc-500)

# Accent — sadece kritik aksiyon butonlarında kullanılır, başka yerde değil
ACCENT        = #818cf8   ← indigo-400, tek accent rengi
ACCENT_BG     = #1e1b4b   ← indigo-950, accent arka planı

# Semantik renkler
SUCCESS  = #4ade80   ← green-400
WARNING  = #fbbf24   ← amber-400
ERROR    = #f87171   ← red-400
INFO     = #60a5fa   ← blue-400
```

### Tipografi
```
Boyut hiyerarşisi:
  32px  weight:700  → ekran başlığı (sadece login)
  20px  weight:600  → section başlığı
  14px  weight:400  → body, liste içerikleri
  12px  weight:400  → caption, etiket, tarih
  13px  monospace   → dosya adları, boyutlar, log satırları, %

Font: System font stack
  macOS:   SF Pro Display / SF Mono
  Windows: Segoe UI / Consolas
  Linux:   Inter / DejaVu
```

### Spacing Ritmi
```
4px  — ikon/metin arası
8px  — satır içi elemanlar
12px — kompakt bölümler
16px — standart padding
24px — bölüm arası
32px — ekran kenar boşluğu
```

### Border Radius
```
4px  — input alanları, küçük chip'ler
6px  — butonlar, kartlar
8px  — büyük panel ve modal
```

### Buton Tipleri
```
Primary   → BG: ACCENT (#818cf8), text: beyaz — sadece ana aksiyon
Secondary → BG: BG_ELEVATED, border: BORDER, text: TEXT_PRIMARY
Ghost     → BG: şeffaf, hover'da BG_HOVER — ikincil aksiyonlar
Danger    → BG: şeffaf, text: ERROR — iptal, silme
```

---

### Ekran 1 — Login
```
 ┌────────────────────────────────────────────────────┐
 │                                                    │  #09090b
 │                                                    │
 │              BLACKBOARD                            │  32px 700 #fafafa
 │              Downloader                            │  16px 400 #71717a
 │                                                    │
 │         ┌──────────────────────────────────┐       │
 │         │                                  │       │  BG_ELEVATED
 │         │  Öğrenci Numarası                │       │  12px #a1a1aa
 │         │  ┌────────────────────────────┐  │       │
 │         │  │ 2200000000                 │  │       │  input: BG_BASE
 │         │  └────────────────────────────┘  │       │  border: #3f3f46
 │         │  2200000000@stu.istinye.edu.tr    │       │  12px #71717a
 │         │                                  │       │
 │         │  Şifre                    [👁]   │       │
 │         │  ┌────────────────────────────┐  │       │
 │         │  │ ················           │  │       │
 │         │  └────────────────────────────┘  │       │
 │         │                                  │       │
 │         │  ┌────────────────────────────┐  │       │  ACCENT BG
 │         │  │    Tarayıcıda Giriş Yap   │  │       │  #818cf8
 │         │  └────────────────────────────┘  │       │
 │         │                                  │       │
 │         │  ● Hazır                         │       │  dot: #4ade80
 │         └──────────────────────────────────┘       │
 │                                                    │
 └────────────────────────────────────────────────────┘

Status geçişleri:
  ● Hazır          →  #71717a  (gri dot)
  ⟳ Bağlanıyor...  →  #fbbf24  (amber, animate)
  ✓ Giriş yapıldı  →  #4ade80  (yeşil)
  ✗ Hata           →  #f87171  (kırmızı)
```

---

### Ekran 2 — Ders Keşfi (Yükleniyor)
```
 ┌────────────────────────────────────────────────────┐
 │                                                    │
 │  Dersler                                          │  20px 600
 │  ────────────────────────────────────────────     │  #27272a
 │                                                    │
 │              ╔══╗  ╔══╗  ╔══╗                    │
 │              ╚══╝  ╚══╝  ╚══╝                    │  3 nokta
 │           Blackboard'dan dersler alınıyor         │  animate: left→right
 │                                                    │
 │  ┌──────────────────────────────────────────────┐ │
 │  │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ │  skeleton card
 │  └──────────────────────────────────────────────┘ │  shimmer efekti
 │  ┌──────────────────────────────────────────────┐ │
 │  │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ │
 │  └──────────────────────────────────────────────┘ │
 │                                                    │
 └────────────────────────────────────────────────────┘

  Skeleton kartlar (#18181b → #27272a shimmer animasyonu)
```

---

### Ekran 2 — Ders Seçimi (Yüklendi)
```
 ┌────────────────────────────────────────────────────┐
 │  ← Geri   Dersler          Tümünü Seç  Temizle    │
 │  ─────────────────────────────────────────────     │
 │  ┌──────────────────────────────────────────────┐  │
 │  │ ⌕  Ders ara...                               │  │  input
 │  └──────────────────────────────────────────────┘  │
 │                                                    │
 │  ┌─────────────────────┐  ┌─────────────────────┐  │
 │  │ ▣  BGT107           │  │ ▣  MAT101           │  │  BG_ELEVATED
 │  │ Bilgisayara Giriş   │  │ Matematik I         │  │  border: #3f3f46
 │  │ ─────────────────   │  │ ──────────────────  │  │  #27272a
 │  │  12 dosya  4 video  │  │  8 dosya  0 video   │  │  12px #a1a1aa
 │  │  ~45 MB             │  │  ~12 MB             │  │  13px mono
 │  └─────────────────────┘  └─────────────────────┘  │
 │                                                    │
 │  ┌─────────────────────┐  ┌─────────────────────┐  │
 │  │ □  ING101           │  │ ▣  FIZ101           │  │  seçilmemiş
 │  │ İngilizce           │  │ Fizik               │  │  border: #27272a
 │  │ ─────────────────   │  │ ──────────────────  │  │  soluk
 │  │  5 dosya   2 video  │  │  20 dosya  6 video  │  │
 │  │  ~8 MB              │  │  ~120 MB            │  │
 │  └─────────────────────┘  └─────────────────────┘  │
 │                                                    │
 │  ~/Downloads/Blackboard              [Değiştir]   │  #71717a
 │  ────────────────────────────────────────────────  │
 │  3 ders seçili  ·  ~177 MB               [ → ]    │  14px  ACCENT btn
 └────────────────────────────────────────────────────┘

Seçili kart:  border: #818cf8 (accent), checkbox: ▣ dolu
Seçilmemiş:  border: #27272a, checkbox: □ boş, opacity: 0.6
Hover:       BG_HOVER (#27272a), border: #3f3f46
```

---

### Ekran 3 — Filtreler
```
 ┌────────────────────────────────────────────────────┐
 │  ← Geri   Filtreler                               │
 │  ─────────────────────────────────────────────     │
 │                                                    │
 │  ┌────────────┐  ┌──────────────┐  ┌──────────┐  │
 │  │ Dosya Türü │  │  Boyut/Tarih │  │  Video   │  │  tab: ghost
 │  └────────────┘  └──────────────┘  └──────────┘  │  aktif: border-b accent
 │  ─────────────                                     │
 │                                                    │
 │  ▣  PDF                            .pdf            │
 │  ▣  Sunum                          .pptx .ppt      │
 │  ▣  Doküman                        .docx .doc      │
 │  ▣  Tablo                          .xlsx .xls      │
 │  ▣  Resim                          .jpg .png       │
 │  ▣  Arşiv                          .zip .rar       │
 │  □  SCORM                          paket           │
 │  ▣  Diğer                                          │
 │                                                    │
 │  ────────────────────────────────────────────────  │
 │  94 dosya  ·  1.2 GB indirilecek                  │  #a1a1aa
 │                                         [ Başlat ] │  ACCENT btn
 └────────────────────────────────────────────────────┘
```

---

### Ekran 4 — İndirme (Tam Boyut)
```
 ┌────────────────────────────────────────────────────────┐
 │  İndirme  72/94               [Sabitle] [Tarayıcı] [⏸] │
 │  ──────────────────────────────────────────────────    │
 │                                                        │
 │  ┌──────────────────────────────────────────────────┐  │
 │  │ ████████████████████░░░░░░░░  72%  · 1.2/1.7 GB │  │  progress
 │  └──────────────────────────────────────────────────┘  │  #818cf8 fill
 │                                                        │
 │  Hafta3_Turevler.pdf                                   │  14px
 │  ┌──────────────────────────────────────────────────┐  │
 │  │ ████████████░░░░░░░░  61%  ·  1.3 / 2.1 MB      │  │  #27272a fill
 │  └──────────────────────────────────────────────────┘  │
 │                                                        │
 │  ┌──────────────────────────────────────────────────┐  │
 │  │  ✓  BGT107  Bilgisayara Giriş    12/12  45 MB   │  │  #4ade80 dot
 │  │  ·  MAT101  Matematik I           5/8   ████░   │  │  #818cf8 progress
 │  │  ○  FIZ101  Fizik                 0/20          │  │  #3f3f46 dot
 │  └──────────────────────────────────────────────────┘  │
 │                                                        │
 │  Log                                           [Temizle]│  12px #71717a
 │  ┌──────────────────────────────────────────────────┐  │
 │  │  ✓  Hafta1_Sunum.pdf                            │  │  13px mono
 │  │  ✓  Hafta2_Diziler.pdf                          │  │  #4ade80
 │  │  ─  video_links.txt  (3 link kaydedildi)        │  │  #a1a1aa
 │  │  !  Hafta4_Odev.docx  retry 1/3                 │  │  #fbbf24
 │  └──────────────────────────────────────────────────┘  │
 └────────────────────────────────────────────────────────┘
```

### Ekran 4 — Kompakt Mod
```
 ┌────────────────────────────────────────────────────────────────┐
 │  ████████████░░░░  72%    Hafta3_Turevler.pdf    [↕] [⏸] [✕]  │
 └────────────────────────────────────────────────────────────────┘
  Yükseklik: 48px  ·  her zaman topmost  ·  ekranın alt köşesine sabitlenir
```

---

### Animasyonlar
```
Skeleton loading:   #18181b → #27272a → #18181b   shimmer (200ms loop)
Kart fade-in:       opacity 0→1 + translateY 8→0px (staggered, 60ms aralık)
Progress bar:       smooth interpolation, jerky jump yok
Status dot:         scale 1→1.2→1 pulse (waiting states için)
Kompakt geçiş:      window height 480→48px (100ms ease-out)
Log satırı:         opacity 0→1 (40ms)
Hover state:        background color 80ms ease
```

---

## GUI Tech Stack

**CustomTkinter** kullanacağız:
- Modern görünüm (dark/light mode)
- Tamamen Python, ek server yok
- tkinter üzerine inşa → kurulum kolay
- Desktop app olarak çalışır

---

## Teknik Keşif Sonuçları (Araştırma Bulguları)

### Blackboard REST API (Cookie Auth — OAuth Gerekmez!)
Blackboard'un `/learn/api/public/v1/` API'si, tarayıcı session cookie'siyle
doğrudan çalışır. OAuth uygulama kaydı gerekmez.

```
Ana endpoint'ler:
  GET /learn/api/public/v1/users/me/courses          → kayıtlı dersler
  GET /learn/api/public/v1/courses/{id}/contents     → ders içerikleri
  GET /learn/api/public/v1/courses/{id}/contents/{id}/children   → alt klasörler
  GET /learn/api/public/v1/courses/{id}/contents/{id}/attachments → dosyalar
  GET /learn/api/public/v1/courses/{id}/contents/{id}/attachments/{id}/download → indir (302 redirect)
```

### Session Cookie
```
BbRouter    ← Ana session token (bu tek başına yeterli çoğu zaman)
JSESSIONID  ← Java session
```

### Istinye SSO Akışı
Istinye üniversitesi **Microsoft Azure AD SAML/SSO** kullanıyor:
```
istinye.blackboard.com → Microsoft login → SAML assertion → BbRouter cookie set
```
Playwright headless=False ile login → cookies kaydedilir → sonraki tüm istekler requests ile yapılır.

### DOM Selectors (Playwright fallback için)
```css
a[href*="/ultra/courses/"]              /* course links on dashboard */
[data-testid="content-list-item"]       /* content items */
a[href*="/bbcswebdav/"]                 /* direct file links */
a[href*="/learn/api/public/v1/courses/"][href*="/download"]  /* API download links */
```

### Dosya URL Formatları
```
/bbcswebdav/pid-{PID}-dt-content-rid-{RID}_1/courses/{COURSE_ID}/{filename}
/learn/api/public/v1/courses/{id}/contents/{id}/attachments/{id}/download  → 302 → gerçek dosya
```

---

## Tech Stack (Güncellenmiş)

| Bileşen | Seçim | Neden |
|---------|-------|-------|
| Dil | Python 3.11+ | Olgun ekosistem, temiz syntax |
| Login | `playwright` headless=False | SSO/MFA için görünür tarayıcı |
| API çağrıları | `requests` + session cookie | REST API'yi hızlı sorgular, Playwright overhead yok |
| Dosya indirme | `httpx` async | Stream indirme, chunk kontrolü |
| Video indirme | `yt-dlp` | SharePoint Stream + 1000+ site |
| GUI | `customtkinter` | Modern desktop UI |
| State | JSON | Basit, elle düzenlenebilir |

### Hibrit Mimari (Kritik Karar)
```
Playwright → sadece Login (SSO/MFA için görünür tarayıcı gerekli)
    ↓
Cookie (BbRouter) → requests.Session'a aktarılır
    ↓
requests.Session → tüm REST API çağrıları (hızlı, hafif)
    ↓
httpx → dosya indirme (async stream)
    ↓
yt-dlp → video indirme (SharePoint/YouTube vs.)
    ↓
Playwright fallback → REST API'de bulunmayan içerikler için
```

Bu sayede login dışında tarayıcı overhead'i yok → çok daha hızlı.

---

## Video Platform: Microsoft SharePoint Stream

Istinye Üniversitesi videoları `istinye-my.sharepoint.com` üzerinde barındırılıyor.
Örnek URL formatı:
```
https://istinye-my.sharepoint.com/personal/{ogretmen}_istinye_edu_tr/
  _layouts/15/stream.aspx?id=/personal/.../DersAdi.mp4
```

### Video İndirme Stratejisi

```
1. Playwright ile Blackboard'a login ol
2. SharePoint'e de aynı Microsoft hesabıyla erişim sağlanır
   (Istinye → Microsoft 365 SSO)
3. Playwright'ın browser cookie'lerini al
4. yt-dlp'ye cookie'leri geçir → video indir
```

### Neden Bu Çalışır
- `yt-dlp --cookies-from-browser` veya cookie string desteği var
- SharePoint Stream, `yt-dlp` extractor listesinde mevcut
- Aynı Microsoft session kullanıldığından ek login gerekmez

### GUI'de Video Seçeneği (İçerik Filtresi Güncellemesi)
```
☑ PDF / Sunum / Doküman
☑ Resim & Grafik
● Video:  ○ İndir (yt-dlp)   ● Link olarak kaydet
☑ Harici linkler (txt olarak)

  Video kalitesi: [ En yüksek ▼ ]   (sadece "İndir" seçilince)
  720p / 1080p / En yüksek / En düşük
```

---

## Proje Yapısı

```
blackboard/
├── PLAN.md
├── requirements.txt
├── main.py               ← giriş noktası, CLI
├── config.py             ← sabitler, domain ayarları
├── auth.py               ← login akışı
├── crawler.py            ← kurs + içerik keşfi
├── downloader.py         ← dosya indirme
├── state.py              ← progress.json okuma/yazma
├── models.py             ← dataclass tanımları
└── data/
    ├── progress.json     ← indirme durumu (auto-generated)
    ├── manifest.json     ← keşfedilen tüm içerik (auto-generated)
    └── downloads/
        ├── BilgisayarMuh101/
        │   ├── Hafta1_Giris.pdf
        │   └── video_links.txt
        └── Matematik201/
            └── ...
```

---

## Login Akışı

```
1. Script başlar
2. Kullanıcıdan öğrenci numarası istenir (terminal)
3. Tarayıcı açılır → Blackboard login sayfası
4. Email alanına otomatik: {numara}@stu.istinye.edu.tr yazılır
5. Şifre alanı odaklanır → kullanıcı şifreyi kendisi yazar
6. Kullanıcı Enter'a basar → login
7. Dashboard'a yönlenince session cookie'leri kaydedilir
8. Tarayıcı arka planda çalışmaya devam eder
```

> **Güvenlik:** Şifre hiçbir zaman script'te saklanmaz, dosyaya yazılmaz.
> Cookie'ler sadece session süresince bellekte tutulur.

---

## Aşamalar (Iteratif)

### Aşama 1 — Kurs Keşfi
```
Girdi : Login olunmuş session
Çıktı : manifest.json (kurs listesi)

- Dashboard'daki tüm kursları tara
- Her kurs için: id, isim, URL kaydet
- manifest.json'a yaz
```

### Aşama 2 — İçerik Haritası (kurs kurs)
```
Girdi : manifest.json (kurs listesi)
Çıktı : manifest.json güncellenir (item listesi)

- Her kursu sırayla aç
- İçerik ağacını recursive olarak gez:
    Kurs → Klasör → Alt Klasör → Dosya/Video/Link
- Her item için kaydet:
    - id, isim, tip, indirme URL'i, boyut
- Kurs tamamlanınca status: "crawled" yaz
- Hata olursa status: "crawl_failed", sonraki kursa geç
```

### Aşama 3 — İndirme (item item)
```
Girdi : manifest.json (item listesi)
Çıktı : downloads/ klasörü, progress.json

- Manifest'i oku
- status: "pending" olan item'ları al
- Sırayla indir:
    PDF/DOC/PPT → downloads/{kurs}/{dosya}
    Video       → downloads/{kurs}/video_links.txt'e ekle
    Link        → downloads/{kurs}/links.txt'e ekle
    SCORM       → downloads/{kurs}/scorm_links.txt'e ekle
- Her başarılı indirmede progress.json güncelle
- Hata olursa status: "failed" yaz, devam et
```

### Aşama 4 — Retry / Güncelleme
```
- main.py --retry ile sadece "failed" item'lar tekrar denenir
- main.py --sync ile yeni eklenen içerikler yakalanır
- Zaten indirilenler atlanır (idempotent)
```

---

## State Dosyaları

### manifest.json
```json
{
  "generated_at": "2026-06-12T10:00:00",
  "courses": {
    "courseId_ABC": {
      "name": "Bilgisayar Mühendisliğine Giriş",
      "url": "...",
      "status": "crawled",
      "items": {
        "itemId_XYZ": {
          "name": "Hafta1_Sunum.pdf",
          "type": "pdf",
          "download_url": "...",
          "size_bytes": 2048000,
          "path_hint": "Hafta 1 → Ders Notları"
        }
      }
    }
  }
}
```

### progress.json
```json
{
  "last_run": "2026-06-12T11:30:00",
  "stats": {
    "total": 120,
    "downloaded": 95,
    "failed": 3,
    "skipped": 22
  },
  "items": {
    "itemId_XYZ": {
      "status": "downloaded",
      "local_path": "downloads/BilgisayarMuh101/Hafta1_Sunum.pdf",
      "downloaded_at": "2026-06-12T11:00:00"
    },
    "itemId_ABC": {
      "status": "failed",
      "error": "403 Forbidden",
      "attempts": 2
    }
  }
}
```

---

## İçerik Tipi Mapping

| Blackboard Tipi | Varsayılan Aksiyon | Alternatif |
|----------------|-------------------|------------|
| PDF / DOCX / PPTX / XLSX | İndir → dosya | — |
| Video (SharePoint Stream) | `yt-dlp` ile indir | URL → `video_links.txt` |
| Video (diğer: YouTube vs.) | URL → `video_links.txt` | `yt-dlp` ile indir |
| Harici link | URL → `links.txt` | — |
| SCORM paketi | URL → `scorm_links.txt` | — |
| Inline metin | HTML → `.html` dosyası | — |
| Resim | İndir → dosya | — |

### video_links.txt Formatı
```
# Bilgisayara Giriş — Video Linkleri
# Otomatik oluşturuldu: 2026-06-12

[Hafta 1 - Giriş Dersi]
https://istinye-my.sharepoint.com/...

[Hafta 2 - Değişkenler]
https://istinye-my.sharepoint.com/...
```

Manuel indirmek için:
```bash
yt-dlp --cookies-from-browser chrome -a video_links.txt
```

---

## CLI Kullanım

```bash
# İlk kurulum
pip install -r requirements.txt
playwright install chromium

# Tam çalıştırma (keşif + indirme)
python main.py

# Sadece belirli kurs
python main.py --course "Matematik"

# Sadece başarısızları tekrar dene
python main.py --retry

# Yeni içerik kontrolü (sync)
python main.py --sync

# Kuru çalıştırma (ne indireceğini göster, indirme)
python main.py --dry-run
```

---

## Hata Yönetimi

| Durum | Davranış |
|-------|----------|
| 403 / 404 | `failed` yaz, devam et |
| Network timeout | 3 retry, sonra `failed` |
| Login süresi doldu | Otomatik re-login dene |
| Disk dolu | Dur, kullanıcıyı uyar |
| Beklenmedik sayfa yapısı | Log yaz, item'ı `skipped` yap |

---

## Geliştirme Sırası

- [ ] **Sprint 1** — `models.py` + `state.py` + `config.py`
- [ ] **Sprint 2** — `auth.py` (login akışı, email otofill)
- [ ] **Sprint 3** — `crawler.py` Aşama 1 (kurs listesi)
- [ ] **Sprint 4** — `crawler.py` Aşama 2 (içerik ağacı)
- [ ] **Sprint 5** — `downloader.py` (dosya indirme)
- [ ] **Sprint 6** — `gui/` CustomTkinter ekranları
- [ ] **Sprint 7** — GUI ↔ backend bağlantısı (threading)
- [ ] **Sprint 8** — Test + hata düzeltme

## Güncellenmiş Proje Yapısı

```
blackboard/
├── PLAN.md
├── requirements.txt
├── main.py               ← GUI başlatıcı
├── config.py
├── auth.py
├── crawler.py
├── downloader.py
├── state.py
├── models.py
├── gui/
│   ├── __init__.py
│   ├── app.py            ← Ana pencere, ekran geçişleri
│   ├── screen_login.py   ← Ekran 1
│   ├── screen_courses.py ← Ekran 2
│   ├── screen_filter.py  ← Ekran 3
│   └── screen_progress.py← Ekran 4
└── data/
    ├── progress.json
    ├── manifest.json
    └── downloads/
```

---

## Kararlaştırılmış Özellikler (Detaylı)

### 1 — Klasör Yapısı

Blackboard'daki klasör hiyerarşisi birebir yansıtılır:

```
downloads/
└── BilgisayarMuh101/
    ├── Ders1/                  ← hoca böyle klasör açtıysa
    │   ├── sunum.pdf
    │   └── odev.docx
    ├── Ders2/                  ← boş klasör → klasör oluşur, içi boş
    └── vize_notu.pdf           ← klasörsüz dosya → direkt kurs klasörüne
```

- Hoca klasör açtıysa → aynı isimde klasör oluştur, içeriği oraya koy
- Hoca boş klasör açtıysa → klasör oluşturulur, içi boş kalır
- Hoca hiç klasör yapmadıysa → dosyalar direkt kurs klasörüne gider
- Alt klasörler de birebir kopyalanır (recursive)

---

### 2 — Dosya İsimlendirme

- **Türkçe → ASCII dönüşümü** (ş→s, ç→c, ğ→g, ı→i, ö→o, ü→u)
- Boşluk → `_`
- Özel karakterler (`/`, `*`, `?`, `"`, `<`, `>`, `|`) → kaldırılır
- Aynı isimde dosya varsa: `dosya_2.pdf`, `dosya_3.pdf` şeklinde devam
- Örnek: `Ünite 3 — Şablonlar.pdf` → `Unite_3_Sablonlar.pdf`

---

### 3 — Sync (Yeni İçerik Tespiti)

- Uygulama açılınca manifest ile Blackboard karşılaştırılır
- Yeni eklenen dosyalar tespit edilir, kullanıcıya bildirilir
- Hata oranını düşürmek için:
  - Sadece kesin "yeni" dosyalar işaretlenir (tarih veya ID farkı)
  - Şüpheli olanlar `review` olarak işaretlenir, kullanıcı karar verir

---

### 4 — Filtreleme Sistemi (Detaylı)

Bkz. aşağıdaki "Filtreleme Sistemi" bölümü.

---

### 5 — Bant Genişliği Yönetimi

**Strateji: Asyncio Semaphore ile Concurrent İndirme**

```
Kullanıcı seçer:
  ○ Tek tek (1 eş zamanlı) — en güvenli, yavaş
  ● İkili (2 eş zamanlı)   — önerilen
  ○ Hızlı (5 eş zamanlı)  — hızlı ama sunucuya yük
```

- Dosyalar arası otomatik bekleme: 0.5–1.5 sn (rastgele, sunucuya yük bindirmemek için)
- Video indirme (yt-dlp) her zaman tek tek yapılır (yt-dlp kendi yönetir)
- Büyük dosyalar (>50MB) önce uyarı gösterilir

---

### 6 — Tarayıcı Yönetimi

**Tarayıcı Kapatılınca:**
```
┌──────────────────────────────┐
│  ⚠ Tarayıcı kapatıldı       │
│                              │
│  İndirme işlemi yarıda kaldı.│
│  Devam etmek istiyor musunuz?│
│                              │
│   [ Evet, Devam Et ]  [ Hayır ]│
└──────────────────────────────┘
```
- Evet → Playwright yeni tarayıcı açar, kaldığı yerden devam eder
- Hayır → İşlem durur, progress.json güncellenir, pencere kapanır

**GUI Davranışı:**
- GUI her zaman tarayıcının **üstünde** kalır (`-topmost` flag)
- "📌 Üstte Tut" toggle butonu: açık/kapalı yapılabilir
- "🌐 Tarayıcıyı Göster" butonu: gizlenen tarayıcıyı öne getirir

**Kompakt Mod:**
- İndirme başlayınca GUI küçük bir şeride dönüşür (200×80 px)
- Sadece: progress bar + mevcut dosya adı + butonlar
- Tarayıcıyla yan yana çalışmak için ideal
- "↕ Genişlet" butonuyla tam boyuta döner

```
┌─────────────────────────────────────────┐
│ ⬛⬛⬛⬛⬛⬛⬛⬛░░░░  72%  Hafta3.pdf  [↕][🌐][⏸]│
└─────────────────────────────────────────┘
```

---

### 7 — Oturum Yönetimi

- Cookie kaydedilmez
- Her açılışta taze login gerekir
- Şifre hiçbir zaman diske yazılmaz

---

## Filtreleme Sistemi (Sprint 4 — Detaylı)

### Filtre Kategorileri

**Dosya Türü:**
```
☑ PDF (.pdf)
☑ Sunum (.pptx, .ppt)
☑ Doküman (.docx, .doc)
☑ Tablo (.xlsx, .xls)
☑ Resim (.jpg, .png, .gif, .svg)
☑ Video — İndir (yt-dlp)
☑ Video — Link kaydet
☑ Arşiv (.zip, .rar)
☐ SCORM paketleri
☑ Diğer dosyalar
```

**Boyut Filtresi:**
```
Min: [____] MB    Max: [____] MB
○ Tümü   ● 0–50MB   ○ 50–200MB   ○ 200MB+
```

**Tarih Filtresi:**
```
☐ Sadece yeni dosyalar (son indirmeden sonra eklenenler)
☐ Tarih aralığı: [__/__/____] — [__/__/____]
```

**İsim Filtresi:**
```
Anahtar kelime: [_______________]
(dosya adında geçen metni filtreler)
```

**Kurs / Klasör Filtresi:**
- Ders seçimi ekranında zaten kurs bazlı seçim var
- Burada ek olarak klasör bazlı dahil/hariç tut

**Video Kalitesi (yt-dlp için):**
```
○ En yüksek
● 1080p
○ 720p
○ En düşük (hızlı indirme)
```

### Filtre Mantığı — İki Aşamalı (Option C)

**Aşama 1 — Kaba Filtre (Keşif Sırasında)**
```
Kullanıcı daha başlamadan filtre seçer:
  ☑ PDF  ☑ Sunum  ☐ Video  ...

Crawler bu tipleri manifest'e hiç eklemez.
→ Hem zaman kazanır, hem manifest temiz kalır.
```

**Aşama 2 — İnce Filtre (İndirme Öncesi)**
```
Manifest hazır, indirme başlamadan önce uygulanır:
  - Boyut filtresi (size_bytes manifest'te var)
  - Tarih filtresi (upload_date manifest'te var)
  - Anahtar kelime (dosya adı üzerinde)

→ "128 dosya bulundu, 94'ü filtre kriterleri karşılıyor (1.2 GB)"
→ Kullanıcı onaylar → indir
```

**Filtre Sonucu Özeti (İndirme başlamadan):**
```
┌─────────────────────────────────────┐
│  Filtre Sonucu                      │
│                                     │
│  Toplam keşfedilen:  128 dosya      │
│  Filtre sonrası:      94 dosya      │
│  Atlanan:             34 dosya      │
│  Tahmini boyut:        1.2 GB       │
│                                     │
│   [ Detay Gör ]  [ İndirmeyi Başlat ]│
└─────────────────────────────────────┘
```

- Tüm filtreler **AND** ile çalışır (hepsi sağlanmalı)
- "Sıfırla" butonu tüm filtreleri varsayılan hale getirir

---

## Dosya Güvenliği — Boş / Bozuk Dosya Koruması

Her indirilen dosya şu 3 kontrolden geçer. **Herhangi biri başarısız olursa
dosya silinir, item `failed` olarak işaretlenir ve retry listesine eklenir.**

### Kontrol 1 — Boyut > 0
```python
if file_path.stat().st_size == 0:
    file_path.unlink()
    raise DownloadError("empty_file")
```

### Kontrol 2 — Sahte HTML Sayfası Değil
Blackboard bazen "Access Denied" veya "Session Expired" HTML sayfasını
200 OK ile döner. Dosya uzantısı PDF ama içerik HTML olur.
```python
content_start = file_path.read_bytes()[:100].lower()
if expected_type != "html":
    if content_start.startswith(b"<html") or content_start.startswith(b"<!doc"):
        file_path.unlink()
        raise DownloadError("received_html_instead_of_file")
```

### Kontrol 3 — Minimum Boyut Eşiği
Bazı "dosyalar" aslında redirect veya placeholder:
```python
MIN_SIZES = {
    "pdf": 1024,       # 1 KB
    "pptx": 5120,      # 5 KB
    "docx": 1024,      # 1 KB
    "video": 102400,   # 100 KB
}
if file_path.stat().st_size < MIN_SIZES.get(item.type, 512):
    file_path.unlink()
    raise DownloadError("file_too_small")
```

### İndirme Sırasında Stream Kontrolü
```
httpx ile stream indirirken:
  - Her chunk gelince boyut sayacı artırılır
  - Hiç chunk gelmezse (0 byte stream) → hata
  - Bağlantı ortada koparsa → geçici dosya silinir, retry
  - Geçici dosya adı: dosya.pdf.tmp → tamamlanınca dosya.pdf'e rename
```
`.tmp` dosyası hiçbir zaman son dosya olarak bırakılmaz.

---

## Kısıtlar ve Notlar

- Blackboard Ultra, React tabanlı SPA — tüm elementler için `waitForSelector` zorunlu
- Sunucu yükünü azaltmak için indirmeler arasına rastgele bekleme eklenir (0.5–1.5 sn)
- Session cookie'leri tarayıcı kapatılınca geçersiz olur, yeni login gerekir
- Cookie kaydedilmez, her açılışta taze login
- GUI kompakt modu tarayıcıyla yan yana çalışmayı kolaylaştırır
