"""src/prompts.py: yukleme, render, kaydetme, yedekleme, sifirlama."""
import pytest


def test_default_prompts_load(prompt_dirs):
    for name in prompt_dirs.PROMPT_TOKENS:
        text = prompt_dirs.load_prompt(name)
        assert text.strip()
        assert not prompt_dirs.has_override(name)


def test_override_takes_precedence(prompt_dirs):
    prompt_dirs.save_prompt("suitability", "OVERRIDE {{JOB_DESCRIPTION}}")
    assert prompt_dirs.has_override("suitability")
    assert prompt_dirs.load_prompt("suitability").startswith("OVERRIDE")
    # diger prompt'lar varsayilan kalir
    assert not prompt_dirs.has_override("tailor_cv")


def test_render_replaces_tokens(prompt_dirs):
    out = prompt_dirs.render_prompt("fix_typst", ERROR_MESSAGE="hata", BROKEN_TYPST_CODE="kod")
    assert "hata" in out and "kod" in out
    assert "{{" not in out


def test_render_missing_value_raises(prompt_dirs):
    with pytest.raises(KeyError):
        prompt_dirs.render_prompt("fix_typst", ERROR_MESSAGE="hata")


def test_missing_tokens_detected(prompt_dirs):
    assert prompt_dirs.missing_tokens("tailor_cv", "token yok") == [
        "BASE_CV_TYPST",
        "JOB_DESCRIPTION",
    ]


def test_blank_save_rejected(prompt_dirs):
    for value in ("", "   ", "\n\t"):
        with pytest.raises(ValueError):
            prompt_dirs.save_prompt("suitability", value)
    assert not prompt_dirs.has_override("suitability")


def test_invalid_name_rejected(prompt_dirs):
    with pytest.raises(ValueError):
        prompt_dirs.load_prompt("../etc/passwd")
    with pytest.raises(ValueError):
        prompt_dirs.save_prompt("bilinmeyen", "x")


def test_backup_rotation_keeps_20(prompt_dirs):
    for i in range(25):
        prompt_dirs.save_prompt("suitability", f"surum {i} {{{{JOB_DESCRIPTION}}}}")
    backups = sorted((prompt_dirs.HISTORY_DIR / "suitability").glob("*.md"))
    assert len(backups) == prompt_dirs.MAX_BACKUPS == 20
    # en eski surumler silinmis, en yeniler kalmis
    names = [p.name for p in backups]
    assert "surum 0" not in " ".join(
        p.read_text(encoding="utf-8") for p in backups
    )
    assert names == sorted(names)


def test_reset_copies_default(prompt_dirs):
    prompt_dirs.save_prompt("tailor_cv", "gecici {{BASE_CV_TYPST}} {{JOB_DESCRIPTION}}")
    prompt_dirs.reset_prompt("tailor_cv")
    assert prompt_dirs.load_prompt("tailor_cv") == prompt_dirs.load_default("tailor_cv")


def test_preview_uses_sample_values(prompt_dirs):
    out = prompt_dirs.preview_prompt("tailor_cv")
    assert "{{" not in out
    assert "Ornek" in out or "ornek" in out


def test_atomic_write_leaves_no_temp_files(prompt_dirs):
    prompt_dirs.save_prompt("fix_typst", "x {{ERROR_MESSAGE}} {{BROKEN_TYPST_CODE}}")
    leftovers = list(prompt_dirs.OVERRIDES_DIR.glob(".tmp-*"))
    assert leftovers == []
