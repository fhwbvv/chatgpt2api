#!/bin/sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
VERSION=$(tr -d '[:space:]' < "${ROOT_DIR}/VERSION")
STAMP_FILE="${ROOT_DIR}/.venv/.chatgpt2api-version"
DEFAULT_PYTHON="python3.13"

if [ -n "${PYTHON_BIN:-}" ]; then
  PYTHON_CMD="${PYTHON_BIN}"
elif command -v "${DEFAULT_PYTHON}" >/dev/null 2>&1; then
  PYTHON_CMD="${DEFAULT_PYTHON}"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
else
  echo "Python 3.13 or newer is required."
  exit 1
fi

"${PYTHON_CMD}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 13) else 1)' || {
  echo "Python 3.13 or newer is required."
  exit 1
}

if [ ! -d "${ROOT_DIR}/.venv" ]; then
  "${PYTHON_CMD}" -m venv "${ROOT_DIR}/.venv"
fi

if [ ! -f "${STAMP_FILE}" ] || [ "$(cat "${STAMP_FILE}")" != "${VERSION}" ]; then
  "${ROOT_DIR}/.venv/bin/python" -m pip install --upgrade pip setuptools wheel
  "${ROOT_DIR}/.venv/bin/python" -m pip install -r "${ROOT_DIR}/requirements.txt"
  printf '%s' "${VERSION}" > "${STAMP_FILE}"
fi

exec "${ROOT_DIR}/.venv/bin/python" -m uvicorn main:app \
  --host "${HOST:-0.0.0.0}" \
  --port "${PORT:-8000}" \
  --access-log
