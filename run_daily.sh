#!/bin/bash

# CV Builder gunluk turu: config.toml'daki sorgu x lokasyon kombinasyonlari
# icin main.py calistirir. Ayarlar: config.toml; AUTO_PUSH .env'den okunur.

set -u

# Ensure dependencies are installed
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Installing dependencies with uv..."
    uv sync || { echo "uv sync FAILED. Aborting."; exit 1; }
fi

# Config yukle (config.toml; yoksa dahili varsayilanlar)
if ! OUT="$(uv run python tools/load_config.py 2>&1)"; then
    echo "config yuklemesi BAŞARISIZ:"
    echo "$OUT"
    exit 1
fi
eval "$OUT"
export AUTO_PUSH

echo "Starting Comprehensive Daily Job Search..."
date
echo "Configuration: Limit=$LIMIT per query, Hours=$HOURS"

# Double Loop: Queries x Locations
for query in "${QUERIES[@]}"; do
    for location in "${LOCATIONS[@]}"; do
        echo "---------------------------------------------------"
        echo "Searching: '$query' in '$location'"
        uv run python main.py --query "$query" --location "$location" --limit $LIMIT --hours $HOURS
        # Small sleep to be polite between quick bursts
        sleep 10
    done
done

echo "---------------------------------------------------"
echo "Daily Job Search Completed."

# Otomatik git commit + push: default kapali (public depolar icin guvenli),
# private jurnal icin .env'de AUTO_PUSH=1 yazilarak aktiflestirilir.
if [ "$AUTO_PUSH" != "true" ]; then
    echo "AUTO_PUSH kapalı, git senkronunu atlıyorum."
    exit 0
fi

echo "Committing data/ folder to Git..."

# Load .env variables if present
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

git add data/
if ! git diff-index --quiet HEAD; then
    git commit -m "Auto-update: Daily job search results $(date +'%Y-%m-%d')"

    if [ -n "${GITHUB_TOKEN:-}" ]; then
        ORIGIN_URL=$(git config --get remote.origin.url)
        # Parse standard Git SSH/HTTPS URL into 'domain.com/user/repo'
        CLEAN_URL=$(echo $ORIGIN_URL | sed -e 's/^[a-zA-Z]*:\/\///' -e 's/.*@//' -e 's/:/\//')

        echo "Pushing changes using GITHUB_TOKEN..."
        # Push using token, redirect output to hide token from logs
        if git push --quiet "https://${GITHUB_TOKEN}@${CLEAN_URL}" HEAD > /dev/null 2>&1; then
            echo "Changes pushed successfully."
        else
            echo "Failed to push using token; falling back to normal git push..."
            if git push origin HEAD > /dev/null 2>&1; then
                echo "Fallback push succeeded (credential store)."
            else
                echo "Failed to push using token AND fallback ALSO failed."
            fi
        fi
    else
        git push origin HEAD && echo "Changes pushed successfully." || echo "Failed to push."
    fi
else
    echo "No changes found in data/, nothing to commit."
fi
