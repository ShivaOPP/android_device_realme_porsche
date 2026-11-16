#!/usr/bin/env python3
"""Check the selected blob inventories against files and install declarations.

This checks source coverage. Soong's ELF and VINTF checks are still required for
link and interface compatibility; a source coverage pass does not prove boot.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ANDROID_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ANDROID_ROOT / "tools/extract-utils"))
from extract_utils.file import File, FileArgs


INVENTORIES = (
    ("device/realme/porsche/proprietary-files.txt", "vendor/realme/porsche"),
    (
        "device/oneplus/sm8350-common/proprietary-files.txt",
        "vendor/oneplus/sm8350-common",
    ),
    ("vendor/oplus/camera/proprietary-files.txt", "vendor/oplus/camera"),
    ("hardware/dolby/proprietary-files.txt", "hardware/dolby"),
)


def install_sources(vendor_root: Path) -> set[str]:
    sources: set[str] = set()
    for blueprint in vendor_root.rglob("Android.bp"):
        for src in re.findall(r'"(proprietary/[^"\n]+)"', blueprint.read_text()):
            sources.add(str((blueprint.parent / src).relative_to(vendor_root)))
    for makefile in vendor_root.glob("*.mk"):
        for src in re.findall(r"([^\s\\]+/proprietary/[^\s\\:]+):", makefile.read_text()):
            full = ANDROID_ROOT / src
            if full.is_relative_to(vendor_root):
                sources.add(str(full.relative_to(vendor_root)))
    return sources


def audit_inventory(inventory: str, vendor: str) -> dict:
    listing = ANDROID_ROOT / inventory
    vendor_root = ANDROID_ROOT / vendor
    if not listing.is_file():
        return {"inventory": inventory, "missing_inventory": True}
    installed = install_sources(vendor_root)
    entries = 0
    missing_files = []
    missing_install_rules = []
    for line_number, line in enumerate(listing.read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        blob = File(line)
        entries += 1
        relative = "proprietary/" + blob.dst
        location = {"line": line_number, "path": blob.dst}
        if not (vendor_root / relative).is_file():
            missing_files.append(location)
        if relative not in installed and FileArgs.EXTRACT_ONLY not in blob.args:
            missing_install_rules.append(location)
    return {
        "inventory": inventory,
        "vendor_root": vendor,
        "entries": entries,
        "missing_files": missing_files,
        "missing_install_rules": missing_install_rules,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    results = [audit_inventory(*entry) for entry in INVENTORIES]
    ok = all(
        not result.get("missing_inventory")
        and not result["missing_files"]
        and not result["missing_install_rules"]
        for result in results
    )
    report = {
        "source_coverage_passed": ok,
        "link_and_vintf_compatibility": "requires Soong build checks",
        "inventories": results,
    }
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    for result in results:
        print(
            result["inventory"],
            "entries=" + str(result.get("entries", 0)),
            "missing_files=" + str(len(result.get("missing_files", []))),
            "missing_install_rules=" + str(len(result.get("missing_install_rules", []))),
        )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
