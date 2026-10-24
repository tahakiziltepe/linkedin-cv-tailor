"""Hashes plaintext passwords in data/database/users.json (idempotent).

Run once after upgrading to hash-based auth, and again whenever the file
gains a new plaintext entry (e.g. manually added user):

    uv run python tools/hash_users.py

Entries already stored as a werkzeug hash ("pbkdf2:...", "scrypt:...")
are left untouched.
"""
import json
import sys
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent.parent
USERS_FILE = BASE_DIR / "data" / "database" / "users.json"


def is_hash(value: str) -> bool:
    """True if the value is already a werkzeug password hash."""
    try:
        # check_password_hash never raises on a valid-format hash; even with
        # a wrong password it returns False instead of erroring out.
        check_password_hash(value, "probe-password")
    except Exception:
        return False
    return isinstance(value, str) and ("pbkdf2" in value or "scrypt" in value or "argon2" in value)


def main() -> int:
    if not USERS_FILE.exists():
        print(f"Kullanıcı dosyası bulunamadı: {USERS_FILE}", file=sys.stderr)
        return 1

    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)

    changed = 0
    for user in users:
        current = user.get("password", "")
        if current and not is_hash(current):
            hashed = generate_password_hash(current)
            if not check_password_hash(hashed, current):
                raise RuntimeError(f"Kritik hata! Kullanıcı {user.get('username')} hash doğrulaması başarısız oldu!")
            user["password"] = hashed
            changed += 1
            print(f"Hash'lendi: {user.get('username')}")
        else:
            print(f"Zaten hash'li / boş, atlandı: {user.get('username')}")

    if changed:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        print(f"{changed} kayıt güncellendi. ({USERS_FILE})")
    else:
        print("Değişiklik gerekmedi.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
