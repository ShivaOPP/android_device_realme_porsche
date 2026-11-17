#!/usr/bin/env python3
"""Check real compiled DSP permissions without weakening platform policy tests."""

import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=root)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root / "system/sepolicy/tests"))
    import policy

    binary = root / "out/soong/.intermediates/system/sepolicy/precompiled_sepolicy/android_common/porsche/precompiled_sepolicy"
    library = root / "out/soong/.intermediates/system/sepolicy/tests/libsepolwrap/linux_glibc_x86_64_shared/libsepolwrap.so"
    compiled = policy.Policy(str(binary), [], str(library))
    checks = []

    def check(source, target, object_class, required, forbidden=()):
        rules = list(compiled.QueryTERule(
            scontext={source}, tcontext={target}, tclass={object_class}))
        actual = set().union(*(r.perms for r in rules))
        checks.append({
            "source": source, "target": target, "class": object_class,
            "required": sorted(required), "forbidden": sorted(forbidden),
            "actual": sorted(actual),
            "pass": set(required) <= actual and not (set(forbidden) & actual),
        })

    # CLO's original client grants include bidirectional Binder/FD and buffers.
    for source, target in [
        ("isolated_compute_app", "vendor_dspservice"),
        ("vendor_dspservice", "isolated_compute_app"),
    ]:
        check(source, target, "binder", {"call", "transfer"})
        check(source, target, "fd", {"use"})
        check(source, target, "memfd_file", {"read", "write", "getattr", "map"})

    for target, manager in [
        ("vendor_hal_dspmanager_hwservice", "hwservice_manager"),
        ("vendor_hal_dspmanager_aidlservice", "service_manager"),
    ]:
        check("isolated_compute_app", target, manager, set(), {"find"})
        # Normal app clients must retain CLO's service discovery behavior.
        check("untrusted_app", target, manager, {"find"})

    result = {
        "policy": str(binary.relative_to(root)),
        "sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "pass": all(c["pass"] for c in checks),
        "checks": checks,
        "limit": "Compiled permissions only; DSP handle delivery still needs runtime testing.",
    }
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
