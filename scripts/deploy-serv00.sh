#!/bin/sh

set -eu

# serv00 source deployment helper for Passenger-based Python websites.
# Usage:
#   1. Upload this repository to the server.
#   2. Edit the variables below.
#   3. Run: sh scripts/deploy-serv00.sh

LOGIN="${LOGIN:-REPLACE_WITH_SERV00_LOGIN}"
DOMAIN="${DOMAIN:-REPLACE_WITH_DOMAIN}"
AUTH_KEY="${AUTH_KEY:-REPLACE_WITH_LONG_RANDOM_SECRET}"

PYTHON_BIN="${PYTHON_BIN:-/usr/local/bin/python3.12}"
APP_DIR="${APP_DIR:-/usr/home/${LOGIN}/domains/${DOMAIN}/public_python}"
VENV_DIR="${VENV_DIR:-/usr/home/${LOGIN}/.virtualenvs/chatgpt2api-312}"
PROFILE_FILE="${PROFILE_FILE:-/usr/home/${LOGIN}/.bash_profile}"

if [ "${LOGIN}" = "REPLACE_WITH_SERV00_LOGIN" ] || [ "${DOMAIN}" = "REPLACE_WITH_DOMAIN" ] || [ "${AUTH_KEY}" = "REPLACE_WITH_LONG_RANDOM_SECRET" ]; then
  echo "Please set LOGIN, DOMAIN, and AUTH_KEY before running this script."
  echo "Example:"
  echo "  LOGIN=yourlogin DOMAIN=api.example.com AUTH_KEY=your-secret sh scripts/deploy-serv00.sh"
  exit 1
fi

if [ ! -d "${APP_DIR}" ]; then
  echo "Application directory not found: ${APP_DIR}"
  echo "Upload the repository to the serv00 Python website root first."
  exit 1
fi

cd "${APP_DIR}"

mkdir -p "$(dirname "${VENV_DIR}")"

if [ ! -x "${VENV_DIR}/bin/python" ]; then
  echo "[1/7] Creating virtualenv at ${VENV_DIR}"
  virtualenv "${VENV_DIR}" -p "${PYTHON_BIN}"
else
  echo "[1/7] Reusing virtualenv at ${VENV_DIR}"
fi

# shellcheck disable=SC1090
. "${VENV_DIR}/bin/activate"

echo "[2/7] Upgrading packaging tools"
pip install --upgrade pip setuptools wheel

echo "[3/7] Installing Python dependencies"
export CFLAGS="${CFLAGS:--I/usr/local/include}"
export CXXFLAGS="${CXXFLAGS:--I/usr/local/include}"
export CC="${CC:-gcc}"
export CXX="${CXX:-g++}"
export MAX_CONCURRENCY="${MAX_CONCURRENCY:-1}"
export CPUCOUNT="${CPUCOUNT:-1}"
export MAKEFLAGS="${MAKEFLAGS:--j1}"
export CMAKE_BUILD_PARALLEL_LEVEL="${CMAKE_BUILD_PARALLEL_LEVEL:-1}"
pip install -r requirements-freebsd.txt

echo "[4/7] Preparing runtime files"
mkdir -p "${APP_DIR}/data" "${APP_DIR}/public"
if [ ! -f "${APP_DIR}/config.json" ] && [ -f "${APP_DIR}/config.json.example" ]; then
  cp "${APP_DIR}/config.json.example" "${APP_DIR}/config.json"
fi

echo "[5/7] Writing Passenger environment block to ${PROFILE_FILE}"
mkdir -p "$(dirname "${PROFILE_FILE}")"
touch "${PROFILE_FILE}"

tmp_file="$(mktemp)"
awk '
  BEGIN { skip = 0 }
  /^# >>> chatgpt2api serv00 >>>$/ { skip = 1; next }
  /^# <<< chatgpt2api serv00 <<<$/{ skip = 0; next }
  skip == 0 { print }
' "${PROFILE_FILE}" > "${tmp_file}"
mv "${tmp_file}" "${PROFILE_FILE}"

cat >> "${PROFILE_FILE}" <<EOF
# >>> chatgpt2api serv00 >>>
export CHATGPT2API_AUTH_KEY="${AUTH_KEY}"
export STORAGE_BACKEND="json"
# <<< chatgpt2api serv00 <<<
EOF

echo "[6/7] Restarting Passenger"
devil www "${DOMAIN}" restart
devil www options "${DOMAIN}" processes 1

echo "[7/7] Done"
echo "Python binary:"
echo "  ${VENV_DIR}/bin/python"
echo
echo "Next checks:"
echo "  tail -n 200 /usr/home/${LOGIN}/domains/${DOMAIN}/logs/error.log"
echo "  curl -I https://${DOMAIN}/health"
echo "  curl https://${DOMAIN}/version"

