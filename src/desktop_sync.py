"""WT Mod Manager desktop sync: explicit, account-bound, background transfers.

Device pairing uses a short-lived server challenge, not the website's tokens.
Only the public API key is embedded. Device secrets are protected by Windows
DPAPI. Server approval and owner binding are checked on every request.
"""
from __future__ import annotations

import ctypes
import hashlib
import io
import json
import os
import re
import secrets
import shutil
import sys
import threading
from functools import wraps
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from ctypes import wintypes
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from src.profile_paths import DATA_DIR

API_ROOT = "https://ovvubbwzxikqcnuvvtjb.supabase.co"
API_KEY = "sb_publishable_NYOePmdOT87GXNFpI9j8OQ_Y8CIyLez"
BRIDGE = API_ROOT + "/functions/v1/wtmm-desktop-bridge"
SITE_LINK = "https://qwerthegoe-hash.github.io/WT-Mod-Manager-Website/desktop-link.html"
SECRET_FILE = DATA_DIR / "desktop-sync-device.bin"
UUID = re.compile(r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$", re.I)
EXTENSIONS = {
    "sights": {".png", ".jpg", ".jpeg", ".webp", ".bmp"},
    "camouflage": {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".dds", ".tga"},
    "sounds": {".wav", ".mp3", ".ogg", ".flac"},
}
LOCAL_FOLDERS = {"sights": "sights", "camouflage": "camouflages", "sounds": "sounds"}


class PackageError(ValueError):
    """Permanent invalid mod ZIP. Do not keep retrying automatically."""


class DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _protect(data: bytes, decrypt: bool = False) -> bytes:
    if sys.platform != "win32":
        raise OSError("Persistent device pairing requires Windows DPAPI.")
    crypt = ctypes.windll.crypt32
    func = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    func.restype = wintypes.BOOL
    if decrypt:
        func.argtypes = [ctypes.POINTER(DataBlob), ctypes.c_void_p,
                         ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                         wintypes.DWORD, ctypes.POINTER(DataBlob)]
    else:
        func.argtypes = [ctypes.POINTER(DataBlob), ctypes.c_wchar_p,
                         ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                         wintypes.DWORD, ctypes.POINTER(DataBlob)]
    buffer = ctypes.create_string_buffer(data)
    input_blob = DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    output_blob = DataBlob()
    if decrypt:
        success = func(ctypes.byref(input_blob), None, None, None, None, 0, ctypes.byref(output_blob))
    else:
        success = func(ctypes.byref(input_blob), "WT Mod Manager device", None, None, None, 0, ctypes.byref(output_blob))
    if not success:
        raise OSError("Windows could not protect/unprotect the device pairing.")
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        kernel = ctypes.windll.kernel32
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        kernel.LocalFree(ctypes.cast(output_blob.pbData, ctypes.c_void_p))


def _load_token() -> str | None:
    try:
        raw = _protect(SECRET_FILE.read_bytes(), decrypt=True).decode("utf-8")
        return raw if 40 <= len(raw) <= 80 and re.fullmatch(r"[A-Za-z0-9_-]+", raw) else None
    except (OSError, UnicodeError, ValueError):
        return None


def _save_token(token: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    safe = _protect(token.encode("utf-8"))
    temporary = SECRET_FILE.with_suffix(".tmp")
    temporary.write_bytes(safe)
    os.replace(temporary, SECRET_FILE)


def _call(action: str, token: str, **payload) -> dict:
    body = json.dumps({"action": action, "device_token": token, **payload}).encode("utf-8")
    request = Request(BRIDGE, data=body, headers={
        "Content-Type": "application/json", "apikey": API_KEY,
        "User-Agent": "WTModManager-Desktop/1.2"
    }, method="POST")
    try:
        with urlopen(request, timeout=15) as response:
            data = json.load(response)
        if not isinstance(data, dict):
            raise RuntimeError("Server returned an invalid response.")
        if data.get("error"):
            raise RuntimeError(str(data["error"]))
        return data
    except HTTPError as error:
        raise RuntimeError("Server returned HTTP " + str(error.code)) from error


def _download_zip(url: str) -> bytes:
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname != "ovvubbwzxikqcnuvvtjb.supabase.co"
            or parsed.username or parsed.password
            or not parsed.path.startswith("/storage/v1/object/sign/wtmm-mod-packages/")):
        raise PackageError("Unexpected mod download origin.")
    request = Request(url, headers={"User-Agent": "WTModManager-Desktop/1.2"})
    with urlopen(request, timeout=20) as response:
        if response.geturl().split("/")[2] != parsed.netloc:
            raise PackageError("Unexpected mod download redirect.")
        content = response.read(20 * 1024 * 1024 + 1)
    if len(content) > 20 * 1024 * 1024:
        raise PackageError("Archive is larger than 20 MB.")
    return content


def _safe_entries(data: bytes, category: str):
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as error:
        raise PackageError("Invalid ZIP archive.") from error
    with archive:
        files = archive.infolist()
        if len(files) > 150:
            raise PackageError("Too many files in archive.")
        total = 0
        valid = []
        for item in files:
            if item.is_dir():
                continue
            path = item.filename
            if ("\\" in path or path.startswith("/") or ":" in path or "\x00" in path
                    or ".." in Path(path).parts or len(path) > 230
                    or (item.external_attr >> 16) & 0o170000 == 0o120000):
                raise PackageError("Unsafe file path or symbolic link in ZIP.")
            total += item.file_size
            if total > 80 * 1024 * 1024 or item.file_size > 25 * 1024 * 1024:
                raise PackageError("Archive expands beyond the safety limit.")
            if Path(path).suffix.lower() in EXTENSIONS[category]:
                valid.append((item, Path(path).suffix.lower()))
        if not valid:
            raise PackageError("ZIP contains no supported files for its category.")
        if len(valid) > 70:
            raise PackageError("Too many supported files in archive.")
        unpacked = []
        for item, ext in valid:
            try:
                raw = archive.read(item)
            except (RuntimeError, zipfile.BadZipFile) as error:
                raise PackageError("Damaged archive entry.") from error
            if len(raw) != item.file_size:
                raise PackageError("File length mismatch.")
            # No scripts, executables or installers are extracted.
            unpacked.append((item.filename, ext, raw))
        return unpacked



# Qt GUI events and background network workers may both mutate the same
# account manifest. Serialize all account-level changes within this process.
_MANIFEST_LOCK = threading.RLock()


def _manifest_serialized(fn):
    @wraps(fn)
    def run(*args, **kwargs):
        with _MANIFEST_LOCK:
            return fn(*args, **kwargs)
    return run


def _managed_name(name, mod_id, category):
    return (
        isinstance(name, str)
        and name == Path(name).name
        and name.startswith(mod_id[:8] + "-")
        and Path(name).suffix.lower() in EXTENSIONS.get(category, set())
        and len(name) <= 110
        and "/" not in name and "\\" not in name
    )


def _write_manifest(manifest, library):
    manifest.parent.mkdir(parents=True, exist_ok=True)
    temporary = manifest.with_suffix(".tmp")
    temporary.write_text(json.dumps(library, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, manifest)


@_manifest_serialized
def restore_previous_mod(user_id: str, mod_id: str) -> tuple[int, str]:
    """Restore last version of an online mod, never touching PC-local files."""
    if not UUID.fullmatch(user_id) or not UUID.fullmatch(mod_id):
        raise PackageError("Invalid account or mod identifier.")
    account = DATA_DIR / "accounts" / user_id
    library = imported_library(user_id)
    current = library.get(mod_id)
    if not isinstance(current, dict) or not isinstance(current.get("previous"), dict):
        raise PackageError("No previous version is available.")
    previous = current["previous"]
    category = str(previous.get("category", ""))
    if category != current.get("category") or category not in LOCAL_FOLDERS:
        raise PackageError("Previous version is incompatible.")
    files = previous.get("files")
    backup_id = previous.get("backup_id")
    if (not isinstance(files, list) or not files or len(files) > 70 or
            not all(_managed_name(name, mod_id, category) for name in files) or
            not isinstance(backup_id, str) or not re.fullmatch(r"[0-9a-f]{24}", backup_id)):
        raise PackageError("Invalid version history.")
    backup = account / "history" / mod_id / backup_id
    destination = account / "mods" / LOCAL_FOLDERS[category]
    if not all((backup / name).is_file() and not (backup / name).is_symlink() for name in files):
        raise PackageError("Previous version backup is missing.")
    destination.mkdir(parents=True, exist_ok=True)
    for name in files:
        temp = destination / (name + ".restore")
        try:
            shutil.copy2(backup / name, temp)
            os.replace(temp, destination / name)
        finally:
            temp.unlink(missing_ok=True)
    # Drop only obsolete assets managed by this mod in the current account.
    for name in current.get("files", []):
        if name not in files and _managed_name(name, mod_id, category):
            target = destination / name
            if target.is_file() and not target.is_symlink():
                target.unlink()
    library[mod_id] = {
        "title": str(previous.get("title", ""))[:90],
        "version": str(previous.get("version", ""))[:32],
        "category": category,
        "sha256": str(previous.get("sha256", "")),
        "files": files,
        "imported_at": int(time.time()),
    }
    _write_manifest(account / "imported-mods.json", library)
    shutil.rmtree(backup, ignore_errors=True)
    return len(files), category


@_manifest_serialized
def _install_account_mod(user_id: str, meta: dict, archive_bytes: bytes) -> int:
    if not UUID.fullmatch(user_id):
        raise PackageError("Invalid account identifier.")
    mod_id = str(meta.get("mod_id", ""))
    category = str(meta.get("category", ""))
    if not UUID.fullmatch(mod_id) or category not in EXTENSIONS:
        raise PackageError("Mod is not compatible with the desktop library.")
    account = DATA_DIR / "accounts" / user_id
    dest = account / "mods" / LOCAL_FOLDERS[category]
    manifest = account / "imported-mods.json"
    archive_sha = hashlib.sha256(archive_bytes).hexdigest()
    try:
        library = json.loads(manifest.read_text("utf-8")) if manifest.is_file() else {}
        if not isinstance(library, dict):
            library = {}
    except (OSError, ValueError):
        library = {}
    old = library.get(mod_id)
    if (isinstance(old, dict) and old.get("sha256") == archive_sha and
            all((dest / name).is_file() for name in old.get("files", []))):
        return 0  # No duplicate imports if the same mod is re-requested.
    unpacked = _safe_entries(archive_bytes, category)
    dest.mkdir(parents=True, exist_ok=True)
    # Retain one previous version before modifying any currently installed
    # managed assets. This backup is scoped to this account and mod only.
    previous = None
    history_dir = account / "history" / mod_id
    if isinstance(old, dict) and old.get("category") == category:
        old_names = old.get("files")
        if (isinstance(old_names, list) and old_names
                and len(old_names) <= 70
                and all(_managed_name(n, mod_id, category) for n in old_names)
                and all((dest / n).is_file() and not (dest / n).is_symlink() for n in old_names)):
            backup_id = secrets.token_hex(12)
            backup = history_dir / backup_id
            backup.mkdir(parents=True, exist_ok=False)
            for name in old_names:
                shutil.copy2(dest / name, backup / name)
            previous = {
                "title": str(old.get("title", ""))[:90],
                "version": str(old.get("version", ""))[:32],
                "category": category,
                "sha256": str(old.get("sha256", "")),
                "files": list(old_names),
                "imported_at": old.get("imported_at"),
                "backup_id": backup_id,
            }
    names = []
    for index, (original, ext, raw) in enumerate(unpacked):
        stem = re.sub(r"[^A-Za-z0-9_-]+", "-", Path(original).stem)[:35].strip("-") or "asset"
        name = mod_id[:8] + "-" + str(index + 1).zfill(2) + "-" + stem + ext
        target = dest / name
        pending = dest / (name + ".part")
        try:
            pending.write_bytes(raw)
            os.replace(pending, target)
        finally:
            pending.unlink(missing_ok=True)
        names.append(name)
    library[mod_id] = {
        "title": str(meta.get("title", ""))[:90],
        "version": str(meta.get("version", ""))[:32],
        "category": category,
        "sha256": archive_sha,
        "files": names,
        "imported_at": int(time.time()),
        **({"previous": previous} if previous else {}),
    }
    _write_manifest(manifest, library)
    # Remove only older files generated for this mod and this same account.
    if isinstance(old, dict) and old.get("category") == category:
        for name in old.get("files", []):
            if name not in names and _managed_name(name, mod_id, category):
                target = dest / name
                if not target.is_symlink():
                    target.unlink(missing_ok=True)
    # Keep the last backup; older backups are pruned after successful install.
    if history_dir.is_dir():
        current_backup = previous.get("backup_id") if previous else None
        for folder in history_dir.iterdir():
            if folder.is_dir() and folder.name != current_backup:
                shutil.rmtree(folder, ignore_errors=True)
    return len(names)


@_manifest_serialized
def imported_library(user_id: str | None) -> dict:
    if not user_id or not UUID.fullmatch(user_id):
        return {}
    path = DATA_DIR / "accounts" / user_id / "imported-mods.json"
    try:
        result = json.loads(path.read_text("utf-8"))
        return result if isinstance(result, dict) else {}
    except (OSError, ValueError):
        return {}


class DesktopSync(QObject):
    """Network work stays off the UI thread. Only completed categories refresh."""
    status_changed = Signal(str)
    account_changed = Signal(str)
    files_changed = Signal(str)
    _completed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._token = _load_token()
        self._pairing_token = None
        self.user_id = None
        self._busy = False
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="wtmm-sync")
        self._completed.connect(self._on_completed)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.sync_now)
        self._timer.start(2500)
        self.sync_now()

    def _start(self, action: str, token: str) -> bool:
        if self._busy:
            return False
        self._busy = True
        task = self._pool.submit(self._work, action, token)
        def complete(future):
            try:
                self._completed.emit((action, token, True, future.result()))
            except Exception as error:
                self._completed.emit((action, token, False, str(error)[:200]))
        task.add_done_callback(complete)
        return True

    def link_account(self) -> None:
        if self._busy:
            self.status_changed.emit("Проверка выполняется. Попробуй привязку ещё раз.")
            return
        pending = secrets.token_urlsafe(32)
        if not self._start("register", pending):
            return
        self._pairing_token = pending
        self.status_changed.emit("Создаю защищённое подключение...")

    def sync_now(self) -> None:
        token = self._pairing_token or self._token
        if token:
            self._start("poll", token)

    def unlink_account(self) -> None:
        token = self._token or self._pairing_token
        self._token = None
        self._pairing_token = None
        self.user_id = None
        SECRET_FILE.unlink(missing_ok=True)
        self.account_changed.emit("")
        self.status_changed.emit("Аккаунт отключён. Локальные файлы сохранены.")
        if token:
            # A poll may still be running. Revoke after it, rather than
            # silently dropping the revoke request because _busy is true.
            self._pool.submit(self._work, "revoke", token)

    @staticmethod
    def _work(action: str, token: str) -> dict:
        if action == "register":
            return _call("register", token)
        if action == "revoke":
            return _call("revoke", token)
        state = _call("status", token)
        if not state.get("paired"):
            return {"paired": False}
        user_id = str(state.get("user_id", ""))
        if not UUID.fullmatch(user_id):
            raise RuntimeError("Account verification failed.")
        queued = _call("poll", token)
        changes = []
        for entry in queued.get("items", []):
            transfer_id = str(entry.get("transfer_id", ""))
            if not UUID.fullmatch(transfer_id):
                continue
            try:
                package = _call("package", token, transfer_id=transfer_id)
                archive = _download_zip(str(package["signed_url"]))
                changed = _install_account_mod(user_id, package, archive)
                _call("ack", token, transfer_id=transfer_id, state="applied")
                if changed:
                    changes.append(str(package["category"]))
            except PackageError as error:
                _call("ack", token, transfer_id=transfer_id,
                      state="failed", error=str(error)[:150])
            except (RuntimeError, OSError, URLError, KeyError, ValueError):
                # Transient network errors remain pending for the next poll.
                continue
        return {"paired": True, "user_id": user_id, "changed": list(set(changes))}

    def _on_completed(self, response) -> None:
        action, completed_token, ok, result = response
        self._busy = False
        if action == "revoke":
            return
        # Disconnect/relink can occur while a background poll is in flight.
        # Never let an old account's result reactivate its interface.
        if completed_token != (self._pairing_token or self._token):
            return
        if not ok:
            if action != "poll":
                self.status_changed.emit("Ошибка соединения: " + str(result))
            return
        if action == "register":
            pair_id = str(result.get("pair_id", ""))
            code = str(result.get("pair_code", ""))
            if not UUID.fullmatch(pair_id) or not re.fullmatch(r"[0-9a-f]{36}", code):
                self.status_changed.emit("Сервер вернул некорректный код привязки.")
                return
            link = SITE_LINK + "?pair_id=" + quote(pair_id) + "&code=" + quote(code)
            QDesktopServices.openUrl(QUrl(link))
            self.status_changed.emit("Подтверди привязку в открывшемся браузере.")
            return
        if action == "revoke":
            return
        if not result.get("paired"):
            return
        user_id = str(result["user_id"])
        if self._pairing_token:
            self._token = self._pairing_token
            self._pairing_token = None
            try:
                _save_token(self._token)
            except OSError:
                self.status_changed.emit("Привязка работает до закрытия приложения. Защищённое сохранение недоступно.")
        if self.user_id != user_id:
            self.user_id = user_id
            self.account_changed.emit(user_id)
            self.status_changed.emit("Аккаунт сайта подключён. Ожидаю команды из «Скачанных модов».")
        for category in result.get("changed", []):
            self.files_changed.emit(category)

    def stop(self) -> None:
        self._timer.stop()
        self._pool.shutdown(wait=False, cancel_futures=True)
