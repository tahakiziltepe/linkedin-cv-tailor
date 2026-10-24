"""src/job_search.py: JobSpy cagrisi mock'lanarak filtre/davranis testleri."""
import pandas as pd


def test_no_results_returns_empty(monkeypatch):
    import src.job_search as js

    monkeypatch.setattr(js, "scrape_jobs", lambda **kwargs: pd.DataFrame())
    assert js.find_jobs("data engineer", "Istanbul") == []


def test_results_converted_to_records(monkeypatch):
    import src.job_search as js

    df = pd.DataFrame(
        [
            {"title": "Data Engineer", "company": "A", "job_url": "u1"},
            {"title": "BI Developer", "company": "B", "job_url": "u2"},
        ]
    )
    captured = {}

    def fake_scrape(**kwargs):
        captured.update(kwargs)
        return df

    monkeypatch.setattr(js, "scrape_jobs", fake_scrape)
    jobs = js.find_jobs("data engineer", "Istanbul", results_wanted=2, hours_old=48)

    assert [j["job_url"] for j in jobs] == ["u1", "u2"]
    assert captured["site_name"] == ["linkedin"]
    assert captured["search_term"] == "data engineer"
    assert captured["results_wanted"] == 2
    assert captured["hours_old"] == 48
    assert captured["linkedin_fetch_description"] is True


def test_exception_returns_empty(monkeypatch):
    import src.job_search as js

    def boom(**kwargs):
        raise RuntimeError("ag hatasi")

    monkeypatch.setattr(js, "scrape_jobs", boom)
    assert js.find_jobs("x", "y") == []
