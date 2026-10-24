"""tools/publish.sh: guard senaryolari ve snapshot icerigi."""
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def git(repo, *args):
    return subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=True
    )


@pytest.fixture
def repo(tmp_path):
    """Gercek projenin gecici, commit'lenmis kopyasi + bare remote."""
    dest = tmp_path / "repo"
    shutil.copytree(
        ROOT,
        dest,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", "data", "__pycache__", ".pytest_cache", ".env"
        ),
    )
    # allow-list'teki ornek veri dosyasi
    (dest / "data" / "database").mkdir(parents=True)
    shutil.copy(
        ROOT / "data" / "database" / "users.example.json",
        dest / "data" / "database" / "users.example.json",
    )

    git(dest, "init", "-q")
    git(dest, "symbolic-ref", "HEAD", "refs/heads/main")
    git(dest, "config", "user.email", "test@example.com")
    git(dest, "config", "user.name", "Test")
    git(dest, "add", "-A")
    git(dest, "commit", "-qm", "init")

    bare = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True)
    git(dest, "remote", "add", "origin", str(bare))
    git(dest, "push", "-qu", "origin", "main")
    return dest


def publish(repo, tmp_path, extra_env=None):
    stage_root = tmp_path / "stage"
    stage_root.mkdir(exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            "PUBLIC_REPO_URL": str(tmp_path / "remote.git"),
            "PUB_DIR": str(tmp_path / "public"),
            "STAGE_ROOT": str(stage_root),
            "DRY": "1",
            "PUBLISH_SKIP_TESTS": "1",
        }
    )
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", "tools/publish.sh"],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
    )


def stage_dir(result):
    match = re.search(r"Stage klasörü korundu: (\S+)", result.stdout)
    assert match, result.stdout + result.stderr
    return Path(match.group(1))


def test_clean_repo_publishes_snapshot(repo, tmp_path):
    result = publish(repo, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "yayına hazır" in result.stdout

    stage = stage_dir(result)
    assert (stage / "prompts" / "suitability.md").exists()
    assert (stage / "src" / "prompts.py").exists()
    assert (stage / "tests" / "test_prompts.py").exists()
    assert (stage / "data" / "base_cv.typ").exists()
    assert not (stage / "data" / "prompts").exists()
    assert not (stage / ".env").exists()


def test_wrong_branch_blocked(repo, tmp_path):
    git(repo, "checkout", "-q", "-b", "feature")
    result = publish(repo, tmp_path)
    assert result.returncode == 1
    assert "sadece 'main'den" in result.stdout


def test_unsynced_main_blocked(repo, tmp_path):
    (repo / "README.md").write_text("degisti\n", encoding="utf-8")
    git(repo, "commit", "-qam", "yerel commit")
    result = publish(repo, tmp_path)
    assert result.returncode == 1
    assert "aynı değil" in result.stdout


def test_dirty_allow_list_file_blocked(repo, tmp_path):
    (repo / "README.md").write_text("commit edilmemis\n", encoding="utf-8")
    result = publish(repo, tmp_path)
    assert result.returncode == 1
    assert "commit edilmemiş" in result.stdout


def test_untracked_allow_list_file_blocked(repo, tmp_path):
    git(repo, "rm", "-q", "--cached", "README.md")
    git(repo, "commit", "-qm", "README takipten cikti")
    git(repo, "push", "-q", "origin", "main")
    result = publish(repo, tmp_path)
    assert result.returncode == 1
    assert "takipli değil" in result.stdout


def test_failing_tests_block_publish(repo, tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_uv = bin_dir / "uv"
    fake_uv.write_text("#!/bin/bash\nexit 1\n", encoding="utf-8")
    fake_uv.chmod(0o755)

    result = publish(
        repo,
        tmp_path,
        extra_env={
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "PUBLISH_SKIP_TESTS": "0",
        },
    )
    assert result.returncode == 1
    assert "testler geçmedi" in result.stdout


def test_passing_tests_allow_publish(repo, tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_uv = bin_dir / "uv"
    fake_uv.write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
    fake_uv.chmod(0o755)

    result = publish(
        repo,
        tmp_path,
        extra_env={
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "PUBLISH_SKIP_TESTS": "0",
        },
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "yayına hazır" in result.stdout
