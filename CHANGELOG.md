# Changelog

## [1.0.0] — 2026-10-24

### Added
- LinkedIn scraping (JobSpy), AI filtreleme ve CV uyarlama pipeline'ı (`main.py`)
- Gemini ile: ilan uygunluk kontrolü (YES/NO), CV kişiselleştirme, bozuk Typst kodunu otomatik onarım
- Typst → PDF üretimi
- Telegram bildirim desteği (`src/notifier.py`)
- Başvuru takibi: `job_history.json` + durum değişiklik logu
- Web paneli (Flask): dashboard, durum yönetimi, PDF indirme (hash'li şifre + zorunlu SECRET_KEY)
- Günlük toplu tur: `run_daily.sh` + `config.toml` ayarları, otomatik push kapalı varsayılan
- `doctor.py` ortam self-testi, `Makefile` hedefleri
- Operasyon rehberi (5 Dakikada Restore, arıza noktaları, token arıza tablosu)
- `tools/publish.sh`: private → public snapshot senkronu (geçmiş taşınmaz, kişisel veri taramalı)
- Prompt'lar ayrı dosyalarda (`prompts/`); web panelinden düzenleme, kuru
  önizleme, varsayılana dönme ve son 20 sürüm yedeği (`data/prompts/`,
  `data/prompts_history/`)
