# Roadmap

## Sprint 1 — Temel Yapı ✅
> `config.py` · `models.py` · `state.py`

- [x] `config.py` — URL'ler, email domain, path'ler, sabitler
- [x] `models.py` — `Course`, `Item`, `ItemType`, `DownloadStatus`, `CourseStatus` dataclass'ları
- [x] `state.py` — `manifest.json` okuma/yazma
- [x] `state.py` — `progress.json` okuma/yazma
- [x] `state.py` — `data/` klasörü otomatik oluşturma

---

## Sprint 2 — Login & Auth
> `auth.py`

- [ ] Playwright `chromium` headless=False başlatma
- [ ] Blackboard URL'e gitme, Microsoft SSO yönlendirmesini bekleme
- [ ] Email alanına `{numara}@stu.istinye.edu.tr` otomatik yazma
- [ ] Şifre alanını odaklama (kullanıcı kendisi yazar)
- [ ] Login başarısını URL pattern ile tespit etme (`/ultra/` içeriyorsa)
- [ ] `BbRouter` ve diğer session cookie'lerini alma
- [ ] Cookie'leri `requests.Session`'a aktarma
- [ ] Tarayıcı kapatılınca uyarı + yeniden açma mantığı
- [ ] Status callback sistemi (GUI'ye durum iletmek için)

---

## Sprint 3 — Crawler (Ders Keşfi)
> `crawler.py` — Aşama 1

- [ ] `GET /learn/api/public/v1/users/me/courses` ile kayıtlı dersleri listeleme
- [ ] Pagination desteği (`paging.nextPage` kontrolü)
- [ ] Her ders için: `id`, `name`, `courseId`, `url` kaydetme
- [ ] Sonuçları `manifest.json`'a yazma
- [ ] Hata durumunda retry (max 3)

---

## Sprint 4 — Crawler (İçerik Keşfi)
> `crawler.py` — Aşama 2

- [ ] `GET /learn/api/public/v1/courses/{id}/contents` ile içerik listeleme
- [ ] Klasörler için recursive `/children` çağrısı
- [ ] Her item için: `id`, `name`, `type`, `url`, `size`, `path_hint` kaydetme
- [ ] `contentHandler.id` → `ItemType` mapping (folder, file, link, video, scorm)
- [ ] Attachment download URL'i çekme (`/attachments/{id}/download`)
- [ ] SharePoint Stream URL tespiti (iframe src içinden)
- [ ] Playwright fallback: REST API'de bulunamayan içerikler için DOM tarama
- [ ] Kurs bazlı `status: crawled` güncelleme
- [ ] Hata olursa `status: crawl_failed`, sonraki kursa geç

---

## Sprint 5 — Downloader
> `downloader.py`

- [ ] `httpx` async stream ile dosya indirme
- [ ] `.tmp` uzantısıyla geçici indirme, tamamlanınca rename
- [ ] **Doğrulama 1:** Boyut > 0 kontrolü
- [ ] **Doğrulama 2:** Sahte HTML sayfası tespiti (içerik başlangıcı kontrolü)
- [ ] **Doğrulama 3:** Minimum boyut eşiği (tip bazlı)
- [ ] Bağlantı kopunca geçici dosyayı silme ve retry
- [ ] Asyncio Semaphore ile concurrent indirme (1/2/5 ayarlanabilir)
- [ ] İndirmeler arası rastgele bekleme (0.5–1.5 sn)
- [ ] `yt-dlp` ile SharePoint Stream video indirme
- [ ] Video URL → `video_links.txt` kaydetme (link modu)
- [ ] `links.txt` ve `scorm_links.txt` oluşturma
- [ ] `progress.json` güncelleme (her başarılı indirmede)
- [ ] Dosya adı: Türkçe → ASCII (`python-slugify`)
- [ ] Aynı isimde dosya varsa `_2`, `_3` eki
- [ ] Klasör yapısını `path_hint`'e göre oluşturma

---

## Sprint 6 — GUI: Login Ekranı
> `gui/screen_login.py`

- [ ] Ana pencere boyutu ve konum (ekran ortası)
- [ ] Logo / başlık tipografisi
- [ ] Öğrenci numarası input — yazarken `{no}@stu.istinye.edu.tr` preview
- [ ] Şifre input — göster/gizle butonu
- [ ] "Tarayıcıda Giriş Yap" primary butonu
- [ ] Status satırı: dot animasyonu + renk geçişi (gri→amber→yeşil→kırmızı)
- [ ] Buton tıklanınca spinner + "Bağlanıyor..." metni
- [ ] Hata mesajı gösterimi (yanlış şifre, bağlantı yok vs.)
- [ ] Giriş başarılıysa Ders Seçimi ekranına geçiş

---

## Sprint 7 — GUI: Ders Seçimi Ekranı
> `gui/screen_courses.py`

- [ ] Header: geri butonu + ders sayısı + "Tümünü Seç" / "Temizle"
- [ ] Arama kutusu (anlık filtreleme)
- [ ] Skeleton loading state (shimmer animasyonu)
- [ ] 2 sütun kart grid (scrollable)
- [ ] Kart içeriği: kod, isim, dosya/video/link sayısı, MB tahmini
- [ ] Seçili kart: `border: #818cf8`, checkbox dolu
- [ ] Seçilmemiş kart: `border: #27272a`, opacity azaltılmış
- [ ] Hover efekti (arka plan rengi geçişi)
- [ ] Kartlar yüklenince staggered fade-in animasyonu
- [ ] Alt bar: "X ders seçili · ~Y MB" canlı güncelleme
- [ ] İndirme klasörü seçici (filedialog)
- [ ] "Devam →" butonu (en az 1 ders seçiliyse aktif)

---

## Sprint 8 — GUI: Filtre Ekranı
> `gui/screen_filter.py`

- [ ] 3 sekme: Dosya Türleri / Boyut & Tarih / Video
- [ ] **Dosya Türleri sekmesi:** checkbox listesi (PDF, sunum, doküman vs.)
- [ ] **Boyut & Tarih sekmesi:** min/max MB input, tarih aralığı, keyword input
- [ ] **Bant genişliği seçimi:** 1 / 2 / 5 eş zamanlı indirme radio butonu
- [ ] **Video sekmesi:** İndir (yt-dlp) / Link kaydet seçimi + kalite dropdown
- [ ] Aktif sekme: alt border accent rengi
- [ ] Alt özet bar: "X dosya · Y GB indirilecek" (filtre değişince canlı güncelleme)
- [ ] "Sıfırla" butonu
- [ ] "Başlat" primary butonu

---

## Sprint 9 — GUI: İndirme Ekranı
> `gui/screen_progress.py`

- [ ] Header: "X/Y dosya" sayacı + Sabitle / Tarayıcı / Duraklat / İptal butonları
- [ ] Genel progress bar (smooth güncelleme, #818cf8 renk)
- [ ] Mevcut dosya adı + dosya bazlı progress bar
- [ ] Kurs listesi: ✓ tamamlandı / · devam ediyor / ○ bekliyor
- [ ] Scrollable log (monospace, renk kodlu satırlar)
- [ ] Log temizle butonu
- [ ] **Kompakt mod:** 48px yükseklik, progress + dosya adı + butonlar
- [ ] Kompakt ↔ tam boyut geçiş animasyonu
- [ ] "Sabitle" (always on top) toggle
- [ ] "Tarayıcıyı Göster" butonu
- [ ] Tamamlanınca özet popup: "X dosya indirildi · Y MB · Z hata"

---

## Sprint 10 — Entegrasyon
> GUI ↔ Backend bağlantısı

- [ ] Worker thread: asyncio event loop ayrı thread'de
- [ ] `queue.Queue` ile thread-safe mesajlaşma
- [ ] `root.after(0, callback)` ile GUI güncellemeleri
- [ ] Tarayıcı kapatılınca GUI uyarı popup'ı (Evet/Hayır)
- [ ] Duraklat / devam / iptal sinyalleri
- [ ] Tüm ekranlar arası veri akışı (login → courses → filter → progress)

---

## Sprint 11 — Son Rötuşlar
> Kalite ve kararlılık

- [ ] Sync modu: yeni içerik tespiti ve diff gösterimi
- [ ] Retry modu: sadece başarısız item'ları yeniden deneme
- [ ] Beklenmedik Blackboard DOM değişikliklerine karşı hata yakalama
- [ ] Disk dolu kontrolü (indirme öncesi yeterli alan var mı?)
- [ ] Büyük dosya uyarısı (>50MB dosya öncesi onay popup'ı)
- [ ] Tüm ekranlarda klavye navigasyonu (Tab, Enter, Escape)
- [ ] `setup.sh` son test (temiz ortamda)
- [ ] README güncelleme (gerçek ekran görüntüleri)

---

## İlerleme Özeti

| Sprint | Konu | Durum |
|--------|------|-------|
| 1 | Temel yapı | ✅ Tamamlandı |
| 2 | Auth & Login | ⬜ Bekliyor |
| 3 | Crawler — Dersler | ⬜ Bekliyor |
| 4 | Crawler — İçerikler | ⬜ Bekliyor |
| 5 | Downloader | ⬜ Bekliyor |
| 6 | GUI: Login | ⬜ Bekliyor |
| 7 | GUI: Ders Seçimi | ⬜ Bekliyor |
| 8 | GUI: Filtreler | ⬜ Bekliyor |
| 9 | GUI: İndirme | ⬜ Bekliyor |
| 10 | Entegrasyon | ⬜ Bekliyor |
| 11 | Son rötuşlar | ⬜ Bekliyor |
