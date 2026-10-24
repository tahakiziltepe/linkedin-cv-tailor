# Güvenlik Politikası

## Desteklenen sürümler

| Sürüm | Destek |
|---|---|
| 1.0.x | ✅ |

Proje tek kişilik bir otomasyon aracıdır; güvenlik düzeltmeleri en iyi çaba
ile, genelde en güncel sürüme yapılır.

## Açık bildirimi

**Lütfen güvenlik açıkları için herkese açık issue açmayın.**

- GitHub'da **Security → Report a vulnerability** yolunu kullanın:
  <https://github.com/tahakiziltepe/linkedin-cv-tailor/security/advisories/new>
- Bildirimde bulunması faydalı olanlar:
  - Etki (ne yapılabiliyor?)
  - Yeniden üretme adımları
  - Etkilenen sürüm / commit
  - Varsa önerilen düzeltme
- **Asla** gerçek `GEMINI_API_KEY`, `TELEGRAM_TOKEN`, `.env` içeriği veya
  kişisel CV verisi göndermeyin; redakte edilmiş örnek kullanın.

Geri dönüş hedefi: 7 gün içinde ilk yanıt. Düzeltme yayınlandığında ilgili
advisory üzerinden bilgi verilir.

## Kapsam

- `src/`, `webapp/`, `main.py`, `tools/`, `tests/` altındaki kod
- Özellikle: web paneli kimlik doğrulaması, oturum yönetimi, indirme
  route'unda yol geçişi (path traversal), prompt paneli, JSON dosya yazımı

Kapsam dışı:

- LinkedIn scraping'in ToS uygunluğu (bkz. README disclaimer)
- Kullanıcının kendi `.env`, CV ve `data/` dosyaları
- Üçüncü taraf servisler (Gemini, Telegram, JobSpy); bunları ilgili
  sağlayıcıya bildirin

## Güvenli kullanım notları

- `.env` dosyası gitignore'ludur; anahtarları asla commit'lemeyin.
- `SECRET_KEY` üretin:
  `python -c "import secrets; print(secrets.token_hex(32))"`.
- Web paneli varsayılan olarak `0.0.0.0:5000` üzerinde dinler. İnternete açık
  bir makinede çalıştırmayın; güvenlik duvarı veya ters proxy ile sınırlayın.
- `data/database/users.json` şifreleri hash'li tutun:
  `make hash-users`.
