#!/usr/bin/env bash
#
#  run_tests.sh
#  CryptoTracker
#
#  Created by Cascade on Dec 14, 2025.
#  Copyright © 2025 CryptoTracker. All rights reserved.
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$ROOT_DIR/.venv"
REQUIREMENTS_FILE="$ROOT_DIR/requirements.txt"
COVERAGE_HTML_DIR="$ROOT_DIR/htmlcov"

if [ ! -d "$VENV_PATH" ]; then
  python3 -m venv "$VENV_PATH"
fi

# shellcheck disable=SC1090
source "$VENV_PATH/bin/activate"

python -m pip install --upgrade pip >/dev/null
python -m pip install -r "$REQUIREMENTS_FILE"
python -m playwright install chromium >/dev/null

pytest --maxfail=1 --disable-warnings --cov=app --cov=tests --cov-report=term-missing --cov-report=html "$@"

echo
echo "Cobertura HTML disponible en: $COVERAGE_HTML_DIR/index.html"
