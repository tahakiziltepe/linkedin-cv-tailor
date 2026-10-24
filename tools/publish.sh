#!/bin/bash
# Private -> public hash snapshot ('snapshot sync'; git geçmişi taşınmaz!)
# 1. rsync ile allow-list dosyaları stage'lenir
# 2. kişisel-veri taraması (temiz değilse durur)
# 3. public clone'da commit + push
# NOT: Bu araç private branch'i push ETMEZ. Yayın ile yedekleme ayrı işlerdir;
# geliştirme commit'leri ayrıca `git push origin main` ile yedeklenmelidir.
# Kullanim: PUBLIC_REPO_URL=https://github.com/me/repo ./tools/publish.sh
#           PUBLISH_CONFIRM=1   (tarama uyarilarini gecmek icin)
#           PUBLISH_SKIP_GUARD=1 (yayin kilidini atlamak icin - acil durum)
#           PUBLISH_SKIP_TESTS=1 (test kapisini atlamak icin - sadece testler icin)
#           PUB_DIR=...         (varsayilan: /tmp/opencode/cv-builder-public)
#           STAGE_ROOT=...      (varsayilan: /tmp/opencode)
set -euo pipefail

BASE_DIR=$(cd "$(dirname "$0")/.." && pwd)
PUB_DIR="${PUB_DIR:-/tmp/opencode/cv-builder-public}"
STAGE_ROOT="${STAGE_ROOT:-/tmp/opencode}"
mkdir -p "$STAGE_ROOT"
STAGE_DIR=$(mktemp -d "$STAGE_ROOT/cv-builder-stage.XXXXXX")
trap 'rm -rf "$STAGE_DIR"' EXIT

if [ -z "${PUBLIC_REPO_URL:-}" ]; then
    echo "Kullanım: PUBLIC_REPO_URL=<github-clone-url> ./tools/publish.sh"
    exit 1
fi

# --- 1) allow-list snapshot ---
FILELIST=(
    .env.example .gitignore .python-version uv.lock pyproject.toml
    README.md CHANGELOG.md CONTRIBUTING.md CODE_OF_CONDUCT.md SECURITY.md
    LICENSE Makefile config.toml
    .github
    doctor.py main.py run_daily.sh
    src/job_search.py src/cv_tailor.py src/pdf_generator.py
    src/tracker.py src/notifier.py src/status_logger.py src/prompts.py
    webapp/web_app.py webapp/templates/login.html webapp/templates/dashboard.html
    webapp/templates/prompts.html
    webapp/static/css/styles.css webapp/static/js/main.js
    templates/base_cv.example.typ
    data/database/users.example.json
    prompts/suitability.md prompts/tailor_cv.md prompts/fix_typst.md
    tools/hash_users.py tools/load_config.py tools/publish.sh
    tests
)
cd "$BASE_DIR"

# --- 0) yayın güvenlik kilidi ---
# Yalnızca remote ile eşitlenmiş, temiz bir private main'den yayın yapılır.
if [ "${PUBLISH_SKIP_GUARD:-0}" = "1" ]; then
    echo "[UYARI] PUBLISH_SKIP_GUARD=1: yayın kilidi atlandı."
else
    CURRENT_BRANCH=$(git branch --show-current)
    if [ "$CURRENT_BRANCH" != "main" ]; then
        echo "YAYIN ENGELLENDİ: aktif branch '$CURRENT_BRANCH'; sadece 'main'den yayın yapılır."
        echo "  Çözüm: git checkout main"
        exit 1
    fi

    if ! git fetch -q origin main; then
        echo "YAYIN ENGELLENDİ: 'origin main' güncellenemedi (ağ/remote hatası)."
        exit 1
    fi
    LOCAL_SHA=$(git rev-parse HEAD)
    REMOTE_SHA=$(git rev-parse origin/main)
    if [ "$LOCAL_SHA" != "$REMOTE_SHA" ]; then
        echo "YAYIN ENGELLENDİ: lokal main ile origin/main aynı değil."
        echo "  lokal : $LOCAL_SHA"
        echo "  remote: $REMOTE_SHA"
        echo "  Çözüm: git push origin main   (veya git pull --ff-only)"
        exit 1
    fi

    DIRTY=$(git diff --name-only HEAD -- "${FILELIST[@]}" || true)
    if [ -n "$DIRTY" ]; then
        echo "YAYIN ENGELLENDİ: yayınlanacak dosyalarda commit edilmemiş değişiklik var:"
        echo "$DIRTY" | sed 's/^/  - /'
        echo "  Çözüm: değişiklikleri commit'leyip pushla."
        exit 1
    fi

    UNTRACKED=()
    for f in "${FILELIST[@]}"; do
        if ! git ls-files --error-unmatch "$f" >/dev/null 2>&1; then
            UNTRACKED+=("$f")
        fi
    done
    if [ ${#UNTRACKED[@]} -gt 0 ]; then
        echo "YAYIN ENGELLENDİ: şu allow-list dosyaları git'te takipli değil:"
        printf '  - %s\n' "${UNTRACKED[@]}"
        echo "  Çözüm: git add <dosya> && git commit"
        exit 1
    fi

    # Test kapisi: yayin oncesi tum offline testler gecmeli.
    if [ "${PUBLISH_SKIP_TESTS:-0}" = "1" ]; then
        echo "[UYARI] PUBLISH_SKIP_TESTS=1: test kapisi atlandi."
    else
        echo "[test] make test (offline)"
        if ! uv run pytest -q -m "not live"; then
            echo "YAYIN ENGELLENDİ: testler geçmedi. Önce 'make test' çalıştır."
            exit 1
        fi
    fi
    echo "[kilit] main + senkron + temiz + testler: yayına hazır."
fi

for f in "${FILELIST[@]}"; do
    [ -f "$f" ] || [ -d "$f" ] || { echo "EKSİK dosya (allow-list): $f"; exit 1; }
done
printf '%s\n' "${FILELIST[@]}" | rsync -a -r --exclude='__pycache__' --exclude='.pytest_cache' --exclude='publish.yml' --files-from=- . "$STAGE_DIR/"
echo "[snapshot] ${#FILELIST[@]} dosya stage'lendi."

# Private CI workflow dosyasını (publish.yml) public repoya aktarma
rm -f "$STAGE_DIR/.github/workflows/publish.yml"

# Inject data dosyalari her senaryoda orneklerle dolu gelsin:
mkdir -p "$STAGE_DIR/data"
cp "$STAGE_DIR/templates/base_cv.example.typ" "$STAGE_DIR/data/base_cv.typ"
echo '[]' > "$STAGE_DIR/data/blocked_companies.json"

# --- 2) kişisel-veri taraması ---
# Not: LICENSE + pyproject (yazar adi public), README (proje URL'leri),
# .github (repo/issue URL'leri), SECURITY.md + CODE_OF_CONDUCT.md (bildirim
# adresi) ve tools/publish.sh (kendi kalibri) kasıtlı olarak scan'e dahil degil.
HITS=$(grep -rInE '(tahakiziltepe|mtahakiziltepe|kiziltepe|tahakiziltepe@hotmail|\+90 ?\(?53[0-9]\)? ?[0-9]{3} ?[0-9]{3})' \
    --exclude=publish.sh --exclude=LICENSE --exclude=pyproject.toml --exclude=README.md \
    --exclude=SECURITY.md --exclude=CODE_OF_CONDUCT.md --exclude-dir=.github \
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
    mkdir -p "$(dirname "$PUB_DIR")"
    git clone "$PUBLIC_REPO_URL" "$PUB_DIR"
fi

# Bos public repo: ilk commit'in 'main' uzerine gitmesini garantile.
if ! git -C "$PUB_DIR" rev-parse --verify -q HEAD >/dev/null; then
    git -C "$PUB_DIR" checkout -q -B main
fi

# Public'te lokal kopyada olmayan commit varsa (orn. merge edilmis bir katki
# PR'i) sessizce uzerine yazma: once private main'e alinmasi gerekir.
if git -C "$PUB_DIR" rev-parse --verify -q HEAD >/dev/null; then
    if git -C "$PUB_DIR" fetch -q origin main 2>/dev/null; then
        BEHIND=$(git -C "$PUB_DIR" rev-list --count HEAD..origin/main)
        if [ "$BEHIND" != "0" ]; then
            echo "YAYIN ENGELLENDİ: public repo'da lokal kopyada olmayan $BEHIND commit var."
            echo "  Bu genelde merge edilmiş bir katkı PR'ı demektir; rsync onu geri alırdı."
            echo "  Çözüm: değişikliği önce private main'e al, sonra:"
            echo "    git -C \"$PUB_DIR\" pull --ff-only"
            echo "  ve yayını tekrar çalıştır."
            exit 1
        fi
    fi
fi

rsync -a --delete --exclude .git --exclude .env --exclude data/output --exclude publish.yml "$STAGE_DIR/" "$PUB_DIR/"
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
