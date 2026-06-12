# Roadmap

## Sprint 1 — Temel Yapı ✅
> `config.py` · `models.py` · `state.py`

- [x] `config.py` — URL'ler, email domain, path'ler, sabitler
- [x] `models.py` — `Course`, `Item`, `ItemType`, `DownloadStatus`, `CourseStatus` dataclass'ları
- [x] `state.py` — `manifest.json` okuma/yazma
- [x] `state.py` — `progress.json` okuma/yazma
- [x] `state.py` — `data/` klasörü otomatik oluşturma

---

## Sprint 2 — Login & Auth ✅
> `core/auth.py`

- [x] Playwright `chromium` headless=False başlatma
- [x] Blackboard URL'e gitme, Microsoft SSO yönlendirmesini bekleme
- [x] Email alanına `{numara}@stu.istinye.edu.tr` otomatik yazma
- [x] Şifre alanını odaklama (kullanıcı kendisi yazar)
- [x] Login başarısını URL pattern ile tespit etme (`/ultra/` içeriyorsa)
- [x] `BbRouter` ve diğer session cookie'lerini alma
- [x] Cookie'leri `requests.Session`'a aktarma
- [x] Tarayıcı kapatılınca uyarı + yeniden açma mantığı
- [x] Status callback sistemi (GUI'ye durum iletmek için)

---

## Sprint 3 — Crawler (Ders Keşfi) ✅
> `crawler.py` — Aşama 1

- [x] `GET /learn/api/public/v1/users/me/courses` ile kayıtlı dersleri listeleme
- [x] Pagination desteği (`paging.nextPage` kontrolü)
- [x] Her ders için: `id`, `name`, `courseId`, `url` kaydetme
- [x] Sonuçları `manifest.json`'a yazma
- [x] Hata durumunda retry (max 3)

---

## Sprint 4 — Crawler (İçerik Keşfi) ✅
> `crawler.py` — Aşama 2

- [x] `GET /learn/api/public/v1/courses/{id}/contents` ile içerik listeleme
- [x] Klasörler için recursive `/children` çağrısı
- [x] Her item için: `id`, `name`, `type`, `url`, `size`, `path_hint` kaydetme
- [x] `contentHandler.id` → `ItemType` mapping (folder, file, link, video, scorm)
- [x] Attachment download URL'i çekme (`/attachments/{id}/download`)
- [x] SharePoint Stream URL tespiti (domain kontrolü ile)
- [x] Kurs bazlı `status: crawled` güncelleme
- [x] Hata olursa `status: crawl_failed`, sonraki kursa geç

---

## Sprint 5 — Downloader ✅
> `downloader.py`

- [x] `httpx` async stream ile dosya indirme
- [x] `.tmp` uzantısıyla geçici indirme, tamamlanınca rename
- [x] **Doğrulama 1:** Boyut > 0 kontrolü
- [x] **Doğrulama 2:** Sahte HTML sayfası tespiti (içerik başlangıcı kontrolü)
- [x] **Doğrulama 3:** Minimum boyut eşiği (tip bazlı)
- [x] Bağlantı kopunca geçici dosyayı silme ve retry
- [x] Asyncio Semaphore ile concurrent indirme (1/2/5 ayarlanabilir)
- [x] İndirmeler arası rastgele bekleme (0.5–1.5 sn)
- [x] `yt-dlp` ile SharePoint Stream video indirme
- [x] Video URL → `video_links.txt` kaydetme (link modu)
- [x] `links.txt` ve `scorm_links.txt` oluşturma
- [x] `progress.json` güncelleme (her başarılı indirmede)
- [x] Dosya adı: Türkçe → ASCII (`python-slugify`)
- [x] Aynı isimde dosya varsa `_2`, `_3` eki
- [x] Klasör yapısını `path_hint`'e göre oluşturma

---

## Sprint 6 — GUI: Login Ekranı ✅
> `gui/theme.py` + `gui/screen_login.py`

- [x] Ana pencere boyutu ve konum
- [x] Logo / başlık tipografisi (Inter, Blackboard Sync başlığı)
- [x] Öğrenci numarası input — yazarken `{no}@stu.istinye.edu.tr` preview
- [x] "Tarayıcıda Giriş Yap" primary butonu
- [x] Status satırı: dot renk geçişi (gri→amber→yeşil→kırmızı)
- [x] Buton tıklanınca "Bağlanıyor..." devre dışı
- [x] Hata mesajı gösterimi
- [x] Giriş başarılıysa Ders Seçimi ekranına geçiş
- [x] Enter tuşuyla giriş başlatma

---

## Sprint 7 — GUI: Ders Seçimi Ekranı ✅
> `gui/screen_courses.py`

- [x] Header: geri butonu + ders sayısı + "Tümünü Seç" / "Temizle"
- [x] Arama kutusu (anlık filtreleme)
- [x] Skeleton loading state
- [x] 2 sütun kart grid (scrollable)
- [x] Kart içeriği: kod, isim, dosya/video/link sayısı, MB tahmini
- [x] Seçili kart: `border: #818cf8`, checkbox dolu
- [x] Seçilmemiş kart: `border: #3f3f46`
- [x] Alt bar: "X ders seçili · ~Y MB" canlı güncelleme
- [x] İndirme klasörü seçici (filedialog)
- [x] "Devam →" butonu (en az 1 ders seçiliyse aktif)

---

## Sprint 8 — GUI: Filtre Ekranı ✅
> `gui/screen_filter.py`

- [x] 3 sekme: Dosya Türleri / Boyut & Tarih / Video
- [x] **Dosya Türleri sekmesi:** checkbox listesi (PDF, sunum, doküman vs.)
- [x] **Boyut & Tarih sekmesi:** min/max MB input, keyword input
- [x] **Bant genişliği seçimi:** 1 / 2 / 5 eş zamanlı indirme radio butonu
- [x] **Video sekmesi:** İndir (yt-dlp) / Link kaydet / Atla + kalite seçimi
- [x] Alt özet bar: "X öğe indirilecek · ~Y MB" (filtre değişince canlı güncelleme)
- [x] "Sıfırla" butonu
- [x] "İndirmeyi Başlat" primary butonu

---

## Sprint 9 — GUI: İndirme Ekranı ✅
> `gui/screen_progress.py`

- [x] Header: "X/Y dosya" sayacı + Sabitle / Kompakt / Duraklat / İptal butonları
- [x] Genel progress bar (smooth güncelleme, #818cf8 renk)
- [x] Mevcut dosya adı + ETA
- [x] Kurs listesi: ✓ tamamlandı / · devam ediyor / ○ bekliyor
- [x] Scrollable log (monospace, renk kodlu)
- [x] Log temizle butonu
- [x] **Kompakt mod:** 48px yükseklik, pencere küçülür
- [x] "Sabitle" (always on top) toggle
- [x] Tamamlanınca özet popup: "X dosya indirildi · Z hata"

---

## Sprint 10 — Entegrasyon ✅
> `gui/app.py`

- [x] Worker thread: asyncio event loop ayrı thread'de
- [x] `queue.Queue` ile thread-safe mesajlaşma
- [x] `root.after(50, poll)` ile GUI güncellemeleri
- [x] Duraklat / devam / iptal sinyalleri downloader'a iletilir
- [x] Tüm ekranlar arası veri akışı (login → courses → filter → progress)
- [x] WM_DELETE_WINDOW handler ile güvenli kapanma

---

## Sprint 11 — Son Rötuşlar ✅
> Kalite ve kararlılık

- [x] Sync modu: `get_new_items()` — eski manifest ile diff
- [x] Retry modu: `get_failed_items()` — sadece başarısız item'lar
- [x] Tüm crawler hataları try/except ile yakalanır, sonraki kursa geçilir
- [x] Disk dolu kontrolü — `check_disk_space()` + downloader.run() başında uyarı
- [x] Büyük dosya uyarısı (>50MB dosya öncesi log mesajı)
- [x] Klavye navigasyonu: Enter (login), Escape (geri/iptal)

---

## İlerleme Özeti

| Sprint | Konu | Durum |
|--------|------|-------|
| 1 | Temel yapı | ✅ Tamamlandı |
| 2 | Auth & Login | ✅ Tamamlandı |
| 3 | Crawler — Dersler | ✅ Tamamlandı |
| 4 | Crawler — İçerikler | ✅ Tamamlandı |
| 5 | Downloader | ✅ Tamamlandı |
| 6 | GUI: Login | ✅ Tamamlandı |
| 7 | GUI: Ders Seçimi | ✅ Tamamlandı |
| 8 | GUI: Filtreler | ✅ Tamamlandı |
| 9 | GUI: İndirme | ✅ Tamamlandı |
| 10 | Entegrasyon | ✅ Tamamlandı |
| 11 | Son rötuşlar | ✅ Tamamlandı |
