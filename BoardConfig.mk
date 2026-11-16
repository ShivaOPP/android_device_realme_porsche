#
# Copyright (C) 2023 Paranoid Android
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/realme/porsche
include build/make/target/board/BoardConfigMainlineCommon.mk
include device/oneplus/sm8350-common/BoardConfigCommon.mk

# Porsche geometry matches the verified A17 device/common tree.
# TODO(porsche): uvite added ttyMSM0 console arguments; the booting A17 base does not.
BOARD_BOOTIMAGE_PARTITION_SIZE := 0xC000000
BOARD_VENDOR_BOOTIMAGE_PARTITION_SIZE := 0xC000000
BOARD_DTBOIMG_PARTITION_SIZE := 0x1800000
BOARD_FLASH_BLOCK_SIZE := 262144
# TODO(porsche): uvite used 131072; A17 common uses 4096 * 64.
BOARD_SUPER_PARTITION_SIZE := 11190403072
# The matching A17 Porsche tree reserves 4 MiB of super for metadata.
# The uvite value reserved 4,000,000 bytes; use the verified A17 value.
BOARD_ONEPLUS_DYNAMIC_PARTITIONS_SIZE := 11186208768

# Both bases use boot header v3, DTB in boot and a separate DTBO image.
KERNEL_DEFCONFIG := vendor/lahaina-qgki_defconfig
TARGET_KERNEL_CONFIG := $(KERNEL_DEFCONFIG)
# TODO(porsche): uvite required an external clang-standalone checkout. Use the
# verified A17 r563880c toolchain shipped in calcite's clang prebuilts instead.
KERNEL_CUSTOM_LLVM := false
KERNEL_FULL_LLVM := true

# AOSPA hooks are still consumed by calcite's BoardConfigSoong.mk.
TARGET_INIT_VENDOR_LIB := //$(DEVICE_PATH):libinit_porsche
TARGET_SURFACEFLINGER_UDFPS_LIB := //hardware/oplus:libudfps_extension.oplus
TARGET_POWER_FEATURE_EXT_LIB := //$(DEVICE_PATH):libpowerfeature_ext_porsche
TARGET_HEALTH_CHARGING_CONTROL_CHARGING_PATH := /sys/class/oplus_chg/battery/mmi_charging_enable

TARGET_OTA_ASSERT_DEVICE := RMX3312,RE58B2L1
TARGET_RECOVERY_FSTAB := $(DEVICE_PATH)/init/fstab.default
TARGET_RECOVERY_UI_MARGIN_HEIGHT := 103
TARGET_SCREEN_DENSITY := 450
# TODO(porsche): prefer the booting A17 density (uvite used 480).

# TODO(porsche): the booting A17 common tree specifies the 256 GB userdata
# geometry. A 128 GB SKU still needs confirmation before building a userdata image.

# TODO(porsche): only A17 per-device properties are active; uvite partition
# property files remain available for cross-checking in this repository.
TARGET_VENDOR_PROP += $(DEVICE_PATH)/vendor.prop

BOARD_VENDOR_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/vendor
SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/private
SYSTEM_EXT_PUBLIC_SEPOLICY_DIRS += $(DEVICE_PATH)/sepolicy/public
include vendor/realme/porsche/BoardConfigVendor.mk
