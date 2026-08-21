#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CREW_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="$CREW_DIR/output"

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

mkdir -p "$OUTPUT_DIR"

if command -v ocr >/dev/null 2>&1; then
  OCR=("ocr")
else
  OCR=("npx" "-y" "@alibaba-group/open-code-review")
fi

# 1. Run lizard on the whole repo and capture CSV
run_lizard \
  --csv \
  --output_file "$OUTPUT_DIR/lizard.csv" \
  --exclude "./tools/repo-cleanup-crew/*" \
  --exclude "./lizard.csv" \
  --exclude "./node_modules/*" \
  .

# 2. Produce the ranked manifest
python3 "$SCRIPT_DIR/manifest-pruner.py" \
  --lizard "$OUTPUT_DIR/lizard.csv" \
  --output "$OUTPUT_DIR/manifest.json" \
  --ocr-cmd "${OCR[*]}"

echo "Manifest written to $OUTPUT_DIR/manifest.json"
