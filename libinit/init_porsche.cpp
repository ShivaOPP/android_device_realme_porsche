/*
 * Copyright (C) 2023 Paranoid Android
 * SPDX-License-Identifier: Apache-2.0
 */

#include <cstring>
#include <android-base/properties.h>

#define _REALLY_INCLUDE_SYS__SYSTEM_PROPERTIES_H_
#include <sys/_system_properties.h>

static void OverrideProperty(const char* name, const char* value) {
    prop_info* pi = const_cast<prop_info*>(__system_property_find(name));
    if (pi != nullptr) {
        __system_property_update(pi, value, std::strlen(value));
    } else {
        __system_property_add(name, std::strlen(name), value, std::strlen(value));
    }
}

void vendor_load_properties() {
    // TODO(porsche): the A17 product supplies its verified RMX3312 fingerprint.
    // Do not restore uvite's Android 13 fingerprint or guess a boot project ID.
    // Preserve a SKU supplied by the bootloader; retain the uvite fallback only
    // for bootloaders that do not populate this property.
    if (android::base::GetProperty("ro.boot.hardware.sku", "").empty()) {
        OverrideProperty("ro.boot.hardware.sku", "porsche");
    }
}
