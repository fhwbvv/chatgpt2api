from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, cast
import time

from services.paths import get_base_dir
from services.storage.factory import create_storage_backend

BASE_DIR = get_base_dir()
DATA_DIR = BASE_DIR / "data"
CONFIG_FILE = BASE_DIR / "config.json"
VERSION_FILE = BASE_DIR / "VERSION"
BACKUP_STATE_FILE = DATA_DIR / "backup_state.json"


def _readable_json_file(path: Path, *, name: str) -> Path | None:
    if not path.exists():
        return None
    if path.is_dir():
        print(
            f"Warning: {name} at '{path}' is a directory, ignoring it and falling back to other configuration sources.",
            file=sys.stderr,
        )
        return None
    return path


def _load_json_object(path: Path, *, name: str) -> dict[str, object]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError(f"{name} must be a JSON object")
    return loaded


def _deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in updates.items():
        current = result.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            result[key] = _deep_merge(current, value)
        else:
            result[key] = value
    return result


def _read_version() -> str:
    try:
        version = VERSION_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return "0.0.0"
    return version or "0.0.0"


def load_backup_state() -> dict[str, object]:
    if not BACKUP_STATE_FILE.exists():
        return {
            "last_started_at": None,
            "last_finished_at": None,
            "last_status": "idle",
            "last_error": None,
            "last_object_key": None,
        }
    try:
        loaded = json.loads(BACKUP_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {
            "last_started_at": None,
            "last_finished_at": None,
            "last_status": "idle",
            "last_error": None,
            "last_object_key": None,
        }
    return loaded if isinstance(loaded, dict) else {}


def save_backup_state(state: dict[str, object]) -> None:
    BACKUP_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


class AppSettings:
    def __init__(self) -> None:
        self._storage_backend = None
        self._raw_config: dict[str, Any] = {}
        self.reload()

    def _defaults(self) -> dict[str, Any]:
        return {
            "auth-key": "",
            "host": "0.0.0.0",
            "port": 8000,
            "refresh_account_interval_minute": 60,
            "image_retention_days": 15,
            "image_poll_timeout_secs": 120,
            "auto_remove_rate_limited_accounts": False,
            "auto_remove_invalid_accounts": True,
            "image_account_concurrency": 3,
            "log_levels": ["debug", "error", "info", "warning"],
            "proxy": "",
            "base_url": "",
            "sensitive_words": [],
            "global_system_prompt": "",
            "ai_review": {
                "enabled": False,
                "base_url": "",
                "api_key": "",
                "model": "",
                "prompt": "",
            },
            "backup": {
                "enabled": False,
                "provider": "cloudflare_r2",
                "account_id": "",
                "access_key_id": "",
                "secret_access_key": "",
                "bucket": "",
                "prefix": "backups",
                "interval_minutes": 1440,
                "rotation_keep": 10,
                "encrypt": False,
                "passphrase": "",
                "include": {
                    "config": True,
                    "register": True,
                    "cpa": True,
                    "sub2api": True,
                    "logs": True,
                    "image_tasks": True,
                    "accounts_snapshot": True,
                    "auth_keys_snapshot": True,
                    "images": False,
                },
            },
        }

    def _load_raw_config(self) -> dict[str, Any]:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        raw_config: dict[str, Any] = self._defaults()
        config_file = _readable_json_file(CONFIG_FILE, name="config.json")
        if config_file is not None:
            raw_config = _deep_merge(
                raw_config,
                cast(dict[str, Any], _load_json_object(config_file, name="config.json")),
            )

        auth_key = str(
            os.getenv("CHATGPT2API_AUTH_KEY")
            or raw_config.get("auth-key")
            or ""
        ).strip()
        if not auth_key:
            raise ValueError(
                "auth-key 未设置。\n"
                "请设置环境变量 CHATGPT2API_AUTH_KEY，或者在 config.json 中填写 auth-key。"
            )

        raw_config["auth-key"] = auth_key
        raw_config["host"] = str(
            os.getenv("CHATGPT2API_HOST")
            or os.getenv("HOST")
            or raw_config.get("host")
            or "0.0.0.0"
        ).strip() or "0.0.0.0"
        raw_config["port"] = int(
            os.getenv("CHATGPT2API_PORT")
            or os.getenv("PORT")
            or raw_config.get("port")
            or 8000
        )
        return raw_config

    def _apply(self, raw_config: dict[str, Any]) -> None:
        self._raw_config = raw_config
        self.auth_key = str(raw_config.get("auth-key") or "").strip()
        self.host = str(raw_config.get("host") or "0.0.0.0").strip() or "0.0.0.0"
        self.port = int(raw_config.get("port") or 8000)
        self.accounts_file = DATA_DIR / "accounts.json"
        self.auth_keys_file = DATA_DIR / "auth_keys.json"
        self.refresh_account_interval_minute = int(raw_config.get("refresh_account_interval_minute") or 60)
        self.image_retention_days = int(raw_config.get("image_retention_days") or 15)
        self.image_poll_timeout_secs = int(raw_config.get("image_poll_timeout_secs") or 120)
        self.auto_remove_rate_limited_accounts = bool(raw_config.get("auto_remove_rate_limited_accounts", False))
        self.auto_remove_invalid_accounts = bool(raw_config.get("auto_remove_invalid_accounts", True))
        self.image_account_concurrency = int(raw_config.get("image_account_concurrency") or 3)
        self.log_levels = list(raw_config.get("log_levels") or ["debug", "error", "info", "warning"])
        self.proxy = str(raw_config.get("proxy") or "").strip()
        self.base_url = str(raw_config.get("base_url") or "").strip()
        self.sensitive_words = [str(item) for item in (raw_config.get("sensitive_words") or []) if str(item).strip()]
        self.global_system_prompt = str(raw_config.get("global_system_prompt") or "").strip()
        self.ai_review = dict(raw_config.get("ai_review") or {})
        self.backup = dict(raw_config.get("backup") or {})
        self.images_dir = DATA_DIR / "images"
        self.image_thumbnails_dir = DATA_DIR / "image_thumbnails"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.image_thumbnails_dir.mkdir(parents=True, exist_ok=True)
        self.app_version = _read_version()

    def reload(self) -> None:
        self._apply(self._load_raw_config())

    def get(self) -> dict[str, Any]:
        return json.loads(json.dumps(self._raw_config, ensure_ascii=False))

    def _save(self) -> None:
        CONFIG_FILE.write_text(
            json.dumps(self._raw_config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def update(self, updates: dict[str, Any]) -> dict[str, Any]:
        merged = _deep_merge(self._raw_config, updates or {})
        self._apply(merged)
        self._save()
        return self.get()

    def get_proxy_settings(self) -> str:
        return self.proxy

    def get_backup_settings(self) -> dict[str, Any]:
        return dict(self.backup)

    def get_storage_backend(self):
        if self._storage_backend is None:
            self._storage_backend = create_storage_backend(DATA_DIR)
        return self._storage_backend

    def cleanup_old_images(self) -> None:
        retention_days = max(0, int(self.image_retention_days or 0))
        if retention_days <= 0 or not self.images_dir.exists():
            return
        now = time.time()
        cutoff_ts = now - retention_days * 86400
        for root in (self.images_dir, self.image_thumbnails_dir):
            if not root.exists():
                continue
            for path in root.rglob("*"):
                try:
                    if path.is_file() and path.stat().st_mtime < cutoff_ts:
                        path.unlink(missing_ok=True)
                except Exception:
                    continue
            self._cleanup_empty_dirs(root)

    @staticmethod
    def _cleanup_empty_dirs(root: Path) -> None:
        if not root.exists():
            return
        for path in sorted(root.rglob("*"), reverse=True):
            try:
                if path.is_dir() and not any(path.iterdir()):
                    path.rmdir()
            except Exception:
                continue


config = AppSettings()
