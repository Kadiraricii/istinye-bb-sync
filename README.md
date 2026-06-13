# Blackboard Downloader

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey?style=flat)

Istinye Üniversitesi Blackboard Ultra sistemindeki ders materyallerini otomatik olarak indiren masaüstü uygulaması.

---

## Nedir?

Blackboard'daki her derse tek tek girip dosya indirmek yerine, bu araç tüm derslerini tarar, içerikleri listeler ve seçtiğin materyalleri bilgisayarına indirir. Hocanın oluşturduğu klasör yapısı birebir korunur. Yarıda kesilirse kaldığı yerden devam eder.

---

## Özellikler

**İndirme**
- Tüm dersler veya seçilen dersler
- PDF, sunum, belge, tablo, resim, arşiv, kod dosyaları (.py, .java, .c vb.)
- Harici linkler `links.txt` dosyasına kaydedilir
- SharePoint Stream videoları yt-dlp ile indirilebilir veya `video_links.txt`'e kaydedilebilir
- Hocanın klasör yapısı birebir korunur
- Kaldığı yerden devam (progress.json)
- Boş / bozuk dosya koruması (3 kademeli doğrulama)
- Türkçe karakter → ASCII dönüşümü, aynı isimde dosyalara `_2` eki

**Keşif**
- REST API üzerinden hızlı ders ve içerik taraması
- İç içe klasörler ve doküman ekleri dahil tam içerik ağacı
- Her ders için dosya sayısı ve tahmini boyut
- Yeni eklenen içerikleri tespit etme (sync)

**Filtreleme**
- Dosya türü chip'leriyle tek tıkla seçim:
  `PDF · Sunum · Belge · Tablo · Resim · Arşiv · Kod · Diğer · Video · Link`
- Video modu: Linkleri Kaydet / yt-dlp ile İndir / Atla
- Video kalitesi: best / 1080 / 720 / worst
- Dosya listesinde tek tek checkbox ile dahil/hariç bırakma
- Eş zamanlı indirme hızı: ×1 / ×2 / ×5
- İndirme öncesi özet: "115 dosya · 480 MB"

**Arayüz**
- Karanlık tema, Deep Navy + Emerald renk paleti
- Ders seçim ekranı: kart grid, arama, anlık boyut özeti
- İndirme sırasında kurs bazlı ilerleme takibi
- Kompakt mod: 48px ince şerit, tarayıcıyla yan yana çalışma
- Her zaman üstte kalma seçeneği

**Güvenlik**
- Şifre hiçbir zaman diske yazılmaz
- Oturum cookie'leri 1 saat sonra otomatik geçersiz sayılır

---

## Nasıl Çalışır?

```
1. Uygulama başlar, öğrenci numarası ve şifre istenir

2. Playwright ile Chromium tarayıcı açılır (görünür mod)
   → Microsoft Azure AD SSO üzerinden login yapılır
   → MFA varsa kullanıcı kendisi halleder

3. Session cookie (BbRouter) alınır
   → Bundan sonra tarayıcı işlemi biter
   → Tüm API çağrıları requests ile yapılır (hızlı)

4. Blackboard REST API üzerinden dersler ve içerikler keşfedilir
   → /learn/api/public/v1/users/me/courses
   → /learn/api/public/v1/courses/{id}/contents
   → Alt klasörler ve doküman ekleri recursive olarak taranır

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
git clone https://github.com/Kadiraricii/istinye-bb-sync
cd istinye-bb-sync
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
./run.sh
```

1. **Login** — Öğrenci numaranı ve şifreni gir
2. **Tarayıcı** — Microsoft login sayfasında giriş yapılır, MFA varsa halledersin
3. **Ders seçimi** — Keşfedilen dersler listelenir, istediğini seç
4. **Filtreler** — Hangi dosya türlerini indireceğini ayarla, dosyaları listeden çıkarabilirsin
5. **İndirme** — Başlat, izle, kapat

İndirilen dosyalar varsayılan olarak `~/Downloads/Blackboard/` klasörüne kaydedilir.

---

## Klasör Yapısı

```
~/Downloads/Blackboard/
├── BST020_Veri_Madenciligi/
│   ├── Ders01/
│   │   ├── BST020-Ders01-Notlar.pdf
│   │   └── BST020-Ders01-Kod.py
│   ├── Ders02/
│   │   └── BST020-Ders02-Notlar.pdf
│   ├── links.txt           ← harici linkler
│   └── video_links.txt     ← video URL'leri
├── MAT101_Matematik_I/
│   └── ...
```

---

## Video İndirme

**Link olarak kaydet (varsayılan)**
Video URL'leri `video_links.txt` dosyasına yazılır:
```bash
yt-dlp --cookies-from-browser chrome -a video_links.txt
```

**Otomatik indir**
Filtreler ekranında "Video → yt-dlp ile İndir" seçilirse SharePoint Stream videoları session cookie'leriyle otomatik indirilir.

---

## Proje Yapısı

```
blackboard/
├── core/
│   ├── config.py         ← URL'ler ve sabitler
│   ├── models.py         ← Course, Item, DownloadFilter veri modelleri
│   ├── state.py          ← manifest.json / progress.json yönetimi
│   ├── auth.py           ← Playwright login ve cookie yönetimi
│   ├── crawler.py        ← REST API ile ders ve içerik keşfi
│   └── downloader.py     ← Async dosya indirme ve doğrulama
├── gui/
│   ├── app.py            ← Ana pencere, ekran geçişleri
│   ├── theme.py          ← Renk ve tipografi sabitleri
│   ├── screen_login.py   ← Login ekranı
│   ├── screen_courses.py ← Ders seçim ekranı
│   ├── screen_filter.py  ← Filtre ve dosya seçim ekranı
│   └── screen_progress.py← İndirme ekranı
├── data/                 ← Runtime verisi (Git'e girmez)
├── main.py
├── setup.sh
├── run.sh
└── requirements.txt
```

---

## Bağımlılıklar

| Paket | Amaç |
|-------|-------|
| playwright | Tarayıcı otomasyonu (login) |
| customtkinter | Masaüstü GUI |
| httpx | Async HTTP / dosya indirme |
| yt-dlp | Video indirme |
| python-slugify | Türkçe → ASCII dosya adı |
| aiofiles | Async dosya yazma |

---

## Notlar

- Bu araç yalnızca kendi ders materyallerini indirmek için tasarlanmıştır
- Blackboard session süresi dolunca yeniden login gerekir
- Sunucuya aşırı yük bindirmemek için indirmeler arasında otomatik bekleme uygulanır
- SCORM paketleri indirilemez, URL olarak kaydedilir

---

## Lisans

Kişisel kullanım amaçlı. Akademik dürüstlük kurallarına uygun kullanın.
