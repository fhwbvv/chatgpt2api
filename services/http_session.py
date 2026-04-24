from __future__ import annotations

try:
    from curl_cffi.requests import Session as Session

    SESSION_BACKEND = "curl_cffi"
except ImportError:
    import requests

    SESSION_BACKEND = "requests"

    class Session(requests.Session):
        def __init__(self, impersonate: str | None = None, verify: bool = True, **kwargs):
            super().__init__()
            self.impersonate = impersonate or ""
            self.verify = verify
            headers = kwargs.pop("headers", None)
            if isinstance(headers, dict):
                self.headers.update(headers)
