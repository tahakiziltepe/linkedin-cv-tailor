"""Ortam self-testi: uv run python doctor.py

Kontroller:
1- bagimliliklar import edilebilir mi
2- .env anahtarlari var mi (GEMINI zorunlu; Telegram/SECRET_KEY opsiyonel)
3- GEMINI anahtari + model adi gecerli mi (404 = README 5.1 senaryosu)
4- TELEGRAM anahtari gecerli mi (mesaj gonderilmez, sadece getMe)
5- typst derliyor mu (mini .typ -> PDF)
6- tracker.json yazma/okuma smoke test

Cikis kodu: FAIL varsa 0\'dan farkli.
"""
import os
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

try:
    from dotenv import load_dotenv
except ImportError:
    print("FAIL: .venv yok mu? Once: uv sync")
    sys.exit(1)

load_dotenv(BASE / ".env")

RESULTS = []


def add(level, name, detail=""):
    RESULTS.append(level)
    line = f"[{level:4}] {name}"
    if detail:
        line += f"  -> {detail}"
    print(line)


# 1) bagimliliklar
try:
    import jobspy  # noqa: F401
    import google.genai  # noqa: F401
    import typst  # noqa: F401
    import pandas  # noqa: F401
    import flask  # noqa: F401

    add("PASS", "bagimlilik importlari")
except Exception as e:
    add("FAIL", "bagimlilik importlari", str(e)[:120])
    print("\nFix: uv sync")
    sys.exit(1)

# 2) .env anahtarlari
gemini = os.environ.get("GEMINI_API_KEY", "").strip()
telegram = os.environ.get("TELEGRAM_TOKEN", "").strip()
if gemini:
    add("PASS", "GEMINI_API_KEY var")
else:
    add("FAIL", "GEMINI_API_KEY yok - pipeline calismaz", ".env'e ekle")
if telegram:
    add("PASS", "TELEGRAM_TOKEN var")
else:
    add("WARN", "TELEGRAM_TOKEN yok - bildirim yok, CV yine uretilir")
if not os.environ.get("SECRET_KEY"):
    add("WARN", "SECRET_KEY yok - web panel baslamaz", ".env'e ekle")

# 3) Gemini + model adi
if gemini:
    try:
        import src.cv_tailor as ct

        if not ct.client:
            add("FAIL", "gemini client", "client olusturulamadi")
        else:
            r = ct.client.models.generate_content(
                model=ct.GEMINI_MODEL_FLASH, contents="Reply: OK"
            )
            body = (r.text or "").strip()
            ok = bool(body)  # 200 + bos olmayan cevap = model adi gecerli
            add("PASS" if ok else "FAIL", f"gemini model: {ct.GEMINI_MODEL_FLASH}", body[:40])
    except Exception as e:
        msg = str(e)[:160]
        add("FAIL", "gemini cagrisi", msg)
        if "404" in msg or "no longer available" in msg:
            print("  -> Model kapanmis olabilir. README 5.1 bolumunu uygula.")

# 4) Telegram getMe (mesaj gonderilmez)
if telegram:
    try:
        import requests

        resp = requests.post(
            f"https://api.telegram.org/bot{telegram}/getMe", timeout=10
        ).json()
        bot = (resp.get("result") or {}).get("username", "?")
        add("PASS" if resp.get("ok") else "FAIL", f"telegram bot: @{bot}")
    except Exception as e:
        add("FAIL", "telegram getMe", str(e)[:120])

# 5) typst
try:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        (tmp / "t.typ").write_text("Merhaba *dunya* #set page(margin: 1cm)")
        typst.compile(str(tmp / "t.typ"), output=str(tmp / "t.pdf"))
        size = (tmp / "t.pdf").stat().st_size
        add("PASS", f"typst derleme ({size} bayt)")
except Exception as e:
    add("FAIL", "typst derleme", str(e)[:160])
    print("  -> README 5.3 bolumu: surum sabitleme")

# 6) tracker
try:
    from src.tracker import JobTracker

    with tempfile.TemporaryDirectory() as d:
        t = JobTracker(Path(d))
        t.add_job({"company": "X", "title": "Y", "url": "u", "pdf_path": None})
        assert t.job_exists("u") and t.delete_job("u")
        add("PASS", "tracker JSON yazma")
except Exception as e:
    add("FAIL", "tracker", str(e)[:120])

fails = sum(1 for lvl in RESULTS if lvl == "FAIL")
print("\n---")
if fails:
    print(f"SONUC: {fails} FAIL - sorunlar yukarida")
else:
    print("SONUC: TAMAM")
sys.exit(1 if fails else 0)
