"""Build a single WT Mod Manager executable on Windows (PyInstaller)."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
import PyInstaller.__main__


ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "assets" / "icons" / "Logotip" / "LogotipProject.png"
ICON = ROOT / "build" / "WTModManager.ico"


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("Windows executable must be built on Windows.")

    required = [ROOT / "src" / "main.py", ROOT / "assets", ROOT / "config", LOGO]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("Missing required project resources: " + ", ".join(missing))

    ICON.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(LOGO) as logo:
        logo.convert("RGBA").save(
            ICON, format="ICO", sizes=[(16, 16), (32, 32), (48, 48),
                                      (64, 64), (128, 128), (256, 256)]
        )

    PyInstaller.__main__.run([
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name=WTModManager",
        "--paths=" + str(ROOT),
        "--icon=" + str(ICON),
        "--add-data=" + str(ROOT / "assets") + ":assets",
        "--add-data=" + str(ROOT / "config") + ":config",
        "--distpath=" + str(ROOT / "dist"),
        "--workpath=" + str(ROOT / "build" / "pyinstaller"),
        "--specpath=" + str(ROOT / "build"),
        str(ROOT / "src" / "main.py"),
    ])

    exe = ROOT / "dist" / "WTModManager.exe"
    if not exe.is_file() or exe.stat().st_size == 0:
        raise SystemExit("Build finished without a usable EXE at " + str(exe))
    print(f"Created {exe} ({exe.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
