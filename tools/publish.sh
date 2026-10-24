#!/bin/bash
# Private -> public hash snapshot ('snapshot sync'; git geçmişi taşınmaz!)
# 1. rsync ile allow-list dosyaları stage'lenir
# 2. kişisel-veri taraması (temiz değilse durur)
# 3. public clone'da commit + push
# Kullanim: PUBLIC_REPO_URL=https://github.com/me/repo ./tools/publish.sh
#           PUBLISH_CONFIRM=1 (tarama uyarilarini gecmek icin)
#           PUB_DIR=...      (varsayilan: /tmp/opencode/cv-builder-public)
set -euo pipefail

BASE_DIR=$(cd "$(dirname "$0")/.." && pwd)
PUB_DIR="${PUB_DIR:-/tmp/opencode/cv-builder-public}"
STAGE_DIR=$(mktemp -d /tmp/opencode/cv-builder-stage.XXXXXX)
trap 'rm -rf "$STAGE_DIR"' EXIT

if [ -z "${PUBLIC_REPO_URL:-}" ]; then
    echo "Kullanım: PUBLIC_REPO_URL=<github-clone-url> ./tools/publish.sh"
    exit 1
fi

# --- 1) allow-list snapshot ---
FILELIST=(
    .env.example .gitignore .python-version uv.lock pyproject.toml
    README.md CHANGELOG.md CONTRIBUTING.md LICENSE Makefile config.toml
    doctor.py main.py run_daily.sh
    src/job_search.py src/cv_tailor.py src/pdf_generator.py
    src/tracker.py src/notifier.py src/status_logger.py
    webapp/web_app.py webapp/templates/login.html webapp/templates/dashboard.html
    webapp/static/css/styles.css webapp/static/js/main.js
    templates/base_cv.example.typ
    data/database/users.example.json
    tools/hash_users.py tools/load_config.py tools/publish.sh
)
cd "$BASE_DIR"
for f in "${FILELIST[@]}"; do
    [ -f "$f" ] || { echo "EKSİK dosya (allow-list): $f"; exit 1; }
done
printf '%s\n' "${FILELIST[@]}" | rsync -a --files-from=- . "$STAGE_DIR/"
echo "[snapshot] ${#FILELIST[@]} dosya stage'lendi."

# Inject data dosyalari her senaryoda orneklerle dolu gelsin:
mkdir -p "$STAGE_DIR/data"
cp "$STAGE_DIR/templates/base_cv.example.typ" "$STAGE_DIR/data/base_cv.typ"
echo '[]' > "$STAGE_DIR/data/blocked_companies.json"

# --- 2) kişisel-veri taraması ---
# Not: LICENSE + pyproject (yazar adi public), README (proje URL'leri) ve
# tools/publish.sh (kendi kalibri) kasıtlı olarak scan'e dahil degil.
HITS=$(grep -rInE '(tahakiziltepe|mtahakiziltepe|kiziltepe|tahakiziltepe@hotmail|\+90 ?\(?53[0-9]\)? ?[0-9]{3} ?[0-9]{3})' \
    --exclude=publish.sh --exclude=LICENSE --exclude=pyproject.toml --exclude=README.md \
    "$STAGE_DIR" 2>/dev/null | grep -v '^Binary' || true)
if [ -n "$HITS" ]; then
    echo "UYARI! Teyit edilmemis kişisel veri kalıntısı bulundu:"
    echo "$HITS" | head -20
    if [ "${PUBLISH_CONFIRM:-0}" != "1" ]; then
        echo "=> push iptal edildi. Kişisel veri yoksa PUBLISH_CONFIRM=1 ile onay ver."
        exit 1
    fi
fi

# --- 3) public clone + commit + push (DRY=1 burada durur) ---
if [ "${DRY:-0}" = "1" ]; then
    echo "[DRY] Push yapılmadı. Stage klasörü korundu: $STAGE_DIR"
    trap - EXIT
    exit 0
fi
if [ ! -d "$PUB_DIR/.git" ]; then
    git clone "$PUBLIC_REPO_URL" "$PUB_DIR"
fi
rsync -a --delete --exclude .git --exclude .env --exclude data/output "$STAGE_DIR/" "$PUB_DIR/"
cd "$PUB_DIR"
if git diff --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    echo "Değişiklik yok, push gerekmez."
    exit 0
fi
git add -A
EMPTY=$(git rev-list --count HEAD 2>/dev/null || echo 0)
if [ "$EMPTY" = "0" ]; then
    git commit -m "Initial public release (v1.0.0)"
else
    git commit -m "Sync from private working repo ($(date +'%Y-%m-%d'))"
fi
git push origin main
echo "Public depo güncellendi: $PUB_DIR"
