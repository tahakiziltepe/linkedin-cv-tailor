"""tools/load_config.py: config.toml -> bash degiskenleri."""
import pytest


def parse_output(text):
    values = {}
    for line in text.splitlines():
        key, _, value = line.partition("=")
        values[key] = value
    return values


def test_defaults_when_config_missing(tmp_path, monkeypatch, capsys):
    import tools.load_config as lc

    monkeypatch.setattr(lc, "CONFIG", tmp_path / "yok.toml")
    monkeypatch.delenv("AUTO_PUSH", raising=False)
    lc.main()
    out = parse_output(capsys.readouterr().out)
    assert out["LIMIT"] == "100"
    assert out["HOURS"] == "12"
    assert out["AUTO_PUSH"] == "false"
    assert "data engineer" in out["QUERIES"]


def test_custom_config(tmp_path, monkeypatch, capsys):
    import tools.load_config as lc

    cfg = tmp_path / "config.toml"
    cfg.write_text(
        'limit = 5\nhours = 7\nauto_push = true\n'
        'queries = ["data engineer", "bi"]\n'
        'locations = ["Turkey"]\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(lc, "CONFIG", cfg)
    monkeypatch.delenv("AUTO_PUSH", raising=False)
    lc.main()
    out = parse_output(capsys.readouterr().out)
    assert out["LIMIT"] == "5"
    assert out["HOURS"] == "7"
    assert out["AUTO_PUSH"] == "true"
    assert "bi" in out["QUERIES"]


@pytest.mark.parametrize("value", ["1", "true", "yes", "on"])
def test_env_auto_push_true_overrides_config(tmp_path, monkeypatch, capsys, value):
    import tools.load_config as lc

    cfg = tmp_path / "config.toml"
    cfg.write_text("auto_push = false\n", encoding="utf-8")
    monkeypatch.setattr(lc, "CONFIG", cfg)
    monkeypatch.setenv("AUTO_PUSH", value)
    lc.main()
    assert parse_output(capsys.readouterr().out)["AUTO_PUSH"] == "true"


def test_invalid_auto_push_exits(tmp_path, monkeypatch):
    import tools.load_config as lc

    monkeypatch.setattr(lc, "CONFIG", tmp_path / "yok.toml")
    monkeypatch.setenv("AUTO_PUSH", "belki")
    with pytest.raises(SystemExit):
        lc.main()


def test_empty_queries_exits(tmp_path, monkeypatch):
    import tools.load_config as lc

    cfg = tmp_path / "config.toml"
    cfg.write_text('queries = []\nlocations = ["Turkey"]\n', encoding="utf-8")
    monkeypatch.setattr(lc, "CONFIG", cfg)
    monkeypatch.delenv("AUTO_PUSH", raising=False)
    with pytest.raises(SystemExit):
        lc.main()
