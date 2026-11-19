"""Build both a portable EXE and an installed onedir Windows app.

Portable EXE remains published for backward-compatible updates. The onedir
payload is what the branded Inno Setup installer installs. Both are built from
the same Python sources, icon, and embedded assets; no source code or runtime
package is downloaded when the installer runs.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
import PyInstaller.__main__


ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "assets" / "icons" / "Logotip" / "LogotipProject.png"
ICON = ROOT / "build" / "WTModManager.ico"


def build(mode: str) -> None:
    args = [
        "--noconfirm",
        "--clean",
        "--onefile" if mode == "portable" else "--onedir",
        "--windowed",
        "--name=WTModManager",
        "--paths=" + str(ROOT),
        "--icon=" + str(ICON),
        "--add-data=" + str(ROOT / "assets") + ":assets",
        "--add-data=" + str(ROOT / "config") + ":config",
        "--add-binary=" + str(ROOT / "build" / "wtmm_taskbar.dll") + ":.",
        "--distpath=" + str(ROOT / "dist"),
        "--workpath=" + str(ROOT / "build" / ("pyinstaller-" + mode)),
        "--specpath=" + str(ROOT / "build" / ("spec-" + mode)),
        str(ROOT / "src" / "main.py"),
    ]
    PyInstaller.__main__.run(args)


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("WT Mod Manager packages must be built on Windows.")

    required = [
        ROOT / "src" / "main.py", ROOT / "assets", ROOT / "config", LOGO,
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

    build("portable")
    build("installed")

    portable = ROOT / "dist" / "WTModManager.exe"
    installed = ROOT / "dist" / "WTModManager" / "WTModManager.exe"
    bundle = ROOT / "dist" / "WTModManager" / "_internal"
    if not portable.is_file() or portable.stat().st_size < 1024 * 1024:
        raise SystemExit("Missing portable WTModManager.exe")
    if not installed.is_file() or not bundle.is_dir():
        raise SystemExit("Missing onedir Windows application or Qt dependencies")

    print(f"Portable EXE: {portable} ({portable.stat().st_size} bytes)")
    print(f"Installer app: {installed} ({installed.stat().st_size} bytes)")
    print(f"Installed runtime folder: {bundle}")


if __name__ == "__main__":
    main()
