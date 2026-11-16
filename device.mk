#
# Copyright (C) 2023 Paranoid Android
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/realme/porsche
SM8350_FSTAB_MODULE := fstab.porsche
$(call inherit-product, device/oneplus/sm8350-common/common.mk)
LOCAL_PATH := $(DEVICE_PATH)

# Product registration and vendor/aospa inheritance belong to
# vendor/aospa/products/porsche/aospa_porsche.mk on calcite.

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

PRODUCT_PACKAGES += \
    libstdc++_vendor

# Display
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/configs/display/display_id_4630946728207028354.xml:$(TARGET_COPY_OUT_VENDOR)/etc/displayconfig/display_id_4630946728207028354.xml

# Fingerprint overlay behaviour and Porsche init are retained from uvite.
TARGET_USES_FOD_ZPOS := true
PRODUCT_PACKAGES += \
    init.porsche.rc \
    init.porsche.perf.rc \
    ueventd.porsche.rc

# Overlays
PRODUCT_PACKAGES += \
    AOSPAPorscheFrameworks \
    AOSPAPorscheSystemUI \
    PorscheCarrierConfig \
    PorscheFrameworks \
    PorscheNfc \
    PorscheSettings \
    PorscheSettingsProvider \
    PorscheSystemUI \
    PorscheWifiResTarget \
    PorscheWifiResTargetMainline

# Porsche IRQ affinity, thermals and WLAN tuning.
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/configs/perf/msm_irqbalance.conf:$(TARGET_COPY_OUT_VENDOR)/etc/msm_irqbalance.conf \
    $(DEVICE_PATH)/configs/thermal/thermal-engine.conf:$(TARGET_COPY_OUT_VENDOR)/etc/thermal-engine.conf \
    $(DEVICE_PATH)/configs/wlan/WCNSS_qcom_cfg.ini:$(TARGET_COPY_OUT_VENDOR)/etc/wifi/WCNSS_qcom_cfg.ini

# Keep the AOSPA gesture extension while using the new Oplus sensor/vibrator HALs.
PRODUCT_SOONG_NAMESPACES += $(DEVICE_PATH)
$(call inherit-product, vendor/realme/porsche/porsche-vendor.mk)

# Verified Porsche declarations from the matching Android 17 device reference.
DEVICE_MANIFEST_FILE += $(DEVICE_PATH)/configs/vintf/manifest_porsche.xml
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/configs/camera/media_profiles_vendor.xml:$(TARGET_COPY_OUT_VENDOR)/etc/media_profiles_vendor.xml
$(call soong_config_set,lineage_health,charging_control_charging_path,/sys/class/oplus_chg/battery/mmi_charging_enable)
$(call soong_config_set,OPLUS_LINEAGE_TOUCH_HAL,INCLUDE_DIR,$(DEVICE_PATH)/touch/include)
$(call soong_config_set_bool,OPLUS_LINEAGE_VIBRATOR_HAL,USE_EFFECT_STREAM,true)

# Use calcite hardware/nxp/nfc AIDL HAL; the old QTI Nfc apps path is gone.
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
