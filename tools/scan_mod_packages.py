#!/usr/bin/env python3
"""WT Mod Manager server-side quarantine scanner.

Reads private Supabase Storage objects via a server-only key, validates ZIPs without
extracting them to disk, then scans the original archive using updated ClamAV.
Only a clean scan is recorded as publishable. No secret is sent to the browser.
Use via GitHub Actions, not from GitHub Pages.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile

MAX_DOWNLOAD = 20 * 1024 * 1024
MAX_FILES = 4096
MAX_EXPANDED = 200 * 1024 * 1024
MAX_RATIO = 200
MAX_ATTEMPTS = 3
PATH_RE = re.compile(r"^[a-f0-9-]{36}/[a-f0-9-]{36}/[a-f0-9-]{36}\.zip$", re.I)
ID_RE = re.compile(r"^[0-9a-f-]{36}$", re.I)


class UnsafeArchive(ValueError):
    """Archive is invalid or violates the review format policy."""


def validate_zip(filename: Path) -> int:
    """Read every member in bounded chunks, checking CRC, paths, sizes and flags."""
    names: set[str] = set()
    total = 0
    try:
        with zipfile.ZipFile(filename) as archive:
            members = archive.infolist()
            if not members or len(members) > MAX_FILES:
                raise UnsafeArchive("Unacceptable number of entries")
            for member in members:
                name = member.filename.replace("\\", "/")
                pieces = name.split("/")
                if (not name or name.startswith("/") or name.startswith("//")
                    or re.match(r"^[A-Za-z]:", name)
                    or any(p == ".." for p in pieces)
                    or ":" in name or len(name) > 1024
                    or any(ord(c) < 32 for c in name)):
                    raise UnsafeArchive("Unsafe member path")
                folded = name.casefold()
                if folded in names:
                    raise UnsafeArchive("Duplicate member path")
                names.add(folded)
                if member.flag_bits & 1:
                    raise UnsafeArchive("Encrypted member")
                if member.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                    raise UnsafeArchive("Unsupported compression")
                if stat.S_IFMT(member.external_attr >> 16) == stat.S_IFLNK:
                    raise UnsafeArchive("Symbolic link")
                if member.file_size > MAX_EXPANDED or (
                    member.file_size > 0 and
                    (member.compress_size == 0 or member.file_size / member.compress_size > MAX_RATIO)
                ):
                    raise UnsafeArchive("Excessive compression")
                total += member.file_size
                if total > MAX_EXPANDED:
                    raise UnsafeArchive("Expanded size limit")
                if member.is_dir():
                    if member.file_size != 0:
                        raise UnsafeArchive("Invalid directory entry")
                    continue
                with archive.open(member) as stream:
                    consumed = 0
                    while True:
                        chunk = stream.read(1024 * 1024)
                        if not chunk:
                            break
                        consumed += len(chunk)
                        if consumed > member.file_size or consumed > MAX_EXPANDED:
                            raise UnsafeArchive("Expanded member size mismatch")
                    if consumed != member.file_size:
                        raise UnsafeArchive("ZIP member truncated")
    except (zipfile.BadZipFile, EOFError, OSError, RuntimeError, UnicodeError) as error:
        raise UnsafeArchive("ZIP structure or CRC failed") from error
    return len(names)


def clamav_clean(filename: Path) -> bool:
    """Return True only when ClamAV successfully reports a clean archive."""
    result = subprocess.run(
        [
            "clamscan", "--no-summary", "--scan-archive=yes",
            "--alert-exceeds-max=yes", "--alert-encrypted=yes",
            "--max-filesize=25M", "--max-scansize=250M",
            "--max-files=4096", "--max-recursion=16",
            "--max-scantime=90000", str(filename)
        ],
        capture_output=True, text=True, timeout=150, check=False,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise RuntimeError("ClamAV scan unavailable or incomplete")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


class Supabase:
    def __init__(self, base: str, key: str):
        base = base.rstrip("/")
        if not re.fullmatch(r"https://[a-z0-9-]+\.supabase\.co", base):
            raise RuntimeError("Invalid Supabase project URL")
        if not key or len(key) < 30:
            raise RuntimeError("Missing service-role credential")
        self.base, self.key = base, key

    def request(self, method: str, endpoint: str, *, data: dict | None = None, binary=False):
        body = json.dumps(data).encode("utf-8") if data is not None else None
        headers = {
            "apikey": self.key,
            "Authorization": "Bearer " + self.key,
            "Accept": "application/json",
            "Cache-Control": "no-store",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
            headers["Prefer"] = "return=representation"
        req = urllib.request.Request(self.base + endpoint, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                if binary:
                    length = response.headers.get("Content-Length")
                    if length and int(length) > MAX_DOWNLOAD:
                        raise UnsafeArchive("Download too large")
                    payload = response.read(MAX_DOWNLOAD + 1)
                    if not payload or len(payload) > MAX_DOWNLOAD:
                        raise UnsafeArchive("Download invalid or too large")
                    return payload
                raw = response.read(1024 * 1024)
                return json.loads(raw) if raw else []
        except urllib.error.HTTPError as error:
            raise RuntimeError("Supabase HTTP " + str(error.code)) from None

    def listing(self, status_filter: str, stale: bool = False) -> list[dict]:
        params = {
            "select": "id,file_path,status,scan_status,scan_attempts,scan_started_at",
            "status": "in.(pending,approved)",
            "scan_attempts": "lt." + str(MAX_ATTEMPTS),
            "order": "created_at.asc",
            "limit": "10",
        }
        if stale:
            cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=2)
            params["scan_status"] = "eq.scanning"
            params["scan_started_at"] = "lt." + cutoff.isoformat()
        else:
            params["scan_status"] = "in.(pending,error)"
        endpoint = "/rest/v1/wtmm_mods?" + urllib.parse.urlencode(params)
        result = self.request("GET", endpoint)
        return result if isinstance(result, list) else []

    def claim(self, job: dict) -> bool:
        params = {
            "id": "eq." + job["id"],
            "status": "eq." + job["status"],
            "scan_status": "eq." + job["scan_status"],
            "scan_attempts": "eq." + str(job["scan_attempts"]),
        }
        if job["scan_status"] == "scanning" and job.get("scan_started_at"):
            params["scan_started_at"] = "eq." + job["scan_started_at"]
        path = "/rest/v1/wtmm_mods?" + urllib.parse.urlencode(params)
        rows = self.request("PATCH", path, data={
            "scan_status": "scanning", "scan_started_at": now(),
            "scan_completed_at": None, "scan_sha256": None, "scan_note": None,
            "scan_attempts": job["scan_attempts"] + 1,
        })
        return bool(rows)

    def finish(self, job: dict, state: str, digest: str | None, note: str | None):
        updates = {
            "scan_status": state, "scan_sha256": digest,
            "scan_completed_at": now(), "scan_note": note,
        }
        # A ClamAV detection blocks BOTH pending and legacy published objects.
        # Structural ZIP validation alone is never an antivirus verdict.
        if state == "blocked" and job["status"] in ("pending", "approved"):
            updates["status"] = "rejected"
            updates["rejection_reason"] = "Automatic antivirus/archive safety review failed"
        params = urllib.parse.urlencode({
            "id": "eq." + job["id"], "scan_status": "eq.scanning",
            "status": "eq." + job["status"],
        })
        self.request("PATCH", "/rest/v1/wtmm_mods?" + params, data=updates)

    def download(self, package_path: str) -> bytes:
        if not PATH_RE.fullmatch(package_path):
            raise UnsafeArchive("Invalid package storage path")
        safe_path = urllib.parse.quote(package_path, safe="/")
        endpoint = "/storage/v1/object/authenticated/wtmm-mod-packages/" + safe_path
        return self.request("GET", endpoint, binary=True)


def process(db: Supabase, job: dict) -> str:
    if not ID_RE.fullmatch(str(job.get("id", ""))) or not PATH_RE.fullmatch(
        str(job.get("file_path", ""))
    ):
        return "skipped"
    if not db.claim(job):
        return "skipped"
    digest = None
    try:
        package = db.download(job["file_path"])
        digest = hashlib.sha256(package).hexdigest()
        with tempfile.TemporaryDirectory(prefix="wtmm-scan-") as tempdir:
            archive = Path(tempdir) / "package.zip"
            archive.write_bytes(package)
            validate_zip(archive)
            state = "clean" if clamav_clean(archive) else "blocked"
        db.finish(job, state, digest, None if state == "clean" else "Antivirus alert")
        return state
    except UnsafeArchive:
        db.finish(job, "blocked", digest, "Archive validation rejected")
        return "blocked"
    except (RuntimeError, OSError, subprocess.TimeoutExpired, TimeoutError):
        db.finish(job, "error", None, "Temporary scanner error")
        return "error"


def main() -> int:
    # Do not print sensitive response bodies, URLs, credentials or package names.
    try:
        base = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        db = Supabase(base, key)
        jobs = db.listing("pending") + db.listing("scanning", stale=True)
        result = {"clean": 0, "blocked": 0, "error": 0, "skipped": 0}
        for job in jobs[:20]:
            state = process(db, job)
            result[state] += 1
        print("WTMM scan batch: " + json.dumps(result, sort_keys=True))
        return 0 if result["error"] == 0 else 1
    except (KeyError, RuntimeError, urllib.error.URLError, OSError, ValueError):
        print("WTMM scanner configuration or service failure", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
