from __future__ import annotations

from typing import Any

try:
    from curl_cffi import requests as requests
    from curl_cffi.requests import Session
except Exception:
    import requests as _requests

    def _proxy_map(proxy: object) -> dict[str, str]:
        value = str(proxy or "").strip()
        if not value:
            return {}
        return {"http": value, "https": value}


    class Session(_requests.Session):
        """Small curl_cffi-compatible wrapper for FreeBSD / serv00."""

        def __init__(
            self,
            *args: Any,
            impersonate: str | None = None,
            proxy: str | None = None,
            verify: bool | str = True,
            **kwargs: Any,
        ) -> None:
            super().__init__()
            self.trust_env = False
            self.verify = verify
            self._compat_proxy = str(proxy or "").strip()

            proxies = kwargs.pop("proxies", None)
            if isinstance(proxies, dict):
                self.proxies.update({str(k): str(v) for k, v in proxies.items() if v})
            elif self._compat_proxy:
                self.proxies.update(_proxy_map(self._compat_proxy))

            headers = kwargs.pop("headers", None)
            if isinstance(headers, dict):
                self.headers.update({str(k): str(v) for k, v in headers.items()})

        def request(self, method: str, url: str, *args: Any, **kwargs: Any):
            kwargs.pop("impersonate", None)
            proxy = str(kwargs.pop("proxy", "") or self._compat_proxy).strip()
            if proxy and "proxies" not in kwargs:
                kwargs["proxies"] = _proxy_map(proxy)
            kwargs.setdefault("verify", self.verify)
            return super().request(method, url, *args, **kwargs)


    class _RequestsFacade:
        Response = _requests.Response
        Session = Session
        exceptions = _requests.exceptions

        @staticmethod
        def request(method: str, url: str, *args: Any, **kwargs: Any):
            session = Session(
                proxy=str(kwargs.pop("proxy", "")).strip() or None,
                verify=kwargs.pop("verify", True),
            )
            try:
                return session.request(method, url, *args, **kwargs)
            finally:
                session.close()

        @classmethod
        def get(cls, url: str, *args: Any, **kwargs: Any):
            return cls.request("GET", url, *args, **kwargs)

        @classmethod
        def post(cls, url: str, *args: Any, **kwargs: Any):
            return cls.request("POST", url, *args, **kwargs)

        @classmethod
        def put(cls, url: str, *args: Any, **kwargs: Any):
            return cls.request("PUT", url, *args, **kwargs)

        @classmethod
        def delete(cls, url: str, *args: Any, **kwargs: Any):
            return cls.request("DELETE", url, *args, **kwargs)


    requests = _RequestsFacade()

