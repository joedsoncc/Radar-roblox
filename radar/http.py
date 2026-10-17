"""Cliente HTTP mínimo (só biblioteca padrão) com limite de taxa e repetição.

Regra do projeto: se a API falhar, devolvemos um erro explícito. Nunca um número inventado.
"""
import http.client
import json
import random
import time
import urllib.error
import urllib.request

USER_AGENT = "roblox-ugc-radar/1.0 (+github actions; somente leitura)"


class ApiError(Exception):
    def __init__(self, url, status, message=""):
        super().__init__(f"{status} em {url}: {message}")
        self.url = url
        self.status = status


class AuthRequired(ApiError):
    """A API respondeu 401/403: exige login. Não contornamos."""


class Client:
    def __init__(self, delay_s=1.2, max_retries=4, timeout_s=20, opener=None):
        self.delay_s = delay_s
        self.max_retries = max_retries
        self.timeout_s = timeout_s
        self._last = 0.0
        self._csrf = None
        self._open = opener or urllib.request.urlopen
        self.calls = 0

    def _wait(self):
        gap = time.monotonic() - self._last
        if gap < self.delay_s:
            time.sleep(self.delay_s - gap)
        self._last = time.monotonic()

    def _request(self, url, data=None, csrf=False):
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        body = None
        if data is not None:
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
            if csrf and self._csrf:
                headers["X-CSRF-TOKEN"] = self._csrf
        return urllib.request.Request(url, data=body, headers=headers,
                                      method="POST" if body is not None else "GET")

    def get_json(self, url):
        return self._send(url)

    def post_json(self, url, data):
        """POST em endpoints públicos que pedem token CSRF (obtido sem login no 1º 403)."""
        return self._send(url, data=data, csrf=True)

    def _send(self, url, data=None, csrf=False):
        attempt = 0
        csrf_retry = False
        while True:
            self._wait()
            self.calls += 1
            try:
                with self._open(self._request(url, data, csrf), timeout=self.timeout_s) as r:
                    raw = r.read()
                    return json.loads(raw.decode() or "null")
            except urllib.error.HTTPError as e:
                status = e.code
                token = e.headers.get("x-csrf-token") if e.headers else None
                if status == 403 and csrf and token and not csrf_retry:
                    self._csrf = token
                    csrf_retry = True
                    continue
                if status in (401, 403):
                    raise AuthRequired(url, status, "a API exigiu login")
                if status == 429 or 500 <= status < 600:
                    if attempt >= self.max_retries:
                        raise ApiError(url, status, "limite de taxa/servidor após repetições")
                    retry_after = e.headers.get("Retry-After") if e.headers else None
                    try:
                        pause = float(retry_after)
                    except (TypeError, ValueError):
                        pause = (2 ** attempt) * 2 + random.random()
                    time.sleep(min(pause, 60))
                    attempt += 1
                    continue
                raise ApiError(url, status, e.reason if hasattr(e, "reason") else "")
            except (urllib.error.URLError, http.client.HTTPException, OSError) as e:
                if attempt >= self.max_retries:
                    raise ApiError(url, "rede", str(e))
                time.sleep((2 ** attempt) * 2)
                attempt += 1
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                raise ApiError(url, "json", type(e).__name__)
