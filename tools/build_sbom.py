"""Generate a minimal CycloneDX 1.5 SBOM from the actual build environment.

This is package inventory provenance, not a vulnerability-free guarantee.
No paths, private environment variables or API tokens are written to SBOM.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.metadata
import json
import re
from pathlib import Path

NAME = re.compile(r"^[a-zA-Z0-9_.-]{1,120}$")
VERSION = re.compile(r"^[a-zA-Z0-9_.!+~-]{1,100}$")


def inventory(distributions=None) -> dict:
    components = []
    seen = set()
    for dist in (distributions if distributions is not None
                 else importlib.metadata.distributions()):
        name = str(dist.metadata.get("Name", "")).strip()
        version = str(dist.version).strip()
        if not NAME.fullmatch(name) or not VERSION.fullmatch(version):
            continue
        normalized = name.lower().replace("_", "-").replace(".", "-")
        if (normalized, version) in seen:
            continue
        seen.add((normalized, version))
        components.append({
            "type": "library",
            "name": name,
            "version": version,
            "purl": f"pkg:pypi/{normalized}@{version}",
        })
    components.sort(key=lambda entry: (entry["name"].lower(), entry["version"]))
    if not components:
        raise ValueError("Cannot produce an empty dependency inventory.")
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(
                timespec="seconds"
            ),
            "tools": [
                {"vendor": "WT Mod Manager", "name": "Local Python SBOM",
                 "version": "1"},
            ],
            "component": {"type": "application", "name": "WT Mod Manager"},
        },
        "components": components,
    }


def validate_sbom(data: dict) -> int:
    if (not isinstance(data, dict) or data.get("bomFormat") != "CycloneDX"
            or data.get("specVersion") != "1.5"):
        raise ValueError("Invalid CycloneDX metadata.")
    components = data.get("components")
    if not isinstance(components, list) or not 3 <= len(components) <= 1500:
        raise ValueError("Unexpected number of Python components.")
    if not {"pyside6", "pillow", "psutil", "pyinstaller"}.issubset({
        c.get("name", "").lower() for c in components
    }):
        raise ValueError("Build's required dependencies are missing from SBOM.")
    return len(components)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("create", "verify"))
    parser.add_argument("--output", type=Path, default=Path("dist/sbom.cdx.json"))
    args = parser.parse_args()
    if args.command == "create":
        obj = inventory()
        validate_sbom(obj)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    loaded = json.loads(args.output.read_text(encoding="utf-8"))
    print("CycloneDX Python components: " + str(validate_sbom(loaded)))


if __name__ == "__main__":
    main()
