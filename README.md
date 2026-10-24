# LinkedIn CV Builder & Tailor — Operasyon Rehberi

![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![uv](https://img.shields.io/badge/uv-managed-purple.svg)

**Yasal uyarı (Disclaimer):** Bu araç LinkedIn üzerine otomatik arama yapar
(JobSpy); scraping bazı şartlarda LinkedIn ToS ile ters düşebilir. Aracı
**kişisel kullanım** amacıyla yazdım; kullanımın tüm sorumluluğu sende.
Ayrıca CV uyarlaması sırasında CV metni Gemini API'ye gönderilir — hassas
verilerin paylaşımı konusunda kendi kararını ver.

> Bu doküman, projeye **herhangi bir zamanda** (1 gün sonra da 1 yıl sonra da)
> geri döndüğünde sıfırdan çalıştırmak için gereken her şeyi içerir.
> Hızlıca çalıştırmak için "5 Dakikada Restore" bölümünden başla, detaylar sonra gelir.

---

## 1) Bu proje ne yapıyor?

**Tek cümleyle:** LinkedIn'i tarar, veri alanındaki (Data Engineer / BI / Analytics)
uygun ilanları Gemini ile filtreler, CV'ni ilana göre kişiselleştirip PDF üretir
ve bunu Telegram'dan bildirir.

```
run_daily.sh (cron)  veya  main.py (manuel)
        │
        ▼
LinkedIn araması (JobSpy) ──► ilan listesi + açıklamaları
        │
        ▼
Filtreler:
  1. Geçmişte işlendiyse atla         (data/database/job_history.json)
  2. Açıklama yoksa atla
  3. Engelli şirket ise atla          (data/blocked_companies.json)
  4. AI uygun değilse atla            (Gemini → YES/NO)
        │
        ▼
Uygun ilan bulundu ──► Telegram bildirimi
        │
        ▼
Gemini, base CV'yi ilana göre uyarlar (Typst kaynak kodu)
        │
        ▼
Typst derleyicisi ──► data/output/<şirket>_<pozisyon>_<zaman>.pdf
        │
        ▼
İlan geçmişe kaydedilir │ bir sonraki ilana 20 sn bekleme (rate limit)
```

İki bileşen daha var:

- **Web paneli** (`webapp/web_app.py`, Flask, port 5000): üretilen CV'leri
  indirme; ilanların durumu (`Pending` → `Applied` → ...) ve notlarını
  düzenleme; bir ilan `Blocked Company` yapılırsa ilgili şirket otomatik
  olarak engelli listeye eklenir.
- **`run_daily.sh`**: `config.toml`'daki sorgu × lokasyon kombinasyonlarını
  döngüyle çalıştıran cron betiği; `auto_push` açıksa (varsayılan kapalı)
  sonunda `data/` değişikliklerini otomatik commit + push eder.

---

## 2) 5 Dakikada Restore (yeni makine / 1 yıl sonra)

Adımları sırayla uygula:

### Adım A — Ön koşullar

```bash
python3 --version                  # >= 3.12
uv --version || pip install uv     # bağımlılık yöneticisi
```

Kullanılan Python sürümü `.python-version` dosyasında sabitlendi (3.12).

### Adım B — Depo ve bağımlılıklar

```bash
git clone https://github.com/tahakiziltepe/linkedin-cv-tailor.git
cd linkedin-cv-tailor
uv sync        # .venv'yi uv.lock'a göre birebir kurar
```

### Adım C — `.env` dosyası

Repo kökünde `.env` oluştur (bu dosya git'e girmez):

```dotenv
GEMINI_API_KEY=...      # ZORUNLU → https://aistudio.google.com/apikey
TELEGRAM_TOKEN=...      # opsiyonel → @BotFather'dan bot token
TELEGRAM_CHAT_ID=...    # opsiyonel → bildirimin gideceği chat
GITHUB_TOKEN=...        # opsiyonel → run_daily.sh otomatik push'u için
```

- Telegram anahtarları yoksa: bildirim atlanır, CV yine üretilir.
- `GITHUB_TOKEN` yoksa: `run_daily.sh` push'u atlar, CV yine üretilir.
- **Yalnızca `GEMINI_API_KEY` yoksa**: AI filtreleme ve uyarlamada devre dışı
  kalır; her ilan için **değiştirilmemiş base CV** PDF olarak yazılır. Yani
  bu anahtar olmadan proje "çalışır" ama amacına hizmet etmez — mutlaka doldur.
- Yukarıdakiler "anahtar hiç yok" senaryosudur. **Anahtar yazılmış ama
  geçersizse** (süre dolmuş, iptal edilmiş) belirtiler farklıdır ve bazıları
  sessizdir → tanı-nasıl-düzelir tablosu için bkz. **5.5. Kimlik bilgileri
  arıza tablosu**. (Gerçek olay: 2026-10-24'te bu repo'da `.env`'deki
  `GITHUB_TOKEN` geçersizdi ve push sessizce başarısız oluyordu.)

### Adım D — Base CV kontrolü

`data/base_cv.typ` depoda mevcutsa hazır durumda. Kendi CV'ni kullanacaksan
yapıyı koru: `== Profile` başlığı, `== Skills` bölümü ve `#work(...)` fonksiyon
çağrıları. Bu dosya hem uyarlamasının hem de prompt'ların temelidir.

### Adım E — Çalıştır!

```bash
uv run python main.py --query "data engineer" --location "Istanbul, Turkey" --limit 3 --hours 24
```

Beklenen çıktı: `data/output/` altında `.typ` + `.pdf` dosyaları ve (Telegram
doldurulduysa) bildirim. `data/database/job_history.json` yoksa ilk çalıştırmada
boş bir liste (`[]`) olarak oluşturulur — normal.

**Ortam sağlığını tek komutla doğrula:** `uv run python doctor.py`
(bağımlılıklar, anahtarlar, model, typst, tracker — hepsi tek tek kontrol edilir;
FAIL satırları sorunu da söyler).

### Adım F (opsiyonel) — Web paneli

```bash
uv run python webapp/web_app.py    # tarayıcıda http://localhost:5000
```

Giriş bilgileri `data/database/users.json` dosyasında (bkz. "Güvenlik Notu" —
parolalar düz metin!).

### Adım G (opsiyonel) — Günlük otomatik çalışma (cron)

```bash
crontab -e
# Her gün 09:00'da:
0 9 * * * cd /tam/yol/linkedin-cv-tailor && ./run_daily.sh >> run_daily.log 2>&1
```

---

## 3) Komutlar ve parametreler

```bash
uv run python main.py \
  --query "data engineer" \        # ZORUNLU — arama sorgusu
  --location "Istanbul, Turkey" \  # varsayılan "Istanbul, Turkey"
  --limit 10 \                     # işlenecek ilan sayısı
  --hours 24                       # son X saat içinde paylaşılmış ilanlar
```

`run_daily.sh` parametresiz çalışır; ayarlarını **`config.toml`**'dan okur:
**6 sorgu × 2 lokasyon** (ingilizce + türkçe). `limit`, `hours`, `queries`,
`locations` ve `auto_push` sabitlerini config'den düzenleyebilirsin.

- `auto_push = false` **varsayılandır** (public kullanımı için güvenli).
  Kendin için açmak istiyorsan: config'de `auto_push = true` ya da `.env`
  içine `AUTO_PUSH=1` yaz (.env önceliklidir).
- Push sırasında ölü `GITHUB_TOKEN` bulunursa betik düz `git push`'a düşer
  (credential store kullanır) — detay: bölüm **5.5**.

---

## 4) Dosya yapısı (hangi dosya ne yapıyor?)

```
main.py                  # CLI + uçtan uca pipeline (yukarıdaki akış)
run_daily.sh             # çok sorgulu günlük tur + otomatik git push
webapp/web_app.py        # Flask panel (port 5000): login, durum, indirme
webapp/templates/        # login.html, dashboard.html
webapp/static/           # css + js

src/
  job_search.py          # JobSpy ile LinkedIn araması (açıklamalarla)
  cv_tailor.py           # Gemini: 1) ilan uygunluğu (YES/NO)
                         #         2) CV'yi ilana göre uyarlama
                         #         3) bozuk Typst kodunu otomatik onarma (3 deneme)
  pdf_generator.py       # .typ dosyası yazar, typst.compile → PDF
  tracker.py             # job_history.json; ekle/sil/tekrar-kontrol
  notifier.py            # Telegram bildirim (mesaj gönderilemezse sessizce atlanır)
  status_logger.py       # durum değişiklikleri (data/database/status_logs.json)

data/
  base_cv.typ            # ÖNEMLİ — Gemini prompting'inin kaynağı
  blocked_companies.json # engelli şirketler
  output/                # üretilen .typ + .pdf dosyaları (git'e girmez)
  database/
    job_history.json     # işlenmiş ilan geçmişi
    users.json           # web panel kullanıcıları (DÜZ METİN şifre!)
    status_logs.json     # durum değişiklik geçmişi
```

### `job_history.json` kayıt şeması

```json
{
  "company": "Hedef Filo",
  "title": "Business Analytics Specialist",
  "url": "https://www.linkedin.com/jobs/view/...",
  "pdf_path": "Hedef_Filo_Business_Analytics_Specialist_20261024_1541.pdf",
  "timestamp": "2026-10-24 15:41:02",
  "query": "Business Intelligence Analyst",
  "status": "Pending",
  "notes": ""
}
```

- `url` tekrar kontrolünde anahtar gibi çalışır (aynı ilan 2 kez işlenmez).
- `pdf_path` CV üretilmezse `null` olur.
- `status` varsayılan `Pending`; web panelinden değiştirilebilir. Panelde bir
  ilan `Blocked Company` yapılırsa ilgili şirket `blocked_companies.json`'a
  eklenir ve bir daha işlenmez.

---

## 5) 1 yıl sonra muhtemelen bozulacak şeyler (ve düzeltme yerleri)

Proje 3 harici servise bağlı: **Google Gemini, LinkedIn (JobSpy), Typst**.
Yıl içinde en muhtemel arıza noktaları:

### 5.1) Gemini model adı kapanır (en muhtemel)

`src/cv_tailor.py` 18–19. satırlar:

```python
GEMINI_MODEL_PRO   = "gemini-3.1-flash-lite-preview"
GEMINI_MODEL_FLASH = "gemini-3.1-flash-lite-preview"
```

Google bir model geri çektiğinde Gemini API şu hatayı döner:

```
404 NOT_FOUND: This model models/gemini-...-flash is no longer available.
```

**Düzeltme:** hata mesajında önerilen yeni model adını (örn.
"models/gemini-X.Y-flash") iki sabite (18–19. satır) yaz. Bugün `_fix_typst_code_api`
de dahil tüm çağrılar aynı sabitlerden besleniyor — başka yerde model adı yok.
Geçmiş not: bu proje daha önce `gemini-2.0-flash`'ın kapanmasıyla aynı sorunu
yaşamış ve `gemini-3.1-flash-lite-preview`'a geçmişti (2026-10-24).

### 5.2) LinkedIn/JobSpy arama başarısızlığı

LinkedIn scraping bazen 0 ilan veya boş `description` döner.

**Çözüm:** `--limit` artır, sorgu/lokasyon değiştir, birkaç saat sonra tekrar dene.
Bu durumda program kilitlenmez; ilanlar atlanır, geçmişe kaydedilmez.

### 5.3) Typst sürüm değişikliği

`pyproject.toml`'da `typst>=0.14.7`. `uv sync` bir yıl sonra çok daha yeni bir
Typst kurarsa base CV'nin derlenmesi başarısız olabilir.

**Çözüm:** [Typst'in GitHub release sayfasından](https://github.com/typst/typst/releases),
base CV'nin derlediği son sürümü pyproject'te sabitle: `typst=="0.14.7"` gibi.
Gerekirse `uv sync` tekrar.

### 5.4) Python sürümü

`.python-version` 3.12. Gelecekte sistemde başka sürüm varsa `uv` otomatik
halleder; sorun çıkarsa `uv python pin 3.12` ile tekrar sabitle.

### 5.5) Kimlik bilgileri (token) arıza tablosu

Token'lar zamanla **süresi biter veya iptal edilebilir** — genellikle
beklenmedik bir gün, sessizce. Bu tablo, hangi anahtar bozulursa ne görürsün
ve nasıl düzeltirsin:

| Anahtar | Nerede kullanılıyor? | Bozulunca ne görürsün (belirti) | Çözüm |
|---|---|---|---|
| `GEMINI_API_KEY` | `cv_tailor.py` (filtre + uyarlama) | Log satırları: `Error checking suitability after retries` ve `Error tailoring CV after retries`. Tüm ilanlar "uygun" gibi görünür; PDF olarak **değiştirilmemiş base CV** yazılır (fail-safe yüzünden sessiz çalışır!) | Yeni anahtar: aistudio.google.com/apikey → `.env` |
| `TELEGRAM_TOKEN` | `notifier.py` | Log: `Failed to send Telegram notification: 401 Unauthorized`. Pipeline sorunsuz devam eder, sadece bildirim gelmez (tespit etmek zor) | @BotFather → `/token` ile yeni token (eski token'ı geçersiz kılar) |
| `GITHUB_TOKEN` (`.env`) | `run_daily.sh` (sadece otomatik push) | Betik sonunda: `Failed to push using token.` — commit **yapılır** ama push **yapılmaz; fallback yok** | Yeni PAT → `.env` güncelle **veya** (bkz. not aşağıda) satırı tamamen sil |

Token kontrol komutları (çalışıp çalışmadığını hızlıca doğrulamak için):

```bash
# GEMINI anahtarı geçerli mi? (True dönerse ok)
uv run python -c "
from dotenv import load_dotenv; load_dotenv()
import src.cv_tailor as c
print(c._check_job_suitability_api('Data Engineer role, SQL, ETL'))
"

# Telegram anahtarı geçerli mi? (200 döner ve bot adı gösterilir)
curl -s https://api.telegram.org/bot$(grep '^TELEGRAM_TOKEN=' .env | cut -d= -f2-)/getMe | head -c 200

# GITHUB_TOKEN geçerli mi? (200 dönerse ok)
curl -s -o /dev/null -w '%{http_code}\n' \
  -H "Authorization: Bearer $(grep '^GITHUB_TOKEN=' .env | cut -d= -f2-)" \
  https://api.github.com/user
```

**Önemli not — `~/.git-credentials` mekaniği (elle `git push` neden çalışıyor?):**

Bu projede elle yaptığın `git push`'lar `.env`'deki tokenla alakasızdır; git kendi
credential store'una (`~/.git-credentials`) bakar. O dosyada şu biçimde
geçerli bir GitHub token saklanabilir:

```
https://<kullanıcı>:<token>@github.com
```

O yüzden `.env`'deki `GITHUB_TOKEN` ölü olsa bile elle yaptığın pushlar
çalışır; **yalnızca `run_daily.sh` etkilenir** (betik öncelik olarak `.env`
tokenını kullanır ve başarısız olursa düz `git push`'a düşmez — yalnızca
token'lı yolu dener).

**Genel kurallar:**
- **Kural 1:** Ölü bir token pipeline'ı asla kilitlemez; en kötü durumda
  ilgili işlev sessizce kaybolur (CV = base CV, bildirim yok, push yok).
- **Kural 2:** "Anahtar var ama işlemsiz" durumunun en tehlikeli yer Gemini —
  PDF'ler üretiliyor ama aslında AI devre dışı; fark etmek zordur.
- **Kural 3:** Yenilerken her iki yeri birden güncelle: `.env` (pipeline anahtarları)
  ve `~/.git-credentials` (manuel push). İkisinin de yukarıdaki kontrollerle
  geçerlilikten geçmeden "tamam oldum" deme.
- **Kural 4:** Yeni GitHub PAT gerekirse: classic token için `repo` scope
  yeterli; fine-grained token için "Contents" + "Pull requests" izinleri
  **write** olmalı (elle push için sadece "Contents" yeterli, PR açmak için
  "Pull requests" de gerekir).

---

## 6) Güvenlik notu (bugün bilinen, 1 yıl sonra da geçerli)

- `data/database/users.json`: parolalar **düz metin**. Tek kullanıcı/lokal
  kullanım için pahalı olmayan bir risk, ama paneli internete açma.
- `webapp/web_app.py` 21. satır: `SECRET_KEY` env'den alınamazsa hard-coded
  fallback'e düşer (`super_secret_key_12345`). Paneli yalnızca localhost'ta çalıştır.
- Uzun vadede düzeltmeler: `werkzeug.security.generate_password_hash` /
  `check_password_hash` kullanımı + zorunlu `SECRET_KEY`.

---

## 7) Risk tablosu

| Risk | Etki | Ne yapmak gerek |
|---|---|---|
| LinkedIn bot koruması | 0 ilan veya boş şablonlar | Bekle, sorgu/limit değiştir |
| Preview Gemini model kapanması | 404, CV üretilmez | 5.1 bölümünü uygula |
| Telegram bot geçersizleşmesi | Bildirim yok (sessiz çalışır) | Yeni bot token |
| Süresi geçmiş `GITHUB_TOKEN` (`.env`) | `run_daily.sh` push'u başarısız, fallback yok | 5.5 bölümünü uygula |
| `run_daily.sh` otomatik push | data/ dosyaları uzak repoya gider | Repo private kalmalı |
| Rate limit / uzun çalışma | 100 ilan ≈ 1 saat | `--limit` düşür |

---

## 8) Hızlı referans (kopyala, çalıştır)

```bash
# --- Sıfırdan kurulum ---
git clone https://github.com/tahakiziltepe/linkedin-cv-tailor.git
cd linkedin-cv-tailor
uv sync
cat > .env <<EOF
GEMINI_API_KEY=anahtarın
EOF

# --- Sıfırdan kurulum + ortam testi (Makefile ile) ---
make setup

# --- Manuel tek çalıştırma ---
uv run python main.py -q "data engineer" -l "Istanbul, Turkey" -n 3 --hours 24
# ya da: make run ARGS='-q "data engineer" -n 3 --hours 24'

# --- Üretilen CV'leri görmek ---
ls -lt data/output | head

# --- Web panel ---
uv run python webapp/web_app.py    # ya da: make web

# --- Günlük tur ---
./run_daily.sh                     # ya da: make daily

# --- Sözdizimi kontrolü ---
uv run python -m py_compile main.py src/*.py webapp/web_app.py
```

Demo yerden (önerilen akış):

```bash
cp templates/base_cv.example.typ data/base_cv.typ   # örnek CV, sonra düzenle
cp data/database/users.example.json data/database/users.json
uv run python doctor.py
uv run python main.py -q "data engineer" -l "Istanbul, Turkey" -n 2 --hours 48
```

---

## 9) Uyarlama Rehberi — kendi CV'nle, kendi sorguların

Bu araç "herkes kendi verisiyle çalıştırsın" diye yazıldı. Aşağıdaki
başlıkları senin kendi bilgilerinle doldurunca proje tamamen senin olur.

### 9.1) Kendi CV'ni koymak

1. `templates/base_cv.example.typ` dosyasını aç — yapısı örneklenir.
2. Kopyala: `cp templates/base_cv.example.typ data/base_cv.typ`
3. Düzenlerken şu yapı korunmalı:
   - `== Profile` başlığı + altındaki `/* ... */` yorum bloğu
     (AI bu bloktan profil özeti cümlelerini seçer)
   - Her iş için `#work(...)` çağrısı; altında `=== Job Description` ve
     `=== Notable Achievements` başlıklı `// V_SHORT: / / V_LONG:` maddeleri
     (AI ilana en uygun maddeleri buradan seçer)
   - `== Skills` altındaki `/* ... */` yetenek veri tabanı
   - Üstteki `#let name = ...`, `email`, `github`, `linkedin`, `phone`
     tanımları ve `#link("mailto:...")` satırları kendi bilgilerinle.
4. Doğrulama: çıktı PDF bozuksa önce typst sürümüne bak (bölüm 5.3).

### 9.2) Sorgularını ve konumunu ayarlamak (`config.toml`)

```toml
limit = 50             # bir turda sorgu başına ilan sayısı
hours = 24             # son X saat içinde paylaşılan ilanlar
auto_push = false      # true: gunluk sonuçları git'e otomatik commit+pushla
queries   = [ "data engineer", "veri analisti" ]       # senin alanın
locations = [ "Turkey", "Istanbul", "Remote" ]         # senin coğrafyan
```

`make daily` bu config ile tüm kombinasyonları çalıştırır. (Yoksa
`./run_daily.sh` aynı işi görür.)

### 9.3) Telegram bildirimlerinin kurulması

1. Telegram'da `@BotFather` → `/newbot` → sana bot token verir.
2. Token'ı ve chat ID'yi `.env`'e yaz.
3. Chat ID'yi bulmak için botuna bir mesaj yaz, sonra
   `https://api.telegram.org/bot<token>/getUpdates` adresindeki JSON'a bak:
   `chat.id` alanı.
4. Doğrulama: `uv run python doctor.py` → `[PASS] telegram bot: @...`.

### 9.4) Web panelinin ayarlanması

- `.env`'de `SECRET_KEY` zorunludur (yoksa panel başlamaz); paneli yalnızca
  localhost'ta çalışır durumda tut.
- Kullanıcılar `data/database/users.json` dosyasında; şifreler hash'li
  tutulur (örnek: `data/database/users.example.json`).
- Yeni kullanıcı: dosyaya `{"username": "...", "password": "<düz metin>"}`
  ekle, sonra bir kez `uv run python tools/hash_users.py` çalıştır
  (idempotent).

### 9.5) Cron ile otomatikleştirme

Bölüm 2'nin Adım G'sindeki cron örneği `run_daily.sh`'i `config.toml`
ayarlarını devralarak çalıştırır; çıktı `run_daily.log` dosyasına akar —
günlük turları incelemenin en hızlı yolu bu logtur.

### 9.6) Geliştirme ve yayın akışı

Bu proje iki ayrı yerde yaşar; ikisini karıştırmayın:

| Ne | Nerede | Nasıl |
|---|---|---|
| Geliştirme + günlük kayıtlar | private repo (`antigravity-cv-builder`), `main` | commit → `git push origin main` |
| Yayınlanan sürüm | public repo (`linkedin-cv-tailor`) | sadece `tools/publish.sh` |

**Kurallar:**

1. Tüm geliştirme private `main` üzerinde yapılır. Riskli bir iş için kısa
   ömürlü bir feature branch açılabilir; iş bitince hemen `main`'e merge edilip
   branch silinir.
2. Her commit'ten sonra private'a push edilir. Günlük `data/` değişiklikleri
   `AUTO_PUSH=1` ile zaten otomatik gider.
3. Public repoya **asla doğrudan commit atılmaz**. Güncelleme yalnızca:
   ```bash
   PUBLIC_REPO_URL=https://github.com/<kullanici>/linkedin-cv-tailor.git \
     bash tools/publish.sh
   ```
   Bu komut allow-list dosyalarını anlık kopyalar, kişisel veri taraması yapar
   ve temizse tek bir "Sync from private working repo" commit'i pushlar.
   Public'teki git geçmişi private'tan **bağımsızdır**.
4. Yeni bir dosya public'e gidecekse `tools/publish.sh` içindeki `FILELIST`'e
   de eklenmelidir. Aksi halde dosya public repoda görünmez.
5. `publish.sh` private branch'i push etmez; yayın ile yedekleme ayrı işlerdir.

---

*Son güncelleme ve doğrulama: 2026-10-24 — `gemini-3.1-flash-lite-preview` ile
uçtan uca çalıştırımda 1 ilan işlendi ve PDF üretildi. MIT lisanslı (LICENSE).*
