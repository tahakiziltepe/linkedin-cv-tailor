"""Prompt dosyalarini yukleme, doldurma ve kaydetme.

Varsayilan prompt'lar `prompts/` altindadir (git takipli). Kullanici
duzenlemeleri `data/prompts/` altinda ayni adla tutulur (gitignore'lu).
Yukleme sirasi: once override, yoksa varsayilan.

Yer tutucular {{TOKEN}} bicimindedir; render ederken deger ile degistirilir.
"""
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULTS_DIR = BASE_DIR / "prompts"
OVERRIDES_DIR = BASE_DIR / "data" / "prompts"
HISTORY_DIR = BASE_DIR / "data" / "prompts_history"
MAX_BACKUPS = 20

TOKEN_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
NAME_RE = re.compile(r"^[a-z0-9_]+$")

# Her prompt icin kullanilan degiskenler
PROMPT_TOKENS = {
    "suitability": ["JOB_DESCRIPTION"],
    "tailor_cv": ["BASE_CV_TYPST", "JOB_DESCRIPTION"],
    "fix_typst": ["ERROR_MESSAGE", "BROKEN_TYPST_CODE"],
}

PROMPT_LABELS = {
    "suitability": "Ilan uygunluk kontrolu (YES/NO)",
    "tailor_cv": "CV uyarlama",
    "fix_typst": "Typst kod onarimi",
}

# Kuru onizlemede kullanilan ornek degerler
SAMPLE_VALUES = {
    "JOB_DESCRIPTION": (
        "Ornek ilan: Data Engineer. SQL, ETL, BigQuery ve Power BI deneyimi beklenir."
    ),
    "BASE_CV_TYPST": (
        '== Profile\nOrnek kisi, veri muhendisi.\n\n'
        '== Work Experience\n#work(title: "Data Engineer", company: "Ornek A.S.")'
    ),
    "ERROR_MESSAGE": 'error: unexpected argument: "dates"',
    "BROKEN_TYPST_CODE": '#work(\n  title: "Data Engineer"\n)',
}


def prompt_names():
    """Düzenlenebilir prompt adlarini dondurur."""
    return list(PROMPT_TOKENS)


def _check_name(name):
    if name not in PROMPT_TOKENS:
        raise ValueError(f"Bilinmeyen prompt: {name}")
    if not NAME_RE.match(name):
        raise ValueError(f"Gecersiz prompt adi: {name}")


def default_path(name):
    _check_name(name)
    return DEFAULTS_DIR / f"{name}.md"


def override_path(name):
    _check_name(name)
    return OVERRIDES_DIR / f"{name}.md"


def has_override(name):
    return override_path(name).exists()


def load_default(name):
    path = default_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Varsayilan prompt bulunamadi: {path}")
    return path.read_text(encoding="utf-8")


def load_prompt(name):
    """Override varsa onu, yoksa varsayilani dondurur."""
    path = override_path(name) if has_override(name) else default_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Prompt bulunamadi: {path}")
    return path.read_text(encoding="utf-8")


def render(text, values):
    """{{TOKEN}} yer tutucularini values ile degistirir."""
    def repl(match):
        key = match.group(1)
        if key not in values:
            raise KeyError(f"Prompt degiskeni icin deger yok: {key}")
        return str(values[key])

    return TOKEN_RE.sub(repl, text)


def render_prompt(name, **values):
    """Prompt'u dosyadan okuyup degiskenleri doldurur."""
    return render(load_prompt(name), values)


def missing_tokens(name, text=None):
    """Metinde eksik olan beklenen token'lari dondurur."""
    _check_name(name)
    if text is None:
        text = load_prompt(name)
    present = set(TOKEN_RE.findall(text))
    return [t for t in PROMPT_TOKENS[name] if t not in present]


def _backup(name, text):
    target = HISTORY_DIR / name
    target.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    (target / f"{stamp}.md").write_text(text, encoding="utf-8")
    backups = sorted(target.glob("*.md"))
    for old in backups[:-MAX_BACKUPS]:
        old.unlink()


def _atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".md")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def save_prompt(name, text):
    """Metni override olarak kaydeder; onceki halini yedekler."""
    _check_name(name)
    text = (text or "").strip()
    if not text:
        raise ValueError("Prompt bos olamaz.")

    path = override_path(name)
    if path.exists():
        _backup(name, path.read_text(encoding="utf-8"))

    _atomic_write(path, text + "\n")
    return path


def reset_prompt(name):
    """Varsayilanin kopyasini override olarak yazar."""
    _check_name(name)
    text = load_default(name).strip()
    save_prompt(name, text)
    return text


def preview_prompt(name, text=None):
    """Kuru onizleme: token'lari ornek degerlerle doldurur (API cagrisi yok)."""
    _check_name(name)
    if text is None:
        text = load_prompt(name)
    return render(text, SAMPLE_VALUES)
