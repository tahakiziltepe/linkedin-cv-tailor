"""main.py: tum dis servisler mock'lanmis orkestrasyon testleri."""
import json
import sys
from pathlib import Path

from tests.conftest import SAMPLE_JOB


class FakeNotifier:
    def __init__(self):
        self.calls = []

    def notify_suitable_job(self, **kwargs):
        self.calls.append(kwargs)
        return True


def set_args(monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["main.py", "-q", "data engineer", "-n", "1", "--hours", "48"]
    )


def fake_render_ok(content, path):
    Path(path).write_bytes(b"%PDF-1.4 test")
    Path(path).with_suffix(".typ").write_text(content, encoding="utf-8")


def run(main_module, monkeypatch, jobs, suitable=True, tailored="#set page()\nCV"):
    m = main_module
    monkeypatch.setattr(m, "find_jobs", lambda *a, **k: list(jobs))
    monkeypatch.setattr(m, "check_job_suitability", lambda desc: suitable)
    monkeypatch.setattr(m, "tailor_cv", lambda cv, desc: tailored)
    fake_notifier = FakeNotifier()
    monkeypatch.setattr(m, "notifier", fake_notifier)
    set_args(monkeypatch)
    m.main()
    return fake_notifier


def history(main_module):
    return main_module.JobTracker(main_module.DATABASE_DIR).load_history()


def test_happy_path_generates_pdf_and_tracks(main_module, monkeypatch):
    main_module.render_pdf = fake_render_ok
    notifier = run(main_module, monkeypatch, [dict(SAMPLE_JOB)])

    entries = history(main_module)
    assert len(entries) == 1
    assert entries[0]["company"] == "Ornek A.S."
    assert entries[0]["title"] == "Data Engineer"
    assert entries[0]["pdf_path"].endswith(".pdf")
    assert entries[0]["status"] == "Pending"
    assert notifier.calls and notifier.calls[0]["company"] == "Ornek A.S."
    assert (main_module.OUTPUT_DIR / entries[0]["pdf_path"]).exists()


def test_unsuitable_job_is_logged_not_notified(main_module, monkeypatch):
    main_module.render_pdf = fake_render_ok
    notifier = run(main_module, monkeypatch, [dict(SAMPLE_JOB)], suitable=False)

    entries = history(main_module)
    assert len(entries) == 1
    assert entries[0]["status"] == "Not Interested"
    assert entries[0]["pdf_path"] is None
    assert notifier.calls == []


def test_blocked_company_is_skipped(main_module, monkeypatch):
    blocked = main_module.DATA_DIR / "blocked_companies.json"
    blocked.write_text(json.dumps(["ornek a.s."]), encoding="utf-8")
    main_module.render_pdf = fake_render_ok
    notifier = run(main_module, monkeypatch, [dict(SAMPLE_JOB)])

    entries = history(main_module)
    assert len(entries) == 1
    assert entries[0]["status"] == "Blocked Company"
    assert notifier.calls == []


def test_duplicate_job_skipped(main_module, monkeypatch):
    tracker = main_module.JobTracker(main_module.DATABASE_DIR)
    tracker.add_job(
        {
            "company": "Ornek A.S.",
            "title": "Data Engineer",
            "url": SAMPLE_JOB["job_url"],
            "pdf_path": None,
        }
    )
    main_module.render_pdf = fake_render_ok
    run(main_module, monkeypatch, [dict(SAMPLE_JOB)])
    assert len(history(main_module)) == 1


def test_missing_description_skipped(main_module, monkeypatch):
    job = dict(SAMPLE_JOB, description="")
    main_module.render_pdf = fake_render_ok
    run(main_module, monkeypatch, [job])
    assert history(main_module) == []


def test_no_jobs_does_nothing(main_module, monkeypatch):
    notifier = run(main_module, monkeypatch, [])
    assert history(main_module) == []
    assert notifier.calls == []


def test_compile_failure_then_fix_succeeds(main_module, monkeypatch):
    calls = {"render": 0, "fix": 0}

    def flaky_render(content, path):
        calls["render"] += 1
        if calls["render"] == 1:
            raise RuntimeError("beklenmeyen argüman")
        fake_render_ok(content, path)

    def fake_fix(code, error):
        calls["fix"] += 1
        return "#set page()\nduzeltildi"

    monkeypatch.setattr(main_module, "render_pdf", flaky_render)
    monkeypatch.setattr(main_module, "fix_typst_code", fake_fix)
    run(main_module, monkeypatch, [dict(SAMPLE_JOB)])

    entries = history(main_module)
    assert len(entries) == 1
    assert calls["fix"] == 1
    assert calls["render"] >= 2


def test_compile_failure_all_retries_leaves_no_entry(main_module, monkeypatch):
    def always_fail(content, path):
        raise RuntimeError("hala bozuk")

    monkeypatch.setattr(main_module, "render_pdf", always_fail)
    monkeypatch.setattr(main_module, "fix_typst_code", lambda code, err: "yine bozuk")
    run(main_module, monkeypatch, [dict(SAMPLE_JOB)])
    assert history(main_module) == []


def test_fix_returns_none_stops_loop(main_module, monkeypatch):
    def always_fail(content, path):
        raise RuntimeError("bozuk")

    monkeypatch.setattr(main_module, "render_pdf", always_fail)
    monkeypatch.setattr(main_module, "fix_typst_code", lambda code, err: None)
    run(main_module, monkeypatch, [dict(SAMPLE_JOB)])
    assert history(main_module) == []
