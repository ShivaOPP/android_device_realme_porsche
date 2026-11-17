#
# Copyright (C) 2021-2025 The LineageOS Project
#
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/realme/porsche
LOCAL_PATH := $(DEVICE_PATH)

# AAPT
PRODUCT_AAPT_CONFIG := normal
PRODUCT_AAPT_PREF_CONFIG := xxhdpi

# Audio
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/configs/audio/audio_platform_info_intcodec.xml:$(TARGET_COPY_OUT_ODM)/etc/audio_platform_info.xml \
    $(DEVICE_PATH)/configs/audio/audio_platform_info_intcodec.xml:$(TARGET_COPY_OUT_VENDOR)/etc/audio/sku_lahaina/audio_platform_info_intcodec.xml \
    $(DEVICE_PATH)/configs/audio/mixer_paths.xml:$(TARGET_COPY_OUT_ODM)/etc/mixer_paths.xml \
    $(DEVICE_PATH)/configs/audio/mixer_paths.xml:$(TARGET_COPY_OUT_VENDOR)/etc/audio/sku_lahaina/mixer_paths.xml \
    $(DEVICE_PATH)/configs/audio/sound_trigger_mixer_paths.xml:$(TARGET_COPY_OUT_ODM)/etc/sound_trigger_mixer_paths.xml \
    $(DEVICE_PATH)/configs/audio/sound_trigger_mixer_paths.xml:$(TARGET_COPY_OUT_VENDOR)/etc/audio/sku_lahaina/sound_trigger_mixer_paths.xml \
    $(DEVICE_PATH)/configs/audio/sound_trigger_platform_info.xml:$(TARGET_COPY_OUT_ODM)/etc/sound_trigger_platform_info.xml \
    $(DEVICE_PATH)/configs/audio/sound_trigger_platform_info.xml:$(TARGET_COPY_OUT_VENDOR)/etc/audio/sku_lahaina/sound_trigger_platform_info.xml

# Boot animation
TARGET_SCREEN_HEIGHT := 2400
TARGET_SCREEN_WIDTH := 1080

# Camera
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/configs/camera/media_profiles_vendor.xml:$(TARGET_COPY_OUT_VENDOR)/etc/media_profiles_vendor.xml

# Display
PRODUCT_SYSTEM_PROPERTIES += \
    sys.brightness.disable_gamma_conversion=true

# Lineage Health
$(call soong_config_set,lineage_health,charging_control_charging_path,/sys/class/oplus_chg/battery/mmi_charging_enable)

# NFC
PRODUCT_PACKAGES += \
    android.hardware.nfc-service.nxp \
    NfcNci \
    SecureElement \
    com.android.nfc_extras \
    Tag

PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.nfc.ese.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.nfc.ese.xml \
    frameworks/native/data/etc/android.hardware.nfc.hce.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.nfc.hce.xml \
    frameworks/native/data/etc/android.hardware.nfc.hcef.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.nfc.hcef.xml \
    frameworks/native/data/etc/android.hardware.nfc.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.nfc.xml \
    frameworks/native/data/etc/android.hardware.se.omapi.ese.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.se.omapi.ese.xml \
    frameworks/native/data/etc/android.hardware.se.omapi.uicc.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/android.hardware.se.omapi.uicc.xml \
    frameworks/native/data/etc/com.android.nfc_extras.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/com.android.nfc_extras.xml \
    frameworks/native/data/etc/com.nxp.mifare.xml:$(TARGET_COPY_OUT_VENDOR)/etc/permissions/com.nxp.mifare.xml

# Overlays
DEVICE_PACKAGE_OVERLAYS += \
    $(LOCAL_PATH)/overlay-custom

PRODUCT_PACKAGES += \
    OPlusFrameworksResTarget \
    OPlusSettingsProviderResTarget \
    OPlusSettingsResTarget \
    OPlusSystemUIResTarget \
    TargetWifiOverlay

# Soong namespaces
# Reference-only LG sources must never provide modules to this product.
PRODUCT_SOURCE_ROOT_DIRS += -ref-lg

PRODUCT_SOONG_NAMESPACES += \
    $(LOCAL_PATH)

# Touch
$(call soong_config_set_bool,OPLUS_LINEAGE_TOUCH_HAL,ENABLE_HTPR,true)
$(call soong_config_set_bool,OPLUS_LINEAGE_TOUCH_HAL,ENABLE_TG,true)
$(call soong_config_set_bool,OPLUS_LINEAGE_TOUCH_HAL,USE_OPLUSTOUCH,false)
$(call soong_config_set,OPLUS_LINEAGE_TOUCH_HAL,GESTURE_ENABLE_INDEP_NODES,/proc/touchpanel/double_tap_enable_indep)
$(call soong_config_set,OPLUS_LINEAGE_TOUCH_HAL,INCLUDE_DIR,$(LOCAL_PATH)/touch/include)
# TODO(porsche): keep ENABLE_GM at the A17 default (false); no verified Porsche
# glove-mode setting was enabled by that tree. HTPR_ENABLE_NODE/HTPR_ENABLE_VALUE
# retain their HAL defaults (GAME_SWITCH_ENABLE_NODE/1) for the unused stock
# AIDL backend. The active direct backend writes game_switch_enable, as in A17.

# LiveDisplay: preserve the working A17 service's default PA/SE selection.
$(call soong_config_set_bool,OPLUS_LINEAGE_LIVEDISPLAY_HAL,ENABLE_PA,true)
$(call soong_config_set_bool,OPLUS_LINEAGE_LIVEDISPLAY_HAL,ENABLE_SE,true)
# TODO(porsche): ENABLE_AB/ENABLE_AF/ENABLE_DM stay unset (default false).
# The reference did not enable these features; no equivalent controls have
# been verified for Porsche, so do not infer support from other Oplus panels.

# Vibrator
$(call soong_config_set_bool,OPLUS_LINEAGE_VIBRATOR_HAL,USE_EFFECT_STREAM,true)
# TODO(porsche): keep vibrator INCLUDE_DIR unset, matching the A17 reference;
# the uvite effect header is not a verified override for this implementation.
# TODO(porsche): OPLUS_SENSORS_FUSIONLIGHT/BACKEND_SUBHAL_LIB_NAME stays unset.
# The booting reference selects sensors.oplus and sensors.qti directly, not
# the FusionLight wrapper. Keep those original sensors and their configuration.

# Inherit from the common OEM chipset makefile.
$(call inherit-product, device/oneplus/sm8350-common/common.mk)

# The new common tree owns init, sensors, thermals, IRQ balancing and WLAN
# configuration. Keep the uvite copies as references, without installing them.
# AOSPA-specific resources and gesture support are retained from the uvite tree.
PRODUCT_PACKAGES += \
    AOSPAPorscheFrameworks \
    AOSPAPorscheSystemUI \
    PorscheNfc
DEVICE_MANIFEST_FILE += $(DEVICE_PATH)/configs/vintf/manifest_porsche.xml
DEVICE_FRAMEWORK_COMPATIBILITY_MATRIX_FILE += $(DEVICE_PATH)/configs/vintf/compatibility_matrix.porsche.xml

# Inherit from the proprietary files makefile.
$(call inherit-product, vendor/realme/porsche/porsche-vendor.mk)

# TODO(porsche): calcite owns vendor.qti.hardware.fm@1.0 for both framework
# and vendor. Use that interface glue once; keep the A17 prebuilt as the
# porsche_vendor_fm_blob filegroup for ABI comparison. FM service is unchanged.
PRODUCT_PACKAGES += vendor.qti.hardware.fm@1.0.vendor
