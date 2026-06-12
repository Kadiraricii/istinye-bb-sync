# Blackboard Downloader

Istinye Üniversitesi Blackboard Ultra sistemindeki ders materyallerini otomatik olarak indiren masaüstü uygulaması.

---

## Nedir?

Blackboard'daki her derse tek tek girip dosya indirmek yerine, bu araç tüm derslerini tarar, içerikleri listeler ve seçtiğin materyalleri bilgisayarına indirir. Hoca hangi klasör yapısını kurmuşsa aynen yansıtılır. Yarıda kesilirse kaldığı yerden devam eder.

---

## Özellikler

**İndirme**
- Tüm dersler veya seçilen dersler
- PDF, sunum, doküman, tablo, resim, arşiv
- SharePoint Stream videoları (yt-dlp ile) veya link olarak kaydetme
- Hoca klasör yapısı birebir korunur
- Kaldığı yerden devam (progress.json)
- Boş / bozuk dosya koruması (3 kademeli doğrulama)
- Türkçe karakter → ASCII dönüşümü, aynı isimde dosyalara `_2` eki

**Keşif**
- REST API üzerinden hızlı ders ve içerik taraması
- Her ders için dosya sayısı ve tahmini boyut
- Yeni eklenen içerikleri tespit etme (sync)

**Filtreleme**
- Dosya türüne göre (PDF, video, resim vs.)
- Boyut aralığına göre (min–max MB)
- Tarihe göre (belirli tarihten sonra eklenenler)
- Dosya adında anahtar kelimeye gö
- İndirme öncesi özet: "94 dosya · 1.2 GB"

**Arayüz**
- Karanlık tema, zinc renk paleti
- Ders seçim ekranı: kart grid, arama, anlık boyut özeti
- İndirme sırasında kurs bazlı ilerleme takibi
- Kompakt mod: 48px ince şerit, tarayıcıyla yan yana çalışma
- Her zaman üstte kalma seçeneği
- Tarayıcı kapatılırsa uyarı ve otomatik yeniden açma

**Güvenlik**
- Şifre hiçbir zaman diske yazılmaz
- Oturum cookie'leri kaydedilmez
- Her başlatmada taze login gerekir

---

## Nasıl Çalışır?

```
1. Uygulama başlar, öğrenci numarası ve şifre istenir

2. Playwright ile Chromium tarayıcı açılır (görünür mod)
   → Microsoft Azure AD SSO üzerinden login yapılır
   → Kullanıcı tüm süreci tarayıcıda görebilir
   → MFA varsa kullanıcı kendisi halleder

3. Session cookie (BbRouter) alınır
   → Bundan sonra tarayıcı işlemi biter
   → Tüm API çağrıları requests ile yapılır (hızlı)

4. Blackboard REST API üzerinden dersler ve içerikler keşfedilir
   → /learn/api/public/v1/users/me/courses
   → /learn/api/public/v1/courses/{id}/contents
   → Bulunamayan içerikler için Playwright fallback devreye girer

5. Kullanıcı dersleri seçer, filtreler ayarlar

6. httpx ile async stream indirme başlar
   → Video varsa yt-dlp devreye girer
   → Her dosya .tmp olarak indirilir, doğrulanır, sonra rename edilir
   → İlerleme progress.json'a sürekli yazılır
```

---

## Gereksinimler

- macOS 12+ / Windows 10+ / Ubuntu 20.04+
- Python 3.11 veya üzeri
- İnternet bağlantısı
- Istinye Üniversitesi öğrenci hesabı

---

## Kurulum

```bash
# Repoyu indir
git clone https://github.com/kullaniciadi/blackboard-downloader
cd blackboard-downloader

# Kur (tek komut)
./setup.sh
```

`setup.sh` şunları yapar:
- Python 3.11+ kontrolü
- Virtual environment oluşturma
- Tüm bağımlılıkları yükleme
- Playwright Chromium tarayıcısını indirme
- Klasör yapısını hazırlama

---

## Kullanım

```bash
# Uygulamayı başlat
./run.sh
```

Adımlar:
1. **Login ekranı** — Öğrenci numaranı gir, şifreni gir
2. **Tarayıcı açılır** — Microsoft login sayfasında giriş yapılır (görünür)
3. **Ders seçimi** — Keşfedilen dersler listelenir, istediğini seç
4. **Filtreler** — Hangi dosya türlerini indireceğini ayarla
5. **İndirme** — Başlat, izle, kapat

İndirilen dosyalar varsayılan olarak `~/Downloads/Blackboard/` klasörüne kaydedilir. Uygulama içinden değiştirilebilir.

---

## Klasör Yapısı

```
~/Downloads/Blackboard/
├── BGT107_Bilgisayara_Giris/
│   ├── Hafta_1/
│   │   ├── Giris_Sunumu.pdf
│   │   └── Ornekler.zip
│   ├── Hafta_2/
│   │   └── Degiskenler.pptx
│   └── video_links.txt        ← video URL'leri
├── MAT101_Matematik_I/
│   ├── Turev.pdf
│   └── Integral.pdf
└── ...
```

---

## Video İndirme

Videolar iki şekilde işlenebilir:

**Link olarak kaydet (varsayılan)**
Video URL'leri `video_links.txt` dosyasına yazılır. Manuel indirmek için:
```bash
# yt-dlp kuruluysa:
yt-dlp --cookies-from-browser chrome -a video_links.txt
```

**Otomatik indir**
Filtreler ekranında "Video → İndir" seçilirse yt-dlp session cookie'leriyle
SharePoint Stream videolarını otomatik indirir.

---

## Proje Yapısı

```
blackboard/
├── main.py               ← Uygulama giriş noktası
├── config.py             ← Sabitler ve ayarlar
├── models.py             ← Veri yapıları (Course, Item, Status)
├── state.py              ← progress.json ve manifest.json yönetimi
├── auth.py               ← Playwright login ve cookie yönetimi
├── crawler.py            ← REST API ile ders ve içerik keşfi
├── downloader.py         ← Async dosya indirme ve doğrulama
├── gui/
│   ├── app.py            ← Ana pencere, ekran geçişleri
│   ├── screen_login.py   ← Login ekranı
│   ├── screen_courses.py ← Ders seçim ekranı
│   ├── screen_filter.py  ← Filtre ekranı
│   └── screen_progress.py← İndirme ekranı
├── data/
│   ├── downloads/        ← İndirilen dosyalar
│   ├── manifest.json     ← Keşfedilen içerikler (otomatik)
│   └── progress.json     ← İndirme durumu (otomatik)
├── setup.sh              ← Kurulum scripti
├── run.sh                ← Başlatma scripti
└── requirements.txt      ← Python bağımlılıkları
```

---

## Bağımlılıklar

| Paket | Sürüm | Amaç |
|-------|-------|------|
| playwright | 1.49.0 | Tarayıcı otomasyonu (login) |
| customtkinter | 5.2.2 | Masaüstü GUI |
| httpx | 0.27.2 | Async HTTP / dosya indirme |
| yt-dlp | 2024.12.13 | Video indirme |
| python-slugify | 8.0.4 | Türkçe → ASCII dosya adı |
| rich | 13.9.4 | Terminal çıktı formatı |
| aiofiles | 24.1.0 | Async dosya yazma |

---

## Notlar

- Bu araç yalnızca kendi ders materyallerinizi indirmek için tasarlanmıştır
- Blackboard session süresi dolunca (genellikle 2–8 saat) yeniden login gerekir
- Sunucuya aşırı yük bindirmemek için indirmeler arasında otomatik bekleme uygulanır
- SCORM paketleri ve bazı gömülü içerikler indirilemeyebilir, URL olarak kaydedilir

---

## Lisans

Kişisel kullanım amaçlı. Akademik dürüstlük kurallarına uygun kullanın.
