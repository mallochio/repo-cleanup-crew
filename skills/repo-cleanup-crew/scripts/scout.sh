#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
REPO="${1:-$(pwd)}"
cd "$REPO"
REPO_CANONICAL="$(pwd -P)"
REPO_NAME="$(basename "$REPO_CANONICAL")"
OUT_DIR="/tmp/repo-cleanup-crew/$REPO_NAME"

mkdir -p "$OUT_DIR"

# ---------- lizard ----------
run_lizard() {
  if command -v uvx >/dev/null 2>&1; then
    local py_version
    py_version="$(python3 -c 'import platform; print(platform.python_version()[:3])' 2>/dev/null || echo '3.9')"
    UV_PYTHON="${UV_PYTHON:-$py_version}" uvx lizard "$@"
  elif command -v lizard >/dev/null 2>&1; then
    lizard "$@"
  elif command -v python3 >/dev/null 2>&1; then
    if python3 -c "import lizard" 2>/dev/null; then
      python3 -m lizard "$@"
    fi
  else
    echo "No lizard runner found." >&2
    exit 1
  fi
}

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
  . || true

# ---------- ruff (Python) ----------
run_ruff() {
  if command -v uvx >/dev/null 2>&1; then
    local py_version
    py_version="$(python3 -c 'import platform; print(platform.python_version()[:3])' 2>/dev/null || echo '3.9')"
    UV_PYTHON="${UV_PYTHON:-$py_version}" uvx ruff check . --config "$SKILL_DIR/rules/ruff.toml" --output-format json --no-cache
  elif command -v ruff >/dev/null 2>&1; then
    ruff check . --config "$SKILL_DIR/rules/ruff.toml" --output-format json --no-cache
  else
    echo "[]"
  fi
}

run_ruff > "$OUT_DIR/ruff.json" 2>/dev/null || true

# ---------- oxlint with anti-slop (JS/TS) ----------
OXLINT_DIR="/tmp/repo-cleanup-crew/.oxlint"
mkdir -p "$OXLINT_DIR"

if [ ! -d "$HOME/.agents/skills/install-anti-slop" ]; then
  npx skills add dmmulroy/anti-slop -g -y >/dev/null 2>&1 || true
fi

if [ -d "$HOME/.agents/skills/install-anti-slop/assets/anti-slop" ] && [ ! -d "$OXLINT_DIR/anti-slop" ]; then
  cp -r "$HOME/.agents/skills/install-anti-slop/assets/anti-slop" "$OXLINT_DIR/anti-slop"
fi

if [ -d "$OXLINT_DIR/anti-slop" ] && [ ! -d "$OXLINT_DIR/node_modules" ]; then
  (cd "$OXLINT_DIR" && npm install oxlint @oxlint/plugins --no-save --no-audit --no-fund) >/dev/null 2>&1
fi

cat > "$OXLINT_DIR/oxlint.config.json" <<'EOF'
{
  "ignorePatterns": [
    ".agents/**",
    ".cache/**",
    "coverage/**",
    "dist/**",
    "node_modules/**",
    "tools/repo-cleanup-crew/**",
    "tools/oxlint/**"
  ],
  "jsPlugins": [
    { "name": "anti-slop", "specifier": "./anti-slop/index.ts" }
  ],
  "rules": {
    "anti-slop/no-chained-type-assertions": "error",
    "anti-slop/no-conditional-empty-object-spread": "error",
    "anti-slop/no-known-value-widening": "error",
    "anti-slop/no-module-mocking": "error",
    "anti-slop/no-object-parameters": "error",
    "anti-slop/no-reflect-apply": "error",
    "anti-slop/no-reflect-get": "error",
    "anti-slop/no-runtime-typeof": "error",
    "anti-slop/no-shape-in-symbol-names": "error",
    "anti-slop/no-unknown-parameters": "error",
    "anti-slop/no-unknown-returns": "error",
    "anti-slop/no-unknown-type-aliases": "error",
    "anti-slop/no-unsafe-dictionary-type": "error",
    "anti-slop/no-widen-then-assert": "error",
    "anti-slop/require-safety-comment-for-type-assertion": "error"
  }
}
EOF

if [ -x "$OXLINT_DIR/node_modules/.bin/oxlint" ]; then
  "$OXLINT_DIR/node_modules/.bin/oxlint" \
    --config "$OXLINT_DIR/oxlint.config.json" \
    --format json . > "$OUT_DIR/oxlint.json" 2>/dev/null || true
else
  echo '{"diagnostics":[]}' > "$OUT_DIR/oxlint.json"
fi

# ---------- ocr ----------
if command -v ocr >/dev/null 2>&1; then
  OCR=("ocr")
else
  OCR=("npx" "-y" "@alibaba-group/open-code-review")
fi

# ---------- manifest ----------
python3 "$SCRIPT_DIR/manifest-pruner.py" \
  --lizard "$OUT_DIR/lizard.csv" \
  --oxlint "$OUT_DIR/oxlint.json" \
  --ruff "$OUT_DIR/ruff.json" \
  --output "$OUT_DIR/manifest.json" \
  --ocr-cmd "${OCR[*]}" \
  --repo "$REPO_CANONICAL"

# ---------- present ----------
python3 "$SCRIPT_DIR/present.py" \
  --manifest "$OUT_DIR/manifest.json" \
  --output "$OUT_DIR/analysis.md"

echo "---"
echo "Manifest: $OUT_DIR/manifest.json"
echo "Analysis: $OUT_DIR/analysis.md"
