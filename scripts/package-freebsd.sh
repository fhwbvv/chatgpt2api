#!/bin/sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
DIST_DIR="${ROOT_DIR}/dist"
BUILD_DIR="${ROOT_DIR}/build"
WEB_DIR="${ROOT_DIR}/web"
APP_NAME="${APP_NAME:-chatgpt2api}"
PACKAGE_BASENAME="${PACKAGE_BASENAME:-chatgpt2api-freebsd-amd64}"
VERSION="${VERSION:-$(tr -d '[:space:]' < "${ROOT_DIR}/VERSION")}"
ARCHIVE_PATH="${DIST_DIR}/${PACKAGE_BASENAME}-${VERSION}.tar.gz"
CHECKSUM_PATH="${ARCHIVE_PATH}.sha256"
PACKAGE_DIR="${DIST_DIR}/${PACKAGE_BASENAME}"
PYTHON_BIN="${PYTHON_BIN:-python3.13}"

echo "[1/6] Preparing static frontend"
if [ -d "${WEB_DIR}/out" ]; then
  echo "Using prebuilt web/out assets"
else
  cd "${WEB_DIR}"
  npm install
  NEXT_PUBLIC_APP_VERSION="${VERSION}" npm run build
fi

echo "[2/6] Preparing Python build environment"
cd "${ROOT_DIR}"
rm -rf .venv-freebsd-build "${BUILD_DIR}" "${PACKAGE_DIR}"
"${PYTHON_BIN}" -m venv .venv-freebsd-build
.venv-freebsd-build/bin/pip install --upgrade pip setuptools wheel
.venv-freebsd-build/bin/pip install -r requirements-freebsd.txt pyinstaller

echo "[3/6] Building FreeBSD executable bundle"
.venv-freebsd-build/bin/pyinstaller \
  --clean \
  --noconfirm \
  --name "${APP_NAME}" \
  --onedir \
  --contents-directory _internal \
  --add-data "web/out:web_dist" \
  --add-data "VERSION:." \
  main.py

echo "[4/6] Preparing release package"
mkdir -p "${PACKAGE_DIR}/docs" "${PACKAGE_DIR}/data"
cp -R "${DIST_DIR}/${APP_NAME}/." "${PACKAGE_DIR}/"
cp VERSION "${PACKAGE_DIR}/VERSION"
cp README.md "${PACKAGE_DIR}/README.md"
cp LICENSE "${PACKAGE_DIR}/LICENSE"
cp docs/freebsd.md "${PACKAGE_DIR}/docs/freebsd.md"
cp config.json "${PACKAGE_DIR}/config.json.example"

echo "[5/6] Creating archive"
tar -C "${DIST_DIR}" -czf "${ARCHIVE_PATH}" "${PACKAGE_BASENAME}"

echo "[6/6] Writing checksum"
(
  cd "${DIST_DIR}"
  sha256 -q "$(basename "${ARCHIVE_PATH}")" > "$(basename "${CHECKSUM_PATH}")"
)

echo "Archive: ${ARCHIVE_PATH}"
echo "Checksum: ${CHECKSUM_PATH}"
