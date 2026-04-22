# FreeBSD Deployment

This release is intended to be a real FreeBSD application bundle built inside a FreeBSD VM. To make FreeBSD and serv00 deployment possible, the project now falls back to a standard `requests` session when `curl-cffi` is unavailable.

## Included Files

The archive contains:

- `chatgpt2api`: FreeBSD executable entrypoint
- `_internal/`: bundled Python runtime and dependencies
- `web_dist/`: prebuilt static frontend files
- `config.json.example`: sample configuration
- `docs/freebsd.md`: deployment notes

## Requirements

- FreeBSD amd64
- one available TCP port

No separate Python installation is required to run the packaged build.

If you deploy from the source tree on serv00 instead of using a release archive, create a virtual environment and install:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-freebsd.txt
```

For serv00 `Website type = Python`, use Passenger instead of a manual port. The project root should contain `passenger_wsgi.py`, and this repository now includes that file. In the panel, point `Python binary` to your virtualenv interpreter.

## Configure

Copy the example configuration and set your own auth key:

```sh
cp config.json.example config.json
```

Example:

```json
{
  "auth-key": "replace-with-your-own-secret",
  "refresh_account_interval_minute": 60,
  "host": "127.0.0.1",
  "port": 18080
}
```

You can also override host and port via environment variables:

- `HOST`
- `PORT`
- `CHATGPT2API_AUTH_KEY`

## Start

```sh
tar -xzf chatgpt2api-freebsd-amd64-<version>.tar.gz
cd chatgpt2api-freebsd-amd64
chmod +x ./chatgpt2api
./chatgpt2api
```

For serv00, bind to localhost and reverse proxy the reserved port from your domain:

```sh
HOST=127.0.0.1 PORT=18080 ./chatgpt2api
```
