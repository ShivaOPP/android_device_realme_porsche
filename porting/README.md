# Porsche / AOSPA calcite port

This workspace targets AOSPA `calcite`, confirmed from the synced manifest and
build system as Android 17 (`android-17.0.0_r1`, release configuration `cp2a`).
The registered product is `aospa_porsche`, with
`vendor/aospa/products/porsche/aospa_porsche.mk` as its product makefile.
The port is being validated; it has not been boot-tested.

## Source ownership

The booting Android 17 Porsche device reference at
`device/realme/porsche-a17-ref` and SM8350 common tree supply device identity,
partition geometry, fstab, properties, overlays, init, kernel configuration and
HAL selections. The original AOSPA uvite device files remain in Git history and
unselected reference files. AOSPA-specific resources, product inheritance and
vendor hooks are preserved and translated to calcite.

`sources.json` records inspected upstream baselines. Every edited repository
uses a local `a17-port` branch; these branches have not been pushed. Upstream
dependency revisions bootstrap the sources and do **not** contain this local
port. Reproducing the port requires applying the local commits in all edited
repositories, including `vendor/aospa`.

| Android 14 path | Active Android 17 path / ownership |
| --- | --- |
| `device/realme/porsche` standalone configuration | `device/realme/porsche` plus `device/oneplus/sm8350-common` |
| `vendor/realme/porsche` within Realme monorepo | Separate `vendor/realme/porsche` plus `vendor/oneplus/sm8350-common` |
| `hardware/oplus` AOSPA uvite | PixelOS-AOSP seventeen at `hardware/oplus`; original at `hardware/oplus-a14-ref` |
| `vendor/oplus/camera` ThankYouMario uvite-porsche | NoPrincessHere seventeen at `vendor/oplus/camera`; original at `vendor/oplus/camera-a14-ref` |
| `kernel/msm-5.4` | `kernel/oneplus/sm8350`; original kernel retained |
| In-tree DolbyManager and old Dolby blobs | `hardware/dolby`, `seventeen-hidl` |
| In-tree sensors / vibrator | Android 17 `hardware/oplus` implementations |
| uvite QCOM audio/display/GPS/media branches | AOSPA calcite-888 / calcite-legacy-component branches at the same active paths |
| uvite NXP HAL repositories | Calcite manifest's `hardware/nxp/nfc/snxxx` AIDL NFC service; old repositories at `*-a14-ref` |

The active A17 vendor blobs come from RMX3312 Android 15
`RMX3312_15.0.0.1670(EX01)` and the A17 common vendor baseline. The reference
product identity is RMX3312 / RE58B2L1, with fingerprint
`realme/RMX3312/RE58B2L1:15/AP3A.240617.008/S.242fe81-7fc3-7fc2:user/release-keys`.
This is a vendor/reference identity, not a claim that the platform is Android 15.

Verified partition geometry: super `11190403072`, dynamic group `11186208768`,
boot and vendor_boot `201326592`, dtbo `25165824`, block size `262144` bytes.
Boot header version is 3. Vendor, ODM and vendor_dlkm use EROFS. The dynamic
group contains odm, product, system, system_ext, vendor and vendor_dlkm.
The Porsche DTS contains project 21617; the port does not invent a numeric
mapping for the bootloader's `ro.boot.prjname`.

## Dependencies

[`../porsche.dependencies`](../porsche.dependencies) is valid JSON describing
device dependencies. AOSPA's native dependency mechanism is instead
`vendor/aospa/products/porsche/beans.xml`, which includes `platforms/lahaina.xml`.
[`porsche.xml`](porsche.xml) is the flattened local-manifest equivalent for a
fresh checkout. Its remote names are supplied by AOSPA's manifest. The base
manifest already supplies the framework, QCOM interfaces, WLAN, NXP NFC and
other platform projects; these are not redundantly cloned as device repos.

Do not install this manifest over the current standalone Git checkouts. Lunch
uses `AOSPA_SKIP_DEPENDENCIES=true` to protect their local port branches.
The current `.repo/local_manifests/zz-existing-aospa.xml` also protects the
existing standalone `vendor/aospa` checkout from Repo replacement.

## Build commands

The host's `/usr/local/bin/repo` wrapper silently injects shallow init and
different sync jobs. The function below bypasses it. Init itself has no shallow
option. The user's later permission permits shallow **platform sync** projects;
manually cloned device/reference repositories retain full history.

```bash
cd /home/ubuntu/rom
repo() { /usr/local/lib/repo/repo-real "$@"; }

# For a new source checkout only; the current checkout is already initialized.
repo init -u https://github.com/AOSPA/manifest -b calcite
repo sync --current-branch --no-tags -j48

# Use the existing local a17-port repositories.
export AOSPA_SKIP_DEPENDENCIES=true
source build/envsetup.sh
lunch aospa_porsche-userdebug
# Explicit release form is also supported:
# lunch aospa_porsche-cp2a-userdebug
m nothing
m -j16 otapackage
```

Retry a failed sync with exactly the same sync command. The `-j16` above only
controls build compilation, not Repo sync. A full ROM build may require more
disk than the current free space after generated objects grow.

## Validation and TODO(porsche)

`audit-blobs.py` checks inventory file presence and generated install rules for
2424 selected blobs. The radio makefile hashes also match all 23 tracked A17
firmware images. This establishes source coverage, **not** ELF symbol closure,
VINTF compatibility or boot success. Keep Soong's ELF checks and SELinux
neverallows enabled.

The standalone selected kernel has compiled its Image, all 88 modules, three
Porsche DTBs and two Porsche DTBOs with Clang r563880c. Every A17 normal and
recovery module load-list entry exists. `kernel-validation.json` records the
outputs. A two-entry DTBO packing check fits the verified 24 MiB partition.
This does not establish correctness of the shared ROM image packing recipes.

The common tree exports real kernel UAPI installed from the selected kernel,
including camera, audio and display headers. `kernel-headers.json` records their
hashes and provenance; regenerate them with
`python3 device/oneplus/sm8350-common/regenerate-kernel-headers.py` after relevant
kernel changes. Raw original headers and the kernel COPYING file are retained.

The A17 reference owns fingerprint, NFC/eSE, camera, audio, display, sensors,
telephony/GPS and HIDL Dolby selections. None is intentionally removed. AOSPA's
charging interface supplies the equivalent Lineage interface, settings apps use
`co.aospa.resources`, and the UDFPS library uses calcite's actual SurfaceFlinger
configuration variable. HIDL services are retained where the primary reference
and proprietary interfaces require them.

Remaining work is tracked by the current build log `.repo/porsche-build.log`.
Soong graph generation has passed; Kati, userspace module compilation,
SELinux/VINTF, integrated images and a ROM build still need to finish before this is
a flashable candidate. In particular:

- The shared kernel/image recipes evaluate DTB/DTBO file discovery while Kati
  generates Ninja, before a clean kernel build. A fix is prepared in
  `patches/calcite-runtime-device-trees.patch`; applying it to
  `device/qcom/common` and `device/qcom/kernelscripts` awaits permission because
  the original directory restriction excludes those repositories.
- Porsche now declares the verified complete 88-module inventory early, copies
  six recovery modules into vendor_boot, and preserves the WLAN filename alias.
  Verify these integrated image rules after Kati passes. Regenerate the inventory
  after a relevant kernel configuration change with
  `python3 device/oneplus/sm8350-common/record-kernel-modules.py KERNEL_OUT`.
- Keep the modern AIDL NFC service together with the reference HIDL eSE
  declarations and verify the merged VINTF manifest, matrices and policy.
- `resource-migrations.json` records obsolete uvite resources. The dedicated
  OEM fast-charge status resource has no calcite equivalent; battery speed is
  calculated from health HAL wattage. Keep this runtime indication on the list
  for validation. Secure NFC uses the current device capability resource.
- Compile the retained AOSPA overlays against calcite resources and validate
  fingerprint brightness/press behavior, charging, suspend and Dolby service
  compatibility during eventual runtime testing.
- `android17-overrides.json` lists verified differences from uvite. A17 values
  win; old init, thermal, IRQ, WLAN and partition prop files are unselected.

Needs device confirmation, without blocking source work:

- The common userdata size `237598617600` is for the 256 GB variant. The 128 GB
  userdata image size is unverified. OTA images do not include userdata.
- Preserve the actual bootloader `ro.boot.prjname`. No new numeric value is
  hardcoded based only on the DTS project ID.

## Disk cleanup and reference recovery

`disk-cleanup.json` records reversible sparse checkout of unrelated devices from
the old Realme vendor worktree (about 5.15 GiB), and cleanup of abandoned platform
sync packs / permitted shallow platform history. Active Porsche, common,
camera and Dolby blobs are retained. Restore the reference worktrees with:

```bash
git -C vendor/realme-a14-ref sparse-checkout disable
git -C vendor/realme-a17-ref/porsche sparse-checkout disable
```

`.find-ignore` markers keep preserved reference repositories out of both Soong
and Make scanning. Remove those markers only when intentionally reactivating a
reference. Their original branches and full Git history remain available.
