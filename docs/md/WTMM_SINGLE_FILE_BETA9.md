# WT Mod Manager Beta 9 — One-EXE installer and resource protection

## What changed

The public installer now deploys the same `WTModManager.exe` used by portable
users, with an additional `wtmm.installed` marker and Inno Setup's uninstall
metadata. PyInstaller's `--onefile` mode includes Python, PySide6, required
native DLLs, icon assets, and two **public** config JSON files.

The installed folder no longer needs visible `_internal`, `assets`, or
`config` directories. Existing Beta 8 users are upgraded in place; only the
old generated `_internal` directory is removed when this app's marker exists.
Personal settings, mods, and protected credentials live under
`%LOCALAPPDATA%\WTModManager` and are left untouched.

The packaged asset/config set is allowlisted:
- `assets/icons` (including official WT Mod Manager branding)
- `config/support_config.json`
- `config/update_config.json`

Other future files under `config/`, including any `.env`, are **not**
automatically added to releases.

## Important security limitations

This is **resource bundling, not encryption**. When launching a onefile EXE,
PyInstaller extracts runtime components to a private temporary `_MEI*`
directory. Users with access to the process/computer can inspect those files,
and Python bytecode may be reverse-engineered. Don't embed secret API keys,
database service-role keys, or proprietary signing private keys in an EXE.

Onefile startup can be slower and may generate antivirus false positives.
The right solution to Windows SmartScreen reputation is genuine publisher
code signing and trusted distribution, never disabling Defender or trying to
hide execution from security software.

## VirusTotal API key

The app has `Загрузки → Диагностика и безопасность` with:
- Save/delete a **personal** key using Windows DPAPI (local user profile).
- An explicit `Проверить API-ключ` button. This uses a single GET lookup
  by the public SHA-256 of an empty file; it does NOT upload file contents.
- User-initiated lookup by SHA-256 after local archive inspection.

Do not copy a user key into GitHub code, installer, CI logs, releases, or
public documentation. Because a key was shared in a chat, rotate/reissue it
before saving the replacement locally. API rate limits and noncommercial
usage restrictions continue to apply.

## Release verification

Windows Actions verifies:
- Source compilation, GUI startup, mod scanning, installer integration tests.
- PyInstaller single EXE output, branded Inno Setup compilation.
- Fresh install has no visible `_internal`, `assets`, or `config` directories.
- In-place upgrade deletes a simulated older generated `_internal` folder.
- Installed app starts, uninstalls, and SHA-256 manifests match published files.
