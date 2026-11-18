
"""WT Mod Manager: original PNG assets, automatically chosen for Qt theme.

Directory layout:
    assets/icons/White/name.png
    assets/icons/Black/name.png
    assets/icons/Logotip/LogotipProject.png
"""

from pathlib import Path
from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from ui.theme_engine import effective_mode

ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = ROOT / "assets" / "icons"


# For dark UI use WHITE icons;
# for light UI use BLACK icons.
def icon_path(name, settings):
    if name not in {
        "sounds",
        "camouflages",
        "reset",
        "settings",
        "sights",
        "configurations",
        "play",
        "pause",
        "stop"
    }:
        return None

    folder = (
        "Black"
        if effective_mode(settings) == "white"
        else "White"
    )

    filename = ICONS_DIR / folder / (name + ".png")
    return filename if filename.is_file() else None


def icon_for(name, settings):
    path = icon_path(name, settings)
    return QIcon(str(path)) if path else QIcon()


def apply_icon(button, name, settings, size=19):
    button.setIcon(icon_for(name, settings))
    button.setIconSize(QSize(size, size))
    return button


# Main application logo
def application_logo_icon():
    path = (
        ICONS_DIR
        / "Logotip"
        / "LogotipProject.png"
    )

    return QIcon(str(path)) if path.is_file() else QIcon()
