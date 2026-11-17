# SPDX-License-Identifier: Apache-2.0
LOCAL_PATH := $(call my-dir)

ifeq ($(TARGET_DEVICE),porsche)
# The A17 extractor emits Lineage's SHA-1-checked firmware helper. Calcite only
# defines add-radio-file, so an undefined helper silently omitted every radio
# image from the OTA. Keep the generated vendor files and their integrity checks
# and register the verified files with AOSPA's native packaging mechanism.
ifndef add-radio-file-sha1-checked
define add-radio-file-sha1-checked
$(if $(filter $(2),$(word 1,$(shell sha1sum $(LOCAL_PATH)/$(1)))),\
  $(call add-radio-file,$(1)),\
  $(error Porsche firmware checksum mismatch: $(LOCAL_PATH)/$(1)))
endef
endif

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
