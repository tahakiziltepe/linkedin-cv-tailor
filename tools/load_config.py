"""Prints run_daily.sh settings from config.toml as bash statements.

Usage (inside run_daily.sh):  eval "$(uv run python tools/load_config.py)"
Missing config.toml falls back to built-in defaults so daily runs keep working.
.env AUTO_PUSH overrides config auto_push.
"""
import os
import shlex
import sys
import tomllib
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CONFIG = BASE / "config.toml"


def main() -> None:
    cfg: dict = {}
    if CONFIG.exists():
        with open(CONFIG, "rb") as f:
            cfg = tomllib.load(f)

    limit = int(cfg.get("limit", 100))
    hours = int(cfg.get("hours", 12))
    auto_push = os.environ.get(
        "AUTO_PUSH",
        str(cfg.get("auto_push", False)).lower(),
    ).lower()
    if auto_push in ("1", "true", "yes", "on"):
        auto_push = "true"
    elif auto_push in ("0", "false", "no", "off"):
        auto_push = "false"
    else:
        raise SystemExit(f"AUTO_PUSH gecersiz: {auto_push!r}")

    queries = cfg.get("queries"  , ["data engineer", "business intelligence"])
    locations = cfg.get("locations", ["Turkey", "Istanbul"])
    if not queries or not locations:
        raise SystemExit("config.toml: queries ve locations bos olamaz")

    q = " ".join(shlex.quote(str(x)) for x in queries)
    l = " ".join(shlex.quote(str(x)) for x in locations)
    print(f"LIMIT={limit}")
    print(f"HOURS={hours}")
    print(f"AUTO_PUSH={auto_push}")
    print(f"QUERIES=({q})")
    print(f"LOCATIONS=({l})")


if __name__ == "__main__":
    main()
