#!/usr/bin/env python3
"""Validate generated Porsche images against their actual kernel and A17 inputs."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, description):
    if not condition:
        raise RuntimeError(description)


def module_dependencies(text, available, label):
    graph = {}
    for line in text.splitlines():
        name, dependencies = line.split(":", 1)
        graph[Path(name).name] = {Path(item).name for item in dependencies.split()}
    require(set(graph) == available, f"{label} depmod inventory differs from packed modules")
    for name, dependencies in graph.items():
        require(dependencies <= available, f"{label} dependencies missing for {name}")
    return graph


def cpio(data):
    files = {}
    offset = 0
    while offset + 110 <= len(data):
        magic = data[offset:offset + 6]
        require(magic in (b"070701", b"070702"), f"Invalid CPIO at {offset}")
        fields = [int(data[offset + 6 + i * 8:offset + 14 + i * 8], 16)
                  for i in range(13)]
        size, name_size = fields[6], fields[11]
        name = data[offset + 110:offset + 110 + name_size - 1].decode()
        offset = (offset + 110 + name_size + 3) & ~3
        contents = data[offset:offset + size]
        require(len(contents) == size, f"Truncated CPIO entry {name}")
        offset = (offset + size + 3) & ~3
        if name == "TRAILER!!!":
            while offset < len(data) and data[offset] == 0:
                offset += 1
            if offset == len(data):
                break
            continue
        files[name.removeprefix("./")] = contents
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    product = root / "out/target/product/porsche"
    kernel = product / "obj/kernel/oneplus/sm8350"
    common = root / "device/oneplus/sm8350-common"
    tools = root / "out/host/linux-x86/bin"
    # Keep validation artifacts for inspection. Do not clear existing outputs.
    scratch = Path(tempfile.mkdtemp(prefix="porsche-image-validation-", dir=root / ".repo"))

    def run(tool, *arguments):
        return subprocess.check_output([str(tools / tool), *map(str, arguments)])

    boot_dir, vendor_dir = scratch / "boot", scratch / "vendor_boot"
    boot_header = run("unpack_bootimg", "--boot_img", product / "boot.img", "--out", boot_dir)
    vendor_header = run("unpack_bootimg", "--boot_img", product / "vendor_boot.img", "--out", vendor_dir)
    (scratch / "boot-header.txt").write_bytes(boot_header)
    (scratch / "vendor-boot-header.txt").write_bytes(vendor_header)
    require(b"boot image header version: 3" in boot_header, "Boot header must be v3")
    require(b"vendor boot image header version: 3" in vendor_header, "Vendor boot header must be v3")
    require(b"androidboot.hardware=qcom" in vendor_header, "Missing verified hardware cmdline")
    boot = cpio(run("lz4", "-d", "-c", boot_dir / "ramdisk"))
    vendor = cpio(run("lz4", "-d", "-c", vendor_dir / "vendor_ramdisk"))
    require(boot.get("init", b"").startswith(b"\x7fELF"), "Boot ramdisk has no ELF init")
    fstabs = {name: data for name, data in vendor.items() if name.endswith("fstab.qcom")}
    require("first_stage_ramdisk/system/etc/fstab.qcom" in fstabs, "First-stage fstab missing")
    require(all(data == (common / "init/fstab.default").read_bytes() for data in fstabs.values()),
            "Packed fstab differs from primary A17 source")
    expected_boot = set((common / "modules.include.recovery").read_text().split())
    packed_boot = {Path(name).name: data for name, data in vendor.items() if name.endswith(".ko")}
    require(expected_boot == set(packed_boot), "Boot module inventory mismatch")
    load_lists = {name: data.decode() for name, data in vendor.items() if "modules.load" in name}
    for name, listing in load_lists.items():
        require(set(listing.split()) <= expected_boot, f"Missing boot module in {name}")
    boot_dep = [data.decode() for name, data in vendor.items() if name.endswith("/modules.dep")]
    require(len(boot_dep) == 1, "Expected one boot module dependency graph")
    boot_graph = module_dependencies(boot_dep[0], expected_boot, "vendor_boot")
    extracted = scratch / "vendor_dlkm"
    erofs = subprocess.run([str(tools / "fsck.erofs"), f"--extract={extracted}",
                            str(product / "vendor_dlkm.img")], check=True, capture_output=True)
    (scratch / "vendor-dlkm-fsck.log").write_bytes(erofs.stdout + erofs.stderr)
    modules = {file.name: file.read_bytes() for file in extracted.rglob("*.ko")}
    expected = set((common / "kernel-modules.list").read_text().split())
    require(set(modules) == expected, "vendor_dlkm module inventory mismatch")
    vendor_graph = module_dependencies((extracted / "lib/modules/modules.dep").read_text(),
                                       expected, "vendor_dlkm")
    vendor_load = (extracted / "lib/modules/modules.load").read_text().split()
    require({Path(name).name for name in vendor_load} <= expected,
            "Vendor load list references missing modules")
    release = (kernel / "include/config/kernel.release").read_text().strip()
    for name, data in [*modules.items(), *packed_boot.items()]:
        match = re.search(rb"vermagic=([^\0]+)", data)
        require(match is not None, f"Missing module version: {name}")
        require(match.group(1).decode().split()[0] == release, f"Module ABI mismatch: {name}")
    require("qca_cld3_wlan.ko" in modules, "WLAN alias absent")
    require((boot_dir / "kernel").read_bytes() == (kernel / "arch/arm64/boot/Image").read_bytes(),
            "Packed kernel differs from build")
    dtb = (vendor_dir / "dtb").read_bytes()
    require(dtb == (product / "dtb.img").read_bytes(), "Packed vendor DTB differs from build")
    source_dts = kernel / "arch/arm64/boot/dts/vendor/oplus/porsche"
    dtbs = []
    for file in sorted(source_dts.glob("*.dtb")):
        data = file.read_bytes()
        require(data in dtb, f"Porsche DTB absent: {file.name}")
        dtbs.append({"file": file.name, "bytes": len(data), "sha256": sha(data)})
    require(len(dtbs) == 3, "Expected three verified Porsche DTBs")
    table = (product / "dtbo.img").read_bytes()
    magic, total, header_size, entry_size, count, offset, page, version = struct.unpack_from(
        ">8I", table)
    require(magic == 0xD7B7AB1E and total <= len(table), "Invalid DTBO table")
    payloads = set()
    for i in range(count):
        size, start, *_ = struct.unpack_from(">8I", table, offset + i * entry_size)
        require(start + size <= total, "DTBO entry outside table")
        payloads.add(sha(table[start:start + size]))
    dtbos = []
    for file in sorted(source_dts.glob("*.dtbo")):
        data = file.read_bytes()
        require(sha(data) in payloads, f"Porsche overlay absent: {file.name}")
        dtbos.append({"file": file.name, "bytes": len(data), "sha256": sha(data)})
    require(len(dtbos) == 2, "Expected both Porsche overlays")
    images = []
    for name, limit in [("boot.img", 201326592), ("vendor_boot.img", 201326592),
                        ("dtbo.img", 25165824), ("vendor_dlkm.img", None)]:
        file = product / name
        require(limit is None or file.stat().st_size <= limit, f"Oversized image: {name}")
        images.append({"file": name, "bytes": file.stat().st_size,
                       "partition_limit": limit, "sha256": sha(file.read_bytes())})
    avb = run("avbtool", "info_image", "--image", product / "boot.img").decode()
    spl = re.search(r"^BOOT_SECURITY_PATCH\s*:=\s*(\S+)",
                    (common / "BoardConfigCommon.mk").read_text(), re.M).group(1)
    require(f"security_patch -> '{spl}'" in avb, "AVB boot SPL differs from primary config")
    result = {
        "pass": True, "kernel_release": release, "boot_and_vendor_boot_header_version": 3,
        "kernel_payload_matches_build": True, "vendor_boot_dtb_matches_build": True,
        "fstab_paths": list(fstabs), "fstab_matches_primary_A17": True,
        "boot_modules": sorted(expected_boot), "ramdisk_module_load_lists": load_lists,
        "vendor_dlkm_module_count": len(modules), "all_module_vermagic_matches_kernel": True,
        "vendor_boot_dependency_closure": True, "vendor_dlkm_dependency_closure": True,
        "vendor_boot_depmod_nodes": len(boot_graph),
        "vendor_dlkm_depmod_nodes": len(vendor_graph), "vendor_dlkm_load_count": len(vendor_load),
        "all_boot_module_vermagic_matches_kernel": True, "wlan_alias_present": True,
        "porsche_dtbs": dtbs, "dtbo_table_entries": count, "dtbo_table_bytes": total,
        "porsche_dtbos": dtbos, "images": images, "erofs_check": "PASS, fsck.erofs --extract",
        "avb_boot_security_patch": spl, "avb_boot_security_patch_matches_primary_A17": True,
        "inspection_directory": str(scratch.relative_to(root)),
        "scope": "Generated-image consistency; no device boot or runtime hardware test.",
    }
    output = args.output or Path(__file__).with_name("image-validation.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"PASS: {release}; {len(modules)} vendor_dlkm and {len(packed_boot)} boot modules; "
          f"{len(dtbs)} Porsche DTBs and {len(dtbos)} overlays")


if __name__ == "__main__":
    main()
