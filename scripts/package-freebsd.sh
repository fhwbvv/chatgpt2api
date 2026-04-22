#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_DIR="${ROOT_DIR}/web"
DIST_DIR="${ROOT_DIR}/dist"
VERSION="${VERSION:-$(tr -d '[:space:]' < "${ROOT_DIR}/VERSION")}"
PACKAGE_BASENAME="${PACKAGE_BASENAME:-chatgpt2api-freebsd-amd64}"
STAGE_DIR="${DIST_DIR}/${PACKAGE_BASENAME}"
ARCHIVE_PATH="${DIST_DIR}/${PACKAGE_BASENAME}-${VERSION}.tar.gz"
CHECKSUM_PATH="${ARCHIVE_PATH}.sha256"

echo "[1/5] Building static frontend"
cd "${WEB_DIR}"
npm install
NEXT_PUBLIC_APP_VERSION="${VERSION}" npm run build

echo "[2/5] Exporting Python dependencies"
cd "${ROOT_DIR}"
mkdir -p "${DIST_DIR}"
uv export --frozen --no-dev --format requirements-txt --no-hashes -o "${DIST_DIR}/requirements.txt"

echo "[3/5] Preparing release payload"
rm -rf "${STAGE_DIR}"
mkdir -p "${STAGE_DIR}/docs" "${STAGE_DIR}/scripts"
cp main.py "${STAGE_DIR}/"
cp pyproject.toml "${STAGE_DIR}/"
cp uv.lock "${STAGE_DIR}/"
cp VERSION "${STAGE_DIR}/"
cp LICENSE "${STAGE_DIR}/"
cp README.md "${STAGE_DIR}/"
cp "${DIST_DIR}/requirements.txt" "${STAGE_DIR}/requirements.txt"
cp docs/freebsd.md "${STAGE_DIR}/docs/freebsd.md"
cp scripts/start-freebsd.sh "${STAGE_DIR}/scripts/start-freebsd.sh"
cp -R services "${STAGE_DIR}/services"
cp -R web/out "${STAGE_DIR}/web_dist"

if [[ -f config.json ]]; then
  cp config.json "${STAGE_DIR}/config.json"
fi

echo "[4/5] Creating archive"
tar -C "${DIST_DIR}" -czf "${ARCHIVE_PATH}" "${PACKAGE_BASENAME}"

echo "[5/5] Writing checksum"
(
  cd "${DIST_DIR}"
  sha256sum "$(basename "${ARCHIVE_PATH}")" | tee "$(basename "${CHECKSUM_PATH}")"
)

echo "Archive: ${ARCHIVE_PATH}"
echo "Checksum: ${CHECKSUM_PATH}"
