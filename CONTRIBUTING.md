# Katkı Rehberi

Teşekkürler! Bu proje kişisel bir otomasyon aracı olarak doğdu ama katkılara
açık. Küçük, tek amaçlı PR'lar en hızlı incelenir.

> **English summary:** Contributions are welcome. You do **not** need a Gemini
> API key, Telegram token or network access to work on the code: run
> `uv sync && make test` and the full offline suite runs with mocked services.
> Flow: fork → branch → commit → PR. Merged changes are ported back to the
> maintainer's private repo and re-published, so your commit SHA may change.
> See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) and
> [SECURITY.md](SECURITY.md).

## İçindekiler

- [Hızlı başlangıç (API anahtarı gerekmez)](#hızlı-başlangıç-api-anahtarı-gerekmez)
- [Ne tür katkılar?](#ne-tür-katkılar)
- [Geliştirme akışı](#geliştirme-akışı)
- [Testler](#testler)
- [PR kontrol listesi](#pr-kontrol-listesi)
- [Yayın akışı (yalnızca bakımcı)](#yayın-akışı-yalnızca-bakımcı)

## Hızlı başlangıç (API anahtarı gerekmez)

```bash
# 1) Fork'layın, sonra kendi fork'unuzu klonlayın
git clone https://github.com/<kullanici>/linkedin-cv-tailor.git
cd linkedin-cv-tailor

# 2) Bağımlılıklar (uv gerekir: https://docs.astral.sh/uv/)
uv sync

# 3) Tüm offline test paketi — ağ/API çağrısı yapmaz
make test
```

`make test`; Gemini, Telegram ve JobSpy çağrılarını mock'lar ve gerçek
`data/` dizinine **yazmaz** (`tmp_path` kullanır). Yani `.env` dosyası
olmadan geliştirme yapabilirsiniz.

Ortam kontrolü (anahtar gerekmez, sadece varlık kontrolü):

```bash
GEMINI_API_KEY=dummy uv run python doctor.py --offline
```

Gerçek API ile uçtan uca denemek isterseniz:

```bash
cp .env.example .env      # GEMINI_API_KEY doldurun
make test-live            # gerçek Gemini çağrısı yapar, kota harcar
```

## Ne tür katkılar?

- **Hata düzeltmeleri** — özellikle README §5'teki bilinen kırılgan noktalar
  (Gemini model adı, JobSpy/LinkedIn değişiklikleri, Typst sürümü).
- **Testler** — yeni davranış veya eksik hata yolu için.
- **Dokümantasyon** — kurulum adımları, sorun giderme, örnekler.
- **İngilizce README çevirisi** — açık bir TODO; büyük katkı, issue açıp
  koordine edelim.
- **Prompt iyileştirmeleri** — `prompts/*.md` (metin değişikliği hijyen
  testini güncellemeyi gerektirir, aşağıya bakın).
- **Yeni bildirim kanalı** (Slack, e-posta vb.) veya yeni iş kaynağı.
- **Typst şablonu** iyileştirmeleri (`templates/base_cv.example.typ`).

Büyük bir değişiklik planlıyorsanız önce issue açın; yaklaşımı netleştirip
sonra PR yazmak herkesin zamanını korur.

## Geliştirme akışı

1. Fork'layın ve `main`'den kısa ömürlü bir branch açın:
   `fix/kisa-aciklama`, `feat/yeni-ozellik`, `docs/readme-en`, `test/...`.
2. Değişikliği **tek amaçlı** tutun; ilgisiz yeniden formatlama/refactor
   yapmayın.
3. Commit mesajı: tek satır özet + gerekirse gövde. Örnekler:
   ```
   fix: handle empty job description in main flow
   test: cover prompt reset when override is missing
   docs: add troubleshooting for expired Gemini model
   ```
   Dil (Türkçe/İngilizce) serbest; tutarlı olun.
4. Davranış değişikliği varsa `tests/` altına test ekleyin.
5. Kullanıcıya görünen değişiklikte README ve/veya `CHANGELOG.md` güncelleyin.
6. `make test` geçmeden PR açmayın.
7. PR açıklamasında **ne**, **neden** ve **nasıl test edildi** olsun; ilgili
   issue'yu `Fixes #123` ile bağlayın.

## Testler

| Komut | Ne yapar | Gereksinim |
|---|---|---|
| `make test` | Offline paket (yayın/PR için zorunlu) | Yok |
| `make test-clean` | Temiz makine simülasyonu | Yok (yavaş) |
| `make test-live` | Gerçek Gemini çağrısı | `.env` + kota |
| `make check` | `py_compile` + `doctor --offline` + `make test` | Dummy `GEMINI_API_KEY` |

Kurallar:

- Varsayılan testler **ağ/API çağrısı yapmaz**. Dış servisleri `monkeypatch`
  ile mock'layın (bkz. `tests/test_cv_tailor.py`, `tests/test_notifier.py`).
- Testler gerçek `data/` dizinine yazmaz; `tmp_path` kullanın.
- Gerçek API gereken testleri `@pytest.mark.live` ile işaretleyin; bunlar
  `make test` içinde çalışmaz.
- Yeni dosya eklerseniz `tests/test_hygiene.py` içindeki `ROOT_REQUIRED`
  listesini ve `tools/publish.sh` allow-list'ini güncelleyin.
- Prompt metnini değiştirirseniz `tests/fixtures/legacy_prompts.py` içindeki
  referansı da güncelleyin (regresyon testi bilinçli olarak metni sabitler).

## PR kontrol listesi

- [ ] `make test` geçiyor
- [ ] Davranış değişikliği için test var
- [ ] README / CHANGELOG gerekiyorsa güncellendi
- [ ] `.env`, API anahtarı veya kişisel `data/` dosyası yok
- [ ] Değişiklik tek amaçlı; commit mesajları açıklayıcı
- [ ] Yeni dosya varsa allow-list / hijyen testi güncellendi

## Yayın akışı (yalnızca bakımcı)

Public repo, bakımcının private reposundan `tools/publish.sh` ile üretilen bir
**anlık görüntüdür** (git geçmişi taşınmaz). Bu yüzden:

- Public `main`'e doğrudan commit atılmaz; katkılar fork + PR ile gelir.
- Merge edilen PR, bakımcı tarafından private repoya alınır ve bir sonraki
  yayında public'e yansır. Bu sırada commit SHA'sı değişebilir; bu normaldir.
- Katkınızın public geçmişinde görünmesi bir sonraki yayını bekleyebilir.

Katkıda bulunanların `tools/publish.sh` çalıştırması gerekmez.

## Sorular

Issue açmadan önce README §5 (sık bozulan şeyler) ve mevcut issue'lara bakın.
Davranış kuralları için [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), güvenlik
bildirimleri için [SECURITY.md](SECURITY.md).
