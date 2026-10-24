"""Regresyon ve hijyen: prompt metinleri, garble, sirlar, allow-list."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys_path_added = False

if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

from tests.fixtures.legacy_prompts import LEGACY_PROMPTS  # noqa: E402

GARBLE_RE = re.compile(r"[\u0400-\u04FF\u4E00-\u9FFF\u3040-\u30FF]")

TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".html",
    ".css",
    ".js",
    ".toml",
    ".sh",
    ".typ",
    ".json",
    ".example",
    ".gitignore",
}

ROOT_REQUIRED = {
    ".env.example",
    ".gitignore",
    ".python-version",
    "uv.lock",
    "pyproject.toml",
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "Makefile",
    "config.toml",
    "doctor.py",
    "main.py",
    "run_daily.sh",
    "templates/base_cv.example.typ",
    "data/database/users.example.json",
    "webapp/web_app.py",
    "webapp/static/css/styles.css",
    "webapp/static/js/main.js",
}


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout


def tracked_files():
    return [line for line in git("ls-files").splitlines() if line]


def test_prompt_files_match_legacy_texts():
    import src.prompts as prompts

    for name, legacy in LEGACY_PROMPTS.items():
        current = prompts.load_default(name)
        assert current.strip() == legacy.strip(), f"{name} prompt metni degismis"


def test_prompt_files_have_required_tokens():
    import src.prompts as prompts

    for name, tokens in prompts.PROMPT_TOKENS.items():
        text = prompts.load_default(name)
        for token in tokens:
            assert "{{" + token + "}}" in text, f"{name}: {token} eksik"


def test_no_inline_prompts_left_in_cv_tailor():
    source = (ROOT / "src" / "cv_tailor.py").read_text(encoding="utf-8")
    assert 'prompt = f"""' not in source
    for name in ("suitability", "tailor_cv", "fix_typst"):
        assert re.search(rf'render_prompt\(\s*"{name}"', source), f"{name} render_prompt kullanmiyor"


def test_no_garble_in_tracked_text_files():
    problems = []
    for rel in tracked_files():
        path = ROOT / rel
        if path.suffix not in TEXT_SUFFIXES and path.name not in {
            ".gitignore",
            ".env.example",
        }:
            continue
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if GARBLE_RE.search(line):
                problems.append(f"{rel}:{lineno}: {line[:60]}")
    assert problems == []


def test_personal_data_not_in_publish_allow_list():
    """Kisisel veri private jurnalda tutulabilir; public allow-list'e giremez."""
    entries = parse_filelist()
    forbidden = {
        ".env",
        "data/base_cv.typ",
        "data/database/job_history.json",
        "data/database/users.json",
        "data/blocked_companies.json",
        "data/prompts/suitability.md",
        "data/prompts_history/suitability/20260101_000000.md",
    }
    for path in forbidden:
        assert not is_covered(path, entries), f"{path} public allow-list'te"


def test_gitignore_covers_personal_files():
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in (".env", "data/prompts/", "data/prompts_history/", "data/base_cv.typ"):
        assert pattern in text


def parse_filelist():
    text = (ROOT / "tools" / "publish.sh").read_text(encoding="utf-8")
    match = re.search(r"FILELIST=\((.*?)\n\)", text, re.S)
    assert match, "publish.sh icinde FILELIST bulunamadi"
    entries = []
    for line in match.group(1).splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            entries.extend(line.split())
    return entries


def is_covered(path, entries):
    for entry in entries:
        entry = entry.rstrip("/")
        if path == entry or path.startswith(entry + "/"):
            return True
    return False


def test_publish_allow_list_is_complete():
    """Yeni bir src/webapp/prompts/tools dosyasi allow-list'te unutulmasin."""
    entries = parse_filelist()
    missing = []
    for path in tracked_files():
        relevant = (
            (path.startswith("src/") and path.endswith(".py"))
            or (path.startswith("prompts/") and path.endswith(".md"))
            or (path.startswith("webapp/templates/") and path.endswith(".html"))
            or (path.startswith("tools/") and path.endswith((".py", ".sh")))
            or path.startswith("tests/")
            or path in ROOT_REQUIRED
        )
        if relevant and not is_covered(path, entries):
            missing.append(path)
    assert missing == [], f"allow-list'te eksik: {missing}"
