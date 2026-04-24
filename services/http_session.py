from __future__ import annotations

try:
    from curl_cffi import requests as requests
    from curl_cffi.requests import Session as Session

    SESSION_BACKEND = "curl_cffi"
except ImportError:
    import requests as requests

    SESSION_BACKEND = "requests"

    class Session(requests.Session):
        def __init__(self, impersonate: str | None = None, verify: bool = True, **kwargs):
            proxy = kwargs.pop("proxy", None)
            proxies = kwargs.pop("proxies", None)
            super().__init__()
            self.impersonate = impersonate or ""
            self.verify = verify
            headers = kwargs.pop("headers", None)
            if isinstance(headers, dict):
                self.headers.update(headers)
            if isinstance(proxies, dict):
                self.proxies.update(proxies)
            elif isinstance(proxy, str) and proxy.strip():
                self.proxies.update({
                    "http": proxy.strip(),
                    "https": proxy.strip(),
                })

    requests.Session = Session
