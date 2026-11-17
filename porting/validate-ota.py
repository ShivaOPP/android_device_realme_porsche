#!/usr/bin/env python3
"""Check the final OTA partition inventory and primary A17 radio payload hashes."""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import zipfile


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path, padding=0):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    require(0 <= padding < 4096, f"Unexpected firmware padding: {path}: {padding}")
    value.update(b"\0" * padding)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ota", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    ota = args.ota.resolve()
    product = root / "out/target/product/porsche"
    target = product / "obj/PACKAGING/target_files_intermediates/aospa_porsche-target_files"
    tools = root / "out/host/linux-x86/bin"
    expected = set((target / "META/ab_partitions.txt").read_text().split())
    dynamic = dict(line.split("=", 1) for line in
                   (target / "META/dynamic_partitions_info.txt").read_text().splitlines()
                   if "=" in line)
    with zipfile.ZipFile(ota) as package:
        metadata_proto = package.read("META-INF/com/android/metadata.pb")
        metadata = dict(line.split("=", 1) for line in
                        package.read("META-INF/com/android/metadata").decode().splitlines()
                        if "=" in line)
        require(metadata.get("ota-type") == "AB", "OTA is not A/B")
        aliases = set(metadata.get("pre-device", "").split("|"))
        identity = re.search(r"^ro.product.system.device=(.+)$",
                             (target / "SYSTEM/build.prop").read_text(), re.M).group(1)
        require(aliases == {identity},
                "OTA assertion differs from the generated primary A17 device identity")
        with package.open("payload.bin") as payload:
            magic, version, length = struct.unpack(">4sQQ", payload.read(20))
            require(magic == b"CrAU" and version == 2, "Unexpected payload header")
            payload.read(4)  # Metadata-signature length, part of the v2 header.
            require(length < 128 * 1024 * 1024, "Unexpected manifest size")
            manifest = payload.read(length)
            require(len(manifest) == length, "Truncated payload manifest")
    decoded_metadata = subprocess.check_output([
        str(tools / "aprotoc"), "--decode=build.tools.releasetools.OtaMetadata",
        "--proto_path=build/make/tools/releasetools", "ota_metadata.proto",
    ], input=metadata_proto, cwd=root).decode()
    for state in ["precondition", "postcondition"]:
        block = re.search(rf"^{state} \{{\n(.*?)^\}}", decoded_metadata, re.M | re.S).group(1)
        devices = set(re.findall(r'^  device: "([^"]+)"$', block, re.M))
        require(devices == {identity}, f"Protobuf {state} device identity mismatch")
    decoded = subprocess.check_output([
        str(tools / "aprotoc"), "--decode=chromeos_update_engine.DeltaArchiveManifest",
        "--proto_path=system/update_engine", "update_metadata.proto",
    ], input=manifest, cwd=root).decode()
    partitions = {}
    for block in re.findall(r"^partitions \{\n(.*?)^\}", decoded, re.M | re.S):
        name = re.search(r'^  partition_name: "([^"]+)"$', block, re.M).group(1)
        info = re.search(r"^  new_partition_info \{\n(.*?)^  \}", block, re.M | re.S).group(1)
        size = int(re.search(r"size: (\d+)", info).group(1))
        raw_hash = re.search(r'hash: (".*")', info).group(1)
        checksum = ast.literal_eval("b" + raw_hash).hex()
        require(name not in partitions, f"Duplicate payload partition: {name}")
        partitions[name] = {"bytes": size, "sha256": checksum}
    require(set(partitions) == expected, "Payload partition list differs from A/B configuration")
    require("userdata" not in partitions, "OTA must not carry SKU-specific userdata image")
    group_text = re.search(r"^dynamic_partition_metadata \{\n(.*?)^\}", decoded, re.M | re.S).group(1)
    groups = re.findall(r"^  groups \{\n(.*?)^  \}", group_text, re.M | re.S)
    require(len(groups) == 1, "Unexpected dynamic partition groups")
    group_name = re.search(r'name: "([^"]+)"', groups[0]).group(1)
    group_size = int(re.search(r"size: (\d+)", groups[0]).group(1))
    group_parts = set(re.findall(r'partition_names: "([^"]+)"', groups[0]))
    require(group_name == dynamic["super_partition_groups"], "Dynamic group name mismatch")
    require(group_size == int(dynamic[f"super_{group_name}_group_size"]), "Dynamic group size mismatch")
    require(group_parts == set(dynamic["dynamic_partition_list"].split()), "Dynamic partition membership mismatch")
    require(sum(partitions[name]["bytes"] for name in group_parts) <= group_size,
            "Payload exceeds dynamic group capacity")
    vendor = root / "vendor/realme/porsche"
    radio = dict(re.findall(r"add-radio-file-sha1-checked,radio/([^,]+),([0-9a-f]+)",
                            (vendor / "Android.mk").read_text()))
    require(len(radio) == 23, "Unexpected primary firmware inventory")
    for filename, original_sha1 in radio.items():
        source = vendor / "radio" / filename
        packed = target / "RADIO" / filename
        require(hashlib.sha1(packed.read_bytes()).hexdigest() == original_sha1,
                f"Staged firmware SHA-1 mismatch: {filename}")
        entry = partitions[filename.removesuffix(".img")]
        require(digest(source, entry["bytes"] - source.stat().st_size) == entry["sha256"],
                f"OTA firmware SHA-256 mismatch: {filename}")
    certificate = root / "build/make/target/product/security/testkey.x509.pem"
    signature = subprocess.run([str(tools / "check_ota_package_signature"),
                                str(certificate), str(ota)], cwd=root,
                               capture_output=True, check=True)
    log = root / ".repo/porsche-ota-signature-final.log"
    log.write_bytes(signature.stdout + signature.stderr)
    result = {
        "pass": True, "ota": str(ota.relative_to(root)), "bytes": ota.stat().st_size,
        "sha256": digest(ota), "signature": "PASS, native verifier with actual build test certificate",
        "metadata": metadata, "protobuf_device_assertions": identity,
        "payload_major_version": version,
        "partitions": partitions, "payload_matches_ab_partition_list": True,
        "userdata_in_payload": False, "primary_radio_images_verified": len(radio),
        "radio_payload_sha256_matches_primary": True,
        "dynamic_group": {"name": group_name, "bytes": group_size,
                          "partitions": sorted(group_parts)},
        "scope": "Signed OTA integrity and partition/firmware consistency; no hardware boot test.",
    }
    output = args.output or Path(__file__).with_name("ota-validation.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"PASS: signed OTA; {len(partitions)} A/B partitions; {len(radio)} primary firmware hashes; no userdata")


if __name__ == "__main__":
    main()
