"""Build one portable/installed EXE with Python and resources inside.

The same PyInstaller onefile binary is published for portable users and
installed by Inno Setup, which adds per-user uninstall registration, shortcuts,
and an installed-app marker. The onefile executable still temporarily extracts
runtime files on launch; this is packaging, not encryption.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
import PyInstaller.__main__


ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "assets" / "icons" / "Logotip" / "LogotipProject.png"
ICON = ROOT / "build" / "WTModManager.ico"


def build() -> None:
    args = [
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name=WTModManager",
        "--paths=" + str(ROOT),
        "--icon=" + str(ICON),
        # Explicit allowlist: do NOT silently bundle future secrets/.env files.
        "--add-data=" + str(ROOT / "assets" / "icons") + ":assets/icons",
        "--add-data=" + str(ROOT / "config" / "support_config.json") + ":config",
        "--add-data=" + str(ROOT / "config" / "update_config.json") + ":config",
        "--add-binary=" + str(ROOT / "build" / "wtmm_taskbar.dll") + ":.",
        "--distpath=" + str(ROOT / "dist"),
        "--workpath=" + str(ROOT / "build" / "pyinstaller-onefile"),
        "--specpath=" + str(ROOT / "build" / "spec-onefile"),
        str(ROOT / "src" / "main.py"),
    ]
    PyInstaller.__main__.run(args)


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("WT Mod Manager packages must be built on Windows.")

    required = [
        ROOT / "src" / "main.py", ROOT / "assets" / "icons", LOGO,
        ROOT / "config" / "update_config.json",
        ROOT / "config" / "support_config.json",
        ROOT / "build" / "wtmm_taskbar.dll",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("Missing required project resources: " + ", ".join(missing))

    ICON.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(LOGO) as logo:
        logo.convert("RGBA").save(
            ICON, format="ICO", sizes=[
                (16, 16), (32, 32), (48, 48),
                (64, 64), (128, 128), (256, 256)
            ]
        )

    build()

    executable = ROOT / "dist" / "WTModManager.exe"
    if not executable.is_file() or executable.stat().st_size < 1024 * 1024:
        raise SystemExit("Missing onefile WTModManager.exe")

    print(f"Single-file executable: {executable} ({executable.stat().st_size} bytes)")
    print("The installer embeds this exact EXE; no standalone assets/config folders.")


if __name__ == "__main__":
    main()
