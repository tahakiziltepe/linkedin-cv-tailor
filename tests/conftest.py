"""Ortak pytest fixture'lari.

Kurallar:
- Testler gercek `data/` dizinine yazmaz (tmp_path kullanilir).
- Varsayilan paket ag/API cagrisi yapmaz (anahtarlar bosaltilir).
- Canli testler `RUN_LIVE_TESTS=1` ile calisir; o zaman gercek .env korunur.
"""
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Offline testlerde gercek anahtarlarin sizmasini engelle.
if os.environ.get("RUN_LIVE_TESTS") != "1":
    os.environ["GEMINI_API_KEY"] = ""
    os.environ["TELEGRAM_TOKEN"] = ""
    os.environ["TELEGRAM_CHAT_ID"] = ""
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("AUTO_PUSH", "0")

SAMPLE_JOB = {
    "title": "Data Engineer",
    "company": "Ornek A.S.",
    "description": "SQL, ETL, BigQuery ve Power BI deneyimi beklenir.",
    "job_url": "https://example.com/jobs/1",
}

SAMPLE_CV = """#set page(margin: 1cm)

= Ornek Kisi

== Profile
Veri muhendisi.

== Work Experience
#work(title: "Data Engineer", company: "Ornek A.S.")
"""


@pytest.fixture
def prompt_dirs(tmp_path, monkeypatch):
    """Prompt override/yedek dizinlerini gecici dizine tasir."""
    import src.prompts as prompts

    monkeypatch.setattr(prompts, "OVERRIDES_DIR", tmp_path / "prompts")
    monkeypatch.setattr(prompts, "HISTORY_DIR", tmp_path / "prompts_history")
    return prompts


@pytest.fixture
def tracker(tmp_path):
    from src.tracker import JobTracker

    database = tmp_path / "database"
    database.mkdir(parents=True, exist_ok=True)
    return JobTracker(database)


@pytest.fixture
def webapp_module(tmp_path, monkeypatch, prompt_dirs):
    """Flask uygulamasini gecici veri diziniyle hazirlar."""
    import webapp.web_app as wa
    from src.status_logger import StatusLogger
    from src.tracker import JobTracker
    from werkzeug.security import generate_password_hash

    data = tmp_path / "data"
    db = data / "database"
    out = data / "output"
    db.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)

    users = [
        {"username": "tester", "password": generate_password_hash("secret")},
        {"username": "legacy", "password": "plain-pass"},
    ]
    users_file = db / "users.json"
    users_file.write_text(json.dumps(users), encoding="utf-8")

    monkeypatch.setattr(wa, "DATA_DIR", data)
    monkeypatch.setattr(wa, "DATABASE_DIR", db)
    monkeypatch.setattr(wa, "OUTPUT_DIR", out)
    monkeypatch.setattr(wa, "USERS_FILE", users_file)
    monkeypatch.setattr(wa, "BLOCKED_COMPANIES_FILE", data / "blocked_companies.json")
    monkeypatch.setattr(wa, "tracker", JobTracker(db))
    monkeypatch.setattr(wa, "status_logger", StatusLogger(db))

    wa.app.config.update(TESTING=True, SECRET_KEY="test-secret-key")
    return wa


@pytest.fixture
def client(webapp_module):
    return webapp_module.app.test_client()


@pytest.fixture
def logged_in(client):
    response = client.post(
        "/login", data={"username": "tester", "password": "secret"}
    )
    assert response.status_code == 302, "test kullanicisi giris yapamadi"
    return client


@pytest.fixture
def main_module(tmp_path, monkeypatch):
    """main.py'yi gecici veri dizini ve hizli sleep ile hazirlar."""
    import time

    import main as m

    data = tmp_path / "data"
    (data / "database").mkdir(parents=True, exist_ok=True)
    (data / "output").mkdir(parents=True, exist_ok=True)
    (data / "base_cv.typ").write_text(SAMPLE_CV, encoding="utf-8")

    monkeypatch.setattr(m, "DATA_DIR", data)
    monkeypatch.setattr(m, "DATABASE_DIR", data / "database")
    monkeypatch.setattr(m, "OUTPUT_DIR", data / "output")
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    return m
