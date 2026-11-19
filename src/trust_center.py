"""On-demand local executable trust checks, never changing Defender settings.

A valid Authenticode signature proves a trusted Windows signing chain, not
that a program is harmless. A GitHub SHA-256 value is not an Authenticode
signature. No files or identifiers are uploaded by this module.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from src.update_checker import VERSION, update_channel, is_installed_app

STATUS_ALLOWLIST = frozenset({
    "Valid", "NotSigned", "NotTrusted", "UnknownError", "HashMismatch",
    "NotTimeValid", "NotSupportedFileFormat", "Incompatible",
})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_executable_trust(path: Path | None = None) -> dict:
    """Bounded check of the *running* local EXE, without network access."""
    target = Path(path if path is not None else sys.executable)
    report = {
        "version": VERSION,
        "channel": update_channel(),
        "distribution": "installed" if is_installed_app() else "portable",
        "sha256": None,
        "authenticode": "Недоступно",
        "publisher": None,
        "note": "SHA-256 не является цифровой подписью.",
    }
    if not target.is_file() or target.is_symlink():
        report["authenticode"] = "Файл недоступен"
        return report
    size = target.stat().st_size
    if size > 350 * 1024 * 1024 or size < 2:
        report["authenticode"] = "Некорректный размер"
        return report
    with target.open("rb") as stream:
        magic = stream.read(2)
    if magic != b"MZ" and sys.platform == "win32":
        report["authenticode"] = "Файл не является Windows EXE"
        return report
    report["sha256"] = _sha256(target)
    report["size_bytes"] = size
    if sys.platform != "win32":
        report["authenticode"] = "Проверка подписи доступна только в Windows"
        return report
    # No paths in the command text, and no shell invocation with user input.
    env = os.environ.copy()
    env["WTMM_TRUST_CHECK_PATH"] = str(target)
    command = (
        "$ErrorActionPreference='Stop';"
        "$r=Get-AuthenticodeSignature -LiteralPath $env:WTMM_TRUST_CHECK_PATH;"
        "[pscustomobject]@{Status=$r.Status.ToString();"
        "Publisher=if($r.SignerCertificate){$r.SignerCertificate.Subject}"
        "else{''}} | ConvertTo-Json -Compress"
    )
    try:
        process = subprocess.run(
            ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive",
             "-Command", command],
            capture_output=True, text=True, timeout=12, env=env, check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if len(process.stdout) > 2048:
            raise ValueError("Unexpectedly long signature result")
        result = json.loads(process.stdout)
        status = str(result.get("Status") or "UnknownError")
        if status not in STATUS_ALLOWLIST:
            status = "UnknownError"
        report["authenticode"] = status
        publisher = str(result.get("Publisher") or "")[:180]
        if status == "Valid" and publisher and not re.search(r"[\x00-\x1f]", publisher):
            report["publisher"] = publisher
    except (OSError, subprocess.SubprocessError, ValueError, TypeError):
        report["authenticode"] = "Не удалось проверить подпись"
    return report


def format_local_trust(report: dict) -> str:
    status = report.get("authenticode", "Неизвестно")
    lines = [
        "WT Trust Center — локальная проверка (без отправки файлов)",
        "Версия: " + str(report.get("version", "?")),
        "Канал: " + str(report.get("channel", "?")),
        "Установка: " + str(report.get("distribution", "?")),
        "SHA-256: " + str(report.get("sha256") or "недоступен"),
        "Подпись Windows Authenticode: " + str(status),
    ]
    if report.get("publisher"):
        lines.append("Издатель сертификата: " + report["publisher"])
    lines += [
        "",
        "Valid означает действительную подпись в проверке Windows, не гарантию безопасности.",
        "NotSigned означает отсутствие цифровой подписи.",
        "Для подтверждения источника сравни SHA-256 с GitHub Releases и",
        "проверь GitHub Attestation для той же версии.",
    ]
    return "\n".join(lines)
