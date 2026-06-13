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

### 1. Login

Login ekranı sıfırdan tasarlandı — hem ilk kullanımda hem sonraki açılışlarda sürtünmesiz çalışacak şekilde.

**İlk açılışta** iki adım var:

1. **Öğrenci numarası** — Alan sadece rakam kabul eder; harf veya özel karakter girmeye çalışınca ekran hafifçe titrer. Kaç karakter girildiği anlık gösterilir (örn. `7 / 10`). Altındaki büyük buton, yazılan karakter sayısına göre soldan sağa "su dolar gibi" dolar; 10 rakam tamamlanınca tam dolu hâle gelir ve otomatik ilerler.

2. **Şifre** — Şifre girmek zorunlu değil. Bilgi kutusu şunu söyler: girilirse giriş otomatik tamamlanır; girilmezse tarayıcı açılır ve kullanıcı kendisi doldurur. Şifre hiçbir zaman diske yazılmaz.

**Sonraki açılışlarda** öğrenci numarası `remember.json`'a kaydedildiği için doğrudan profil kartı görünür — adı, avatar rengi ve üniversite uzantısıyla. Bir tıkla şifre adımına geçilir. Farklı hesap kullanmak isteyenler için "Farklı hesap kullan" linki her zaman görünür.

**Oturum hâlâ geçerliyse** (son login 1 saatten az önce yapıldıysa) ekranın altında `⚡ Önceki oturumla devam et · 5dk önce` butonu belirir. Bu butona tıklamak tarayıcı açmadan, şifre girmeden doğrudan ders seçim ekranına taşır.

Giriş başladığında bağlantı ekranı açılır: dönen animasyon ve durum mesajı. Microsoft Azure AD SSO sayfası yüklenir. MFA gerekiyorsa (telefon onayı, Authenticator vs.) kullanıcı halleder — uygulama bekler. İsteyenler `Tarayıcıyı Göster →` butonuyla tarayıcıyı ön plana alabilir.

Şifre yanlış girildiyse veya giriş başarısız olursa tarayıcı kapanmaz; hata mesajı gösterilir ve kullanıcı tarayıcıdan düzeltebilir.

Login tamamlanınca `BbRouter` session cookie'si alınır ve şifrelenmiş olarak `data/session.json`'a kaydedilir. Tarayıcı kapanır; bundan sonra her şey arka planda `requests` ile çalışır.

### 2. İçerik Keşfi (Crawler)

Blackboard REST API üzerinden tüm kayıtlı dersler çekilir. Kullanıcının erişebildiği her ders için içerik ağacı recursive olarak taranır:

- `resource/x-bb-folder` → alt klasöre in, aynı işlemi tekrarla
- `resource/x-bb-document` → hem alt içerikleri (`/children`) hem de doğrudan ekleri (`/attachments`) kontrol et
- `resource/x-bb-file` → dosya eki olarak al
- `resource/x-bb-externallink` → URL'i analiz et; SharePoint/Stream linki ise video, `.pdf` gibi uzantılı ise ilgili tür, değilse harici link olarak işaretle
- `hasChildren: true` olan her içerik için recursion devreye girer

Availability kontrolü: yalnızca `available: "No"` olanlar atlanır. `"Term"` (dönem bazlı erişim) ve `"PartiallyVisible"` dahil edilir.

Her item için `path_hint` alanı doldurulur — indirme sırasında bu bilgi birebir klasör yapısına dönüşür.

### 3. Filtreler ve Dosya Seçimi

Kullanıcı hangi ders(ler)in içeriğini indireceğini seçtikten sonra filtre ekranı açılır:

- **Dosya türü chip'leri** — PDF, Sunum, Belge, Tablo, Resim, Arşiv, Kod, Diğer, Video, Link; tek tıkla aç/kapat
- **Video modu** — Linkleri Kaydet (varsayılan) / yt-dlp ile İndir / Atla
- **Dosya listesi** — tüm içerikler klasör yoluyla birlikte listelenir; her satırda checkbox ile tek tek dahil/hariç bırakılabilir
- **Eş zamanlı hız** — ×1 / ×2 / ×5 paralel indirme
- Alt kısımda anlık özet: "115 dosya · 480 MB"

### 4. İndirme

`httpx` ile async stream indirme başlar. Her dosya önce `.tmp` uzantısıyla yazılır, tamamlanınca boyut ve bütünlük doğrulanır, ardından gerçek adıyla kaydedilir. Hata durumunda 3 deneme yapılır.

Videolar için yt-dlp seçilmişse session cookie otomatik aktarılır. Link modunda URL'ler `video_links.txt`'e yazılır. Harici linkler `links.txt`'e kaydedilir.

Her adımda ilerleme `progress.json`'a yazılır. Uygulama kapanıp tekrar açılırsa zaten indirilen dosyalar atlanır, kaldığı yerden devam eder.

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
