"""Read-only, bounded War Thunder installation and user-content discovery.

Only inspect common Windows folders and Steam's local library manifest. Do not
scan disks, start War Thunder, modify game files, or transmit discovered paths.
Manual folder selection remains available when no unique location is found.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Mapping


_MAX_STEAM_VDF = 256 * 1024
_MAX_STEAM_LIBRARIES = 20
_MAX_SAVE_PROFILES = 64
_MAX_SKIN_TEMPLATES = 64


def _unique_paths(paths):
    found = set()
    result = []
    for value in paths:
        path = Path(value).expanduser()
        # Avoid resolving links: this feature only suggests destinations and
        # the installer itself rejects symlinked write paths.
        key = str(path).casefold()
        if key not in found:
            found.add(key)
            result.append(path)
    return result


def _steam_libraries(steam_dir: Path):
    """Read Steam's own manifest without walking the user's drive."""
    yield steam_dir
    manifest = steam_dir / "steamapps" / "libraryfolders.vdf"
    try:
        if manifest.is_symlink() or manifest.stat().st_size > _MAX_STEAM_VDF:
            return
        content = manifest.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return

    # Steam writes path values as quoted VDF strings. Only the explicit path
    # property is used; no path from the manifest is executed.
    matches = re.findall(r'"path"\s*"([^"\r\n]+)"', content, re.I)
    for value in matches[:_MAX_STEAM_LIBRARIES]:
        decoded = value.replace("\\\\", "\\").strip()
        if decoded:
            yield Path(decoded)


def _valid_root(folder: Path) -> bool:
    """A plausible root has a regular config.blk, not a symlink."""
    try:
        config = folder / "config.blk"
        return (
            folder.is_dir() and not folder.is_symlink()
            and config.is_file() and not config.is_symlink()
        )
    except OSError:
        return False


def find_game_roots(
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> tuple[Path, ...]:
    """Find existing Steam or native installations with no registry/network I/O.

    This is a suggestion, not proof that the installation is healthy or that a
    mod is compatible. A custom install location can always be chosen manually.
    """
    env = os.environ if environ is None else environ
    user_home = Path.home() if home is None else Path(home)
    steam_dirs = []
    native = []
    for key in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        base = env.get(key)
        if not base:
            continue
        parent = Path(base)
        steam_dirs.append(parent / "Steam")
        native.extend((
            parent / "War Thunder",
            parent / "WarThunder",
            parent / "Gaijin" / "War Thunder",
        ))
    steam_dirs.append(user_home / "Steam")
    native.extend((user_home / "Games" / "WarThunder", user_home / "Games" / "War Thunder"))

    candidates = list(native)
    for steam in _unique_paths(steam_dirs):
        for library in _steam_libraries(steam):
            candidates.extend((
                library / "steamapps" / "common" / "War Thunder",
                library / "steamapps" / "common" / "WarThunder",
            ))

    return tuple(root for root in _unique_paths(candidates) if _valid_root(root))


def find_sight_folders(
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> tuple[Path, ...]:
    """Find existing production/UserSights locations under known Documents."""
    env = os.environ if environ is None else environ
    user_home = Path.home() if home is None else Path(home)
    documents = [user_home / "Documents"]
    if env.get("OneDrive"):
        documents.append(Path(env["OneDrive"]) / "Documents")
    if env.get("OneDriveCommercial"):
        documents.append(Path(env["OneDriveCommercial"]) / "Documents")

    result = []
    for docs in _unique_paths(documents):
        saves = docs / "My Games" / "WarThunder" / "Saves"
        if not saves.is_dir() or saves.is_symlink():
            continue
        try:
            profiles = sorted(saves.iterdir(), key=lambda p: p.name.casefold())
        except OSError:
            continue
        locations = [saves / "production"]
        locations += [profile / "production" for profile in profiles[:_MAX_SAVE_PROFILES]
                      if profile.is_dir() and not profile.is_symlink()]
        for production in locations:
            if not production.is_dir() or production.is_symlink():
                continue
            sights = production / "UserSights"
            if sights.is_symlink():
                continue
            result.append(sights if sights.is_dir() else production)
    return tuple(_unique_paths(result))


def find_skin_templates(game_root: Path) -> tuple[Path, ...]:
    """List existing vehicle templates only; never create or overwrite them."""
    root = Path(game_root)
    if not _valid_root(root):
        return ()
    user_skins = root / "UserSkins"
    if not user_skins.is_dir() or user_skins.is_symlink():
        return ()
    try:
        entries = sorted(user_skins.iterdir(), key=lambda p: p.name.casefold())
    except OSError:
        return ()
    return tuple(
        path for path in entries[:_MAX_SKIN_TEMPLATES]
        if path.name.lower().startswith("template_")
        and path.is_dir() and not path.is_symlink()
    )
