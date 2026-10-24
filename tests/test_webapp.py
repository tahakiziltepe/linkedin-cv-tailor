"""webapp/web_app.py: auth, dashboard, API ve prompt paneli."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_protected_pages_redirect_to_login(client):
    for path in ("/", "/prompts"):
        response = client.get(path)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


def test_api_requires_login_returns_401(client):
    response = client.post("/api/update_status", json={})
    assert response.status_code == 401
    assert response.get_json()["error"] == "Unauthorized"


def test_login_page_renders(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"login" in response.data.lower() or b"giri" in response.data.lower()


def test_login_wrong_password(client):
    response = client.post(
        "/login", data={"username": "tester", "password": "yanlis"}
    )
    assert response.status_code == 200
    assert "Geçersiz" in response.get_data(as_text=True)


def test_login_legacy_plaintext_user(client):
    response = client.post(
        "/login", data={"username": "legacy", "password": "plain-pass"}
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_login_success_and_logout(client):
    response = client.post(
        "/login", data={"username": "tester", "password": "secret"}
    )
    assert response.status_code == 302
    assert client.get("/").status_code == 200
    assert client.get("/logout").status_code == 302
    assert client.get("/").status_code == 302


def test_dashboard_renders_tracked_jobs(logged_in, webapp_module):
    webapp_module.tracker.add_job(
        {
            "company": "ACME",
            "title": "Data Engineer",
            "url": "https://example.com/j/1",
            "pdf_path": None,
        }
    )
    response = logged_in.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "ACME" in body and "Data Engineer" in body


def test_prompts_page_lists_prompts(logged_in):
    response = logged_in.get("/prompts")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Prompt Yonetimi" in body
    assert "CV uyarlama" in body


def test_prompt_save_creates_override(logged_in, webapp_module, prompt_dirs):
    response = logged_in.post(
        "/prompts/save",
        data={"name": "suitability", "text": "YENI {{JOB_DESCRIPTION}}"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert prompt_dirs.has_override("suitability")
    assert "YENI" in prompt_dirs.load_prompt("suitability")


def test_prompt_save_rejects_blank(logged_in, prompt_dirs):
    response = logged_in.post(
        "/prompts/save",
        data={"name": "suitability", "text": "   "},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert not prompt_dirs.has_override("suitability")
    assert "Kaydedilemedi" in response.get_data(as_text=True)


def test_prompt_preview_fills_tokens(logged_in):
    response = logged_in.post(
        "/prompts/preview",
        data={
            "name": "fix_typst",
            "text": "HATA={{ERROR_MESSAGE}} KOD={{BROKEN_TYPST_CODE}}",
        },
    )
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    preview = body.split("<pre", 1)[1]
    assert "{{" not in preview
    assert "error:" in preview


def test_prompt_reset_restores_default(logged_in, prompt_dirs):
    prompt_dirs.save_prompt(
        "fix_typst", "gecici {{ERROR_MESSAGE}} {{BROKEN_TYPST_CODE}}"
    )
    response = logged_in.post(
        "/prompts/reset", data={"name": "fix_typst"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert prompt_dirs.load_prompt("fix_typst") == prompt_dirs.load_default("fix_typst")


def test_update_status_success(logged_in, webapp_module):
    webapp_module.tracker.add_job(
        {"company": "A", "title": "T", "url": "u1", "pdf_path": None}
    )
    response = logged_in.post(
        "/api/update_status", json={"url": "u1", "status": "Applied"}
    )
    assert response.status_code == 200
    assert response.get_json()["success"] is True
    assert webapp_module.tracker.load_history()[0]["status"] == "Applied"
    assert webapp_module.status_logger.load_logs()[0]["new_status"] == "Applied"


def test_update_status_blocked_adds_company(logged_in, webapp_module):
    webapp_module.tracker.add_job(
        {"company": "Kotu Sirket", "title": "T", "url": "u2", "pdf_path": None}
    )
    response = logged_in.post(
        "/api/update_status", json={"url": "u2", "status": "Blocked Company"}
    )
    assert response.status_code == 200
    blocked = json.loads(
        webapp_module.BLOCKED_COMPANIES_FILE.read_text(encoding="utf-8")
    )
    assert "Kotu Sirket" in blocked


def test_update_status_validation(logged_in):
    assert logged_in.post("/api/update_status", json={}).status_code == 400
    assert (
        logged_in.post(
            "/api/update_status", json={"url": "yok", "status": "Applied"}
        ).status_code
        == 404
    )


def test_update_notes(logged_in, webapp_module):
    webapp_module.tracker.add_job(
        {"company": "A", "title": "T", "url": "u3", "pdf_path": None}
    )
    response = logged_in.post(
        "/api/update_notes", json={"url": "u3", "notes": "gorusme var"}
    )
    assert response.status_code == 200
    assert webapp_module.tracker.load_history()[0]["notes"] == "gorusme var"


def test_delete_job_api(logged_in, webapp_module):
    webapp_module.tracker.add_job(
        {"company": "A", "title": "T", "url": "u4", "pdf_path": None}
    )
    assert logged_in.post("/api/delete_job", json={"url": "u4"}).status_code == 200
    assert webapp_module.tracker.job_exists("u4") is False
    assert logged_in.post("/api/delete_job", json={"url": "u4"}).status_code == 404


def test_add_job_api(logged_in, webapp_module):
    response = logged_in.post(
        "/api/add_job", json={"company": "Manuel", "title": "Uzman"}
    )
    assert response.status_code == 200
    job = response.get_json()["job"]
    assert job["url"].startswith("manual-job-")
    assert webapp_module.tracker.job_exists(job["url"])


def test_add_job_requires_company_and_title(logged_in):
    assert logged_in.post("/api/add_job", json={"company": "A"}).status_code == 400


def test_blocked_companies_get_and_post(logged_in, webapp_module):
    response = logged_in.post(
        "/api/blocked_companies",
        json={"companies": [" A ", "", 3, "B"]},
    )
    assert response.status_code == 200
    assert response.get_json()["companies"] == ["A", "B"]
    assert logged_in.get("/api/blocked_companies").get_json() == ["A", "B"]


def test_download_file(logged_in, webapp_module):
    pdf = webapp_module.OUTPUT_DIR / "cv.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")
    response = logged_in.get("/download/cv.pdf")
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")


def test_download_path_traversal_blocked(logged_in, webapp_module):
    (webapp_module.DATA_DIR / "gizli.txt").write_text(" sir ", encoding="utf-8")
    response = logged_in.get("/download/../gizli.txt")
    assert response.status_code in (400, 404)


def test_secret_key_required_at_import():
    """SECRET_KEY yoksa uygulama acik hata vermeli (gercek .env'i devre disi)."""
    code = (
        "import os, sys\n"
        "import dotenv\n"
        "dotenv.load_dotenv = lambda *a, **k: None\n"
        "os.environ.pop('SECRET_KEY', None)\n"
        f"sys.path.insert(0, {str(ROOT)!r})\n"
        "import webapp.web_app\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "SECRET_KEY" in result.stderr
