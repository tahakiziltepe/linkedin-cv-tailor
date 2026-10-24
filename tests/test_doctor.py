"""doctor.py: offline kontroller ve cikis kodu."""
import doctor


def test_offline_with_fake_gemini_has_no_fail(monkeypatch, capsys):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("TELEGRAM_TOKEN", "")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "")

    results = doctor.run_checks(offline=True)
    out = capsys.readouterr().out

    assert "FAIL" not in results
    assert "SKIP" in results  # gemini cagrisi atlandi
    assert "prompt dosyalari" in out
    assert "tracker JSON" in out


def test_missing_gemini_is_fail(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("TELEGRAM_TOKEN", "")

    results = doctor.run_checks(offline=True)
    assert "FAIL" in results


def test_main_returns_zero_when_ok(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("TELEGRAM_TOKEN", "")
    assert doctor.main(["--offline"]) == 0


def test_main_returns_nonzero_when_missing_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("TELEGRAM_TOKEN", "")
    assert doctor.main(["--offline"]) == 1
