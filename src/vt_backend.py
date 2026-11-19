"""Server-mediated VirusTotal report lookups for paired WT Mod Manager devices.

No VirusTotal API key is present in this client. Only SHA-256 and the Windows
DPAPI-protected device pairing token are sent to the official Supabase project.
"""
from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler

from src.desktop_sync import API_KEY, API_ROOT, _load_token
from src.mod_security import VirusTotalError

ENDPOINT = API_ROOT + "/functions/v1/wtmm-vt-lookup"
VALID_HASH = re.compile(r"^[0-9a-f]{64}$")
MAX_RESPONSE = 64 * 1024


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def lookup_shared_vt_hash(digest: str) -> dict:
    if not isinstance(digest, str) or not VALID_HASH.fullmatch(digest):
        raise VirusTotalError("Неправильный SHA-256.")
    token = _load_token()
    if not token:
        raise VirusTotalError(
            "Для общей проверки VirusTotal сначала свяжи аккаунт сайта с WT Mod Manager."
        )
    body = json.dumps({"sha256": digest, "device_token": token}).encode("utf-8")
    request = Request(
        ENDPOINT, data=body,
        headers={"Content-Type": "application/json", "apikey": API_KEY,
                 "User-Agent": "WTModManager/1.3 Secure Hash Lookup"},
        method="POST"
    )
    try:
        with build_opener(_NoRedirect()).open(request, timeout=18) as response:
            raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise VirusTotalError("Сервер вернул слишком большой ответ.")
    except HTTPError as error:
        if error.code == 401:
            raise VirusTotalError(
                "Аккаунт не подключён. Переподключи аккаунт сайта."
            ) from None
        if error.code == 429:
            raise VirusTotalError(
                "Лимит общей бесплатной проверки достигнут. Повтори позже."
            ) from None
        raise VirusTotalError("Сервер проверки недоступен: HTTP " +
                              str(error.code)) from None
    except (OSError, URLError) as error:
        raise VirusTotalError("Не удалось связаться с сервером проверки.") from error

    try:
        report = json.loads(raw)
        if not isinstance(report, dict) or report.get("error"):
            raise ValueError("service response")
        if report.get("known") is False:
            return {"known": False, "sha256": digest}
        if report.get("known") is not True or report.get("sha256") != digest:
            raise ValueError("digest mismatch")
        counts = {}
        for key in ("malicious", "suspicious", "harmless", "undetected"):
            value = report.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError("invalid count")
            counts[key] = value
        return {"known": True, "sha256": digest, **counts}
    except (ValueError, TypeError, UnicodeError) as error:
        raise VirusTotalError("Получен некорректный отчёт сервера.") from error
