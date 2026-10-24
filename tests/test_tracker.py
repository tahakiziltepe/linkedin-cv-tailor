"""src/tracker.py: JSON gecmis yonetimi."""
import json


def test_init_creates_empty_history(tracker):
    assert tracker.history_file.exists()
    assert tracker.load_history() == []


def test_add_job_inserts_at_top_with_defaults(tracker):
    tracker.add_job({"company": "A", "title": "T1", "url": "u1", "pdf_path": None})
    tracker.add_job({"company": "B", "title": "T2", "url": "u2", "pdf_path": "x.pdf"})
    history = tracker.load_history()
    assert [j["url"] for j in history] == ["u2", "u1"]
    assert history[0]["status"] == "Pending"
    assert history[0]["notes"] == ""


def test_duplicate_url_ignored(tracker):
    tracker.add_job({"company": "A", "title": "T", "url": "u", "pdf_path": None})
    tracker.add_job({"company": "A2", "title": "T2", "url": "u", "pdf_path": None})
    assert len(tracker.load_history()) == 1


def test_job_exists(tracker):
    assert tracker.job_exists("u") is False
    tracker.add_job({"company": "A", "title": "T", "url": "u", "pdf_path": None})
    assert tracker.job_exists("u") is True
    assert tracker.job_exists("baska") is False


def test_delete_job(tracker):
    tracker.add_job({"company": "A", "title": "T", "url": "u", "pdf_path": None})
    assert tracker.delete_job("u") is True
    assert tracker.job_exists("u") is False
    assert tracker.delete_job("u") is False


def test_corrupt_json_returns_empty(tracker):
    tracker.history_file.write_text("{bozuk json", encoding="utf-8")
    assert tracker.load_history() == []


def test_unicode_roundtrip(tracker):
    tracker.add_job(
        {"company": "Şirket", "title": "İş Zekası", "url": "u", "pdf_path": None}
    )
    raw = tracker.history_file.read_text(encoding="utf-8")
    assert "Şirket" in raw and "İş Zekası" in raw
    assert json.loads(raw)[0]["company"] == "Şirket"
