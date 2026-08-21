#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${1:-$(pwd)}"
REPO_NAME="$(basename "$REPO")"
OUT_DIR="/tmp/repo-cleanup-crew/$REPO_NAME"

cd "$REPO"

run_lizard() {
  if command -v lizard >/dev/null 2>&1; then
    lizard "$@"
  elif command -v uvx >/dev/null 2>&1; then
    local py_version
    py_version="$(python3 -c 'import platform; print(platform.python_version()[:3])' 2>/dev/null || echo '3.9')"
    UV_PYTHON="${UV_PYTHON:-$py_version}" uvx lizard "$@"
  elif command -v python3 >/dev/null 2>&1; then
    if python3 -c "import lizard" 2>/dev/null; then
      python3 -m lizard "$@"
    fi
  else
    echo "No lizard runner found. Install lizard, uvx, or Python with lizard." >&2
    exit 1
  fi
}

if command -v ocr >/dev/null 2>&1; then
  OCR=("ocr")
else
  OCR=("npx" "-y" "@alibaba-group/open-code-review")
fi

mkdir -p "$OUT_DIR"

# 1. Run lizard on the repo and capture CSV outside the repo
run_lizard \
  --csv \
  --output_file "$OUT_DIR/lizard.csv" \
  --exclude "./.agents/*" \
  --exclude "./.cache/*" \
  --exclude "./coverage/*" \
  --exclude "./dist/*" \
  --exclude "./tools/repo-cleanup-crew/*" \
  --exclude "./lizard.csv" \
  --exclude "./node_modules/*" \
  .

# 2. Produce the ranked manifest in /tmp
python3 "$SCRIPT_DIR/manifest-pruner.py" \
  --lizard "$OUT_DIR/lizard.csv" \
  --output "$OUT_DIR/manifest.json" \
  --ocr-cmd "${OCR[*]}"

# 3. Present a neat analysis
python3 "$SCRIPT_DIR/present.py" \
  --manifest "$OUT_DIR/manifest.json" \
  --output "$OUT_DIR/analysis.md"

echo "---"
echo "Manifest: $OUT_DIR/manifest.json"
echo "Analysis: $OUT_DIR/analysis.md"
