"""Local mod-file safety inspection and optional VirusTotal hash lookup.

No files are uploaded to VirusTotal. A personal API key is optional and saved
only in the current Windows user's DPAPI-protected profile; never in GitHub,
settings.json or logs. ZIP validation is structural, NOT an antivirus verdict.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import urllib.error
import urllib.request
import zipfile

from src.profile_paths import DATA_DIR

KEY_FILE = DATA_DIR / "virustotal-api-key.bin"
MAX_ZIP = 20 * 1024 * 1024
MAX_FILE = 25 * 1024 * 1024
MAX_ENTRIES = 150
MAX_TOTAL_UNPACKED = 80 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200

# Only mod-related data files may be accepted as a downloadable package.
MOD_EXTENSIONS = frozenset({
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".dds", ".tga",
    ".wav", ".mp3", ".ogg", ".flac",
    ".blk", ".cfg", ".txt", ".json", ".xml"
})


class SecurityError(ValueError):
    """Local inspection failure or unsafe archive."""


class VirusTotalError(RuntimeError):
    """VirusTotal public API was unavailable or rejected a request."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_mod_file(file_path: str | Path) -> dict:
    """Bounded, no-extraction inspection; no unsafe archive members executed."""
    path = Path(file_path).expanduser()
    if path.is_symlink() or not path.is_file():
        raise SecurityError("Выбранный файл недоступен или является ссылкой.")
    size = path.stat().st_size
    if size == 0 or size > MAX_FILE:
        raise SecurityError("Файл пустой или превышает лимит 25 МБ.")
    suffix = path.suffix.lower()
    if suffix != ".zip" and suffix not in MOD_EXTENSIONS:
        raise SecurityError("Этот тип файла не относится к разрешённым файлам модов.")
    count = 1
    if suffix == ".zip":
        if size > MAX_ZIP:
            raise SecurityError("ZIP превышает разрешённый размер 20 МБ.")
        names: set[str] = set()
        expanded = 0
        count = 0
        try:
            with zipfile.ZipFile(path) as archive:
                members = archive.infolist()
                if not members or len(members) > MAX_ENTRIES:
                    raise SecurityError("Неверное число элементов ZIP (не более 150).")
                for member in members:
                    name = member.filename
                    components = name.split("/")
                    if (not name or "\\" in name or name.startswith("/")
                            or re.match(r"^[A-Za-z]:", name)
                            or ":" in name or len(name) > 240
                            or any(x in ("", ".", "..") for x in components[:-1])
                            or any(ord(x) < 32 for x in name)):
                        raise SecurityError("ZIP содержит небезопасный путь.")
                    if member.flag_bits & 1:
                        raise SecurityError("Зашифрованный элемент ZIP запрещён.")
                    mode = stat.S_IFMT(member.external_attr >> 16)
                    if mode == stat.S_IFLNK:
                        raise SecurityError("ZIP содержит символическую ссылку.")
                    if member.compress_type not in (zipfile.ZIP_DEFLATED, zipfile.ZIP_STORED):
                        raise SecurityError("Неподдерживаемый формат сжатия ZIP.")
                    folded = name.casefold()
                    if folded in names:
                        raise SecurityError("В ZIP обнаружены повторяющиеся имена.")
                    names.add(folded)
                    if member.is_dir():
                        if member.file_size:
                            raise SecurityError("Некорректная папка в ZIP.")
                        continue
                    if Path(name).suffix.lower() not in MOD_EXTENSIONS:
                        raise SecurityError("ZIP содержит файлы неразрешённого типа.")
                    count += 1
                    expanded += member.file_size
                    if (member.file_size > MAX_FILE or expanded > MAX_TOTAL_UNPACKED
                            or (member.file_size > 0 and (
                                member.compress_size == 0 or
                                member.file_size / member.compress_size > MAX_COMPRESSION_RATIO
                            ))):
                        raise SecurityError("ZIP может содержать опасную степень сжатия.")
                    # Reading every member checks decompression and CRC without writing
                    # a single extracted file to disk.
                    read = 0
                    with archive.open(member) as stream:
                        while True:
                            block = stream.read(1024 * 1024)
                            if not block:
                                break
                            read += len(block)
                            if read > member.file_size:
                                raise SecurityError("Неверная длина элемента ZIP.")
                    if read != member.file_size:
                        raise SecurityError("Повреждённый элемент ZIP.")
                if count == 0:
                    raise SecurityError("В ZIP нет файлов модов.")
        except (zipfile.BadZipFile, RuntimeError, EOFError, OSError) as error:
            raise SecurityError("ZIP повреждён или содержит некорректные данные.") from error

    return {"path": str(path), "sha256": _sha256(path), "bytes": size,
            "files": count, "zip": suffix == ".zip",
            "message": ("Структура ZIP проверена" if suffix == ".zip"
                        else "Тип и размер файла проверены") +
                       ". Это не антивирусная проверка."}


def _dpapi(payload: bytes, decrypt: bool = False) -> bytes:
    from src.desktop_sync import _protect
    return _protect(payload, decrypt=decrypt)


def has_vt_key() -> bool:
    try:
        return bool(load_vt_key())
    except VirusTotalError:
        return False


def save_vt_key(key: str) -> None:
    """Persist encrypted credentials only if Windows DPAPI is available."""
    if sys.platform != "win32":
        raise VirusTotalError("Сохранение API-ключа поддерживается только в Windows.")
    value = str(key or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", value):
        raise VirusTotalError("Неверный формат личного API-ключа VirusTotal.")
    try:
        sealed = _dpapi(value.encode("ascii"))
        KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp = KEY_FILE.with_suffix(".tmp")
        try:
            temp.write_bytes(sealed)
            os.replace(temp, KEY_FILE)
        finally:
            temp.unlink(missing_ok=True)
    except (OSError, ValueError) as error:
        raise VirusTotalError("Windows не смогла безопасно сохранить ключ.") from error


def load_vt_key() -> str | None:
    if not KEY_FILE.is_file():
        return None
    if sys.platform != "win32":
        return None
    try:
        value = _dpapi(KEY_FILE.read_bytes(), decrypt=True).decode("ascii")
    except (OSError, UnicodeError, ValueError) as error:
        raise VirusTotalError("Не удалось прочитать защищённый API-ключ.") from error
    return value if re.fullmatch(r"[A-Za-z0-9_-]{32,128}", value) else None


def remove_vt_key() -> None:
    try:
        KEY_FILE.unlink(missing_ok=True)
    except OSError as error:
        raise VirusTotalError("Не удалось удалить локальный API-ключ.") from error


def verify_vt_key() -> bool:
    """User-triggered authentication probe. Sends only a public SHA-256.

    A valid key may return HTTP 404 for an unknown hash; lookup_vt_sha256
    treats this as an authorized result. This consumes one public API request.
    """
    empty_sha256 = hashlib.sha256(b"").hexdigest()
    lookup_vt_sha256(empty_sha256)
    return True


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def lookup_vt_sha256(digest: str, api_key: str | None = None) -> dict:
    """One explicit lookup of a hash; file content NEVER leaves this computer."""
    if not re.fullmatch(r"[0-9a-f]{64}", str(digest or "")):
        raise VirusTotalError("Некорректный SHA-256.")
    key = api_key if api_key is not None else load_vt_key()
    if not key:
        raise VirusTotalError("Сначала укажи личный API-ключ VirusTotal.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", key):
        raise VirusTotalError("Некорректный API-ключ.")
    request = urllib.request.Request(
        "https://www.virustotal.com/api/v3/files/" + digest,
        headers={"x-apikey": key, "Accept": "application/json",
                 "User-Agent": "WTModManager-Community/1.3"},
        method="GET"
    )
    try:
        with urllib.request.build_opener(_NoRedirect()).open(request, timeout=15) as response:
            data = response.read(1024 * 1024 + 1)
            if len(data) > 1024 * 1024:
                raise VirusTotalError("Отчёт VirusTotal слишком большой.")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return {"known": False, "sha256": digest}
        if error.code == 429:
            raise VirusTotalError("Лимит VirusTotal исчерпан. Повтори позже.") from None
        if error.code in (401, 403):
            raise VirusTotalError("API-ключ недействителен или доступ запрещён.") from None
        raise VirusTotalError("Сервис VirusTotal вернул ошибку HTTP " +
                              str(error.code)) from None
    except (OSError, TimeoutError, urllib.error.URLError) as error:
        raise VirusTotalError("Нет соединения с VirusTotal.") from error
    try:
        report = json.loads(data)
        attributes = report["data"]["attributes"]
        stats = attributes["last_analysis_stats"]
        if not isinstance(stats, dict):
            raise ValueError
        parsed = {label: max(0, int(stats.get(label, 0)))
                  for label in ("malicious", "suspicious", "harmless", "undetected")}
    except (ValueError, TypeError, KeyError, UnicodeError) as error:
        raise VirusTotalError("Некорректный формат отчёта VirusTotal.") from error
    return {"known": True, "sha256": digest, **parsed}
