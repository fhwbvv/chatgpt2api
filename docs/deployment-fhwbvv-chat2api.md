# Deployment Guide For `fhwbvv/chatgpt2api`

This document describes how to deploy the current fork:

- Repository: `https://github.com/fhwbvv/chatgpt2api`

It focuses on source-tree deployment and especially `serv00`, which is the environment used in the recent setup.

## What Is Different In This Fork

Compared with a plain upstream checkout, this fork currently includes deployment-oriented changes that matter for serv00 and FreeBSD-style environments:

- `passenger_wsgi.py` is present for serv00 Python website mode
- frontend build uses Webpack instead of Turbopack
- source deployments can serve frontend assets directly from `web/out`
- image frontend flow supports URL-based image delivery

## Deployment Modes

There are two practical ways to run this fork:

1. Source deployment on serv00 using `Website type = Python`
2. Running the packaged FreeBSD bundle or other self-hosted builds

This document mainly covers the first one.

## serv00 Deployment

### 1. Panel setup

In the serv00 panel:

- go to `WWW websites`
- add or edit the website
- use:
  - `Website type: Python`
  - `Environment: Production`

Do not guess the interpreter path. Use the virtualenv interpreter created below.

### 2. Code location

Example project path used in the recent deployment:

```sh
/usr/home/u99/domains/chatgpt2api.u99.serv00.net/public_python
```

Clone the fork into that directory:

```sh
devil binexec on
cd /usr/home/u99/domains/chatgpt2api.u99.serv00.net
git clone https://github.com/fhwbvv/chatgpt2api.git public_python
cd public_python
```

If the code is already deployed, use `git pull` instead of recloning.

### 3. Python virtual environment

The current serv00 deployment used a dedicated virtualenv outside the project tree:

```sh
mkdir -p /usr/home/u99/.virtualenvs
cd /usr/home/u99/.virtualenvs
virtualenv chat2api -p /usr/local/bin/python3.12
```

Expected interpreter:

```sh
/usr/home/u99/.virtualenvs/chat2api/bin/python
```

Activate it when updating dependencies:

```sh
source /usr/home/u99/.virtualenvs/chat2api/bin/activate
```

### 4. Install backend dependencies

From the virtualenv:

```sh
source /usr/home/u99/.virtualenvs/chat2api/bin/activate
pip install -r /usr/home/u99/domains/chatgpt2api.u99.serv00.net/public_python/requirements-freebsd.txt
```

### 5. Configure auth key

You can use either environment variables or `config.json`.

Example environment setup:

```sh
echo "export CHATGPT2API_AUTH_KEY='your-secret-key'" >> /usr/home/u99/.bash_profile
. /usr/home/u99/.bash_profile
```

### 6. Passenger Python binary

Back in the serv00 website configuration, set `Python binary` to:

```sh
/usr/home/u99/.virtualenvs/chat2api/bin/python
```

This project includes:

- `passenger_wsgi.py`

Passenger will use that file as the entrypoint.

### 7. Build the frontend

This fork serves the frontend from the source tree when `web/out` exists, so the frontend must be built after pulling updates.

Run:

```sh
cd /usr/home/u99/domains/chatgpt2api.u99.serv00.net/public_python/web
npm install
NEXT_PUBLIC_APP_VERSION="$(tr -d '[:space:]' < ../VERSION)" npm run build
```

Important:

- the current build script already uses `next build --webpack`
- this is required on `freebsd/x64`
- do not switch it back to plain `next build` unless platform support changes

### 8. Restart the site

```sh
cd /usr/home/u99/domains/chatgpt2api.u99.serv00.net/public_python
devil www restart chatgpt2api.u99.serv00.net
```

### 9. Smoke checks

Check backend:

```sh
curl https://chatgpt2api.u99.serv00.net/version
```

Check frontend:

- `https://chatgpt2api.u99.serv00.net/image`
- `https://chatgpt2api.u99.serv00.net/settings`

## serv00 Update Procedure

For an existing deployment, the normal update flow is:

```sh
cd /usr/home/u99/domains/chatgpt2api.u99.serv00.net/public_python
git pull origin main

source /usr/home/u99/.virtualenvs/chat2api/bin/activate
pip install -r requirements-freebsd.txt

cd web
npm install
NEXT_PUBLIC_APP_VERSION="$(tr -d '[:space:]' < ../VERSION)" npm run build

cd ..
devil www restart chatgpt2api.u99.serv00.net
```

## How Frontend Hosting Works In This Fork

The backend now resolves frontend assets in this order:

1. `web_dist`
2. `web/out`

This means:

- packaged FreeBSD releases still work with bundled `web_dist`
- source deployments can work directly from `web/out`

No extra copy step is required during normal source deployment.

## Image Frontend Notes

The image page now prefers URL-based image delivery:

- frontend requests `response_format: "url"`
- generated files are stored under `data/generated-images`
- the backend exposes:
  - `GET /v1/images/files/{image_name}`

This avoids large terminal output and oversized browser-stored Base64 history for the normal UI flow.

## Known Gaps

At the time of writing:

- this fork is not fully synced with upstream `basketikun/chatgpt2api`
- upstream has newer changes for:
  - image frontend
  - settings page
  - proxy/settings/sub2api integration

If you want the fork UI to match upstream more closely, plan a selective sync or merge for those areas.

## Troubleshooting

### Build fails on FreeBSD mentioning Turbopack

Cause:

- platform does not support Turbopack native bindings

Expected fix in this fork:

- `web/package.json` uses:

```json
"build": "next build --webpack"
```

### Frontend not visible after build

Check:

```sh
ls -l /usr/home/u99/domains/chatgpt2api.u99.serv00.net/public_python/web/out
```

Then restart the site:

```sh
devil www restart chatgpt2api.u99.serv00.net
```

### Passenger startup issues

Check log:

```sh
tail -n 100 /usr/home/u99/domains/chatgpt2api.u99.serv00.net/logs/error.log
```

### Wrong Python environment

If `.venv/bin/activate` does not exist, that does not necessarily mean deployment is broken. The current serv00 setup may be using:

```sh
/usr/home/u99/.virtualenvs/chat2api/bin/python
```

Confirm the actual interpreter configured in the serv00 panel before changing environments or deleting any virtualenv directory.
