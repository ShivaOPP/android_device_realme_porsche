# SPDX-License-Identifier: Apache-2.0
LOCAL_PATH := $(call my-dir)

ifeq ($(TARGET_DEVICE),porsche)
include $(call all-makefiles-under,$(LOCAL_PATH))

# TODO(porsche): the A17 common/vendor trees and AOSPA QCOM common install the
# ACDB, firmware and RFS symlinks. Do not race those modules with uvite's directory
# recipes (which cleared their contents). The originals remain in Git history.

# Calcite's kernel builder does not consume Lineage TARGET_MODULE_ALIASES.
# Match the verified A17 alias without changing the driver's firmware behavior.
$(KERNEL_MODULES_OUT)/qca_cld3_wlan.ko: $(PRODUCT_OUT)/kernel
	cp $(KERNEL_MODULES_OUT)/wlan.ko $@

# These files are produced by the complete kernel build before image packaging.
$(filter-out $(KERNEL_MODULES_OUT)/qca_cld3_wlan.ko,$(BOARD_VENDOR_KERNEL_MODULES)): $(PRODUCT_OUT)/kernel
endif
