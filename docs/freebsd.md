# FreeBSD Deployment

This repository publishes a FreeBSD deployment archive that tracks the upstream `basketikun/chatgpt2api` source tree and reuses the upstream `VERSION` file as the GitHub Release tag.

## Included Files

The release archive contains:

- Python application source code
- prebuilt static frontend files in `web_dist/`
- `requirements.txt` exported from `uv.lock`
- `scripts/start-freebsd.sh` for bootstrapping the runtime environment on FreeBSD

## Requirements

- `python3.13`
- `py313-pip`
- network access for the first dependency install

Example on FreeBSD:

```sh
pkg update
pkg install -y python3.13 py313-pip
```

## Start

```sh
tar -xzf chatgpt2api-freebsd-amd64-<version>.tar.gz
cd chatgpt2api-freebsd-amd64
chmod +x scripts/start-freebsd.sh
./scripts/start-freebsd.sh
```

Optional environment variables:

- `PYTHON_BIN`: custom Python interpreter path, default prefers `python3.13`
- `HOST`: bind address, default `0.0.0.0`
- `PORT`: listen port, default `8000`

The first start creates `.venv/`, installs Python dependencies from `requirements.txt`, and then runs `uvicorn`.
