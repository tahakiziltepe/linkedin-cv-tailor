"""Temiz makine simulasyonu: .env yokken doctor anlasilir hata vermeli."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.clean

IGNORE = shutil.ignore_patterns(
    ".git", ".venv", "data", "__pycache__", ".pytest_cache", ".env"
)


def copy_project(tmp_path):
    dest = tmp_path / "clean-repo"
    shutil.copytree(ROOT, dest, ignore=IGNORE)
    return dest


def clean_env():
    env = os.environ.copy()
    for key in ("GEMINI_API_KEY", "TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID", "SECRET_KEY"):
        env.pop(key, None)
    return env


def run_doctor(repo, env):
    return subprocess.run(
        [sys.executable, "doctor.py", "--offline"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )


def test_clean_machine_without_env_fails_with_hint(tmp_path):
    repo = copy_project(tmp_path)
    result = run_doctor(repo, clean_env())

    assert result.returncode == 1
    assert "GEMINI_API_KEY yok" in result.stdout
    assert "SONUC:" in result.stdout


def test_clean_machine_with_example_env_passes_offline(tmp_path):
    repo = copy_project(tmp_path)
    (repo / ".env").write_text(
        "GEMINI_API_KEY=fake-key\nSECRET_KEY=fake-secret\n", encoding="utf-8"
    )

    result = run_doctor(repo, clean_env())

    assert result.returncode == 0, result.stdout + result.stderr
    assert "SONUC: TAMAM" in result.stdout
    assert "[SKIP] gemini cagrisi" in result.stdout
