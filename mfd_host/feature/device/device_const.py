# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Const Module for Device feature."""

# Device status error code and description mapping on Windows
DEVICE_STATUS_DESCRIPTION_MAP = {
    0: "Code 0: Device is working properly.",
    1: "Code 1: This device is not configured correctly.",
    3: "Code 3: The driver for this device might be corrupted, "
    "or your system may be running low on memory or other resources.",
    10: "Code 10: The device cannot start",
    12: "Code 12: This device cannot find enough free resources that it can use. "
    "If you want to use this device, you will need to disable one of the other devices on this system.",
    14: "Code 14: This device cannot work properly until you restart your computer.",
    16: "Code 16: Windows cannot identify all the resources this device uses.",
    18: "Code 18: Reinstall the drivers for this device.",
    19: "Code 19: Windows cannot start this hardware device because its configuration information "
    "(in the registry) is incomplete or damaged. To fix this problem you can first try running a "
    "Troubleshooting Wizard. If that does not work, you should uninstall and then reinstall the hardware device.",
    21: "Code 21: Windows is removing this device.",
    22: "Code 22: This device is disabled.",
    24: "Code 24: This device is not present, is not working properly, or does not have all its drivers installed.",
    28: "Code 28: The drivers for this device are not installed.",
    29: "Code 29: This device is disabled because the firmware of the device did not give it the required resources.",
    31: "Code 31: This device is not working properly because "
    "Windows cannot load the drivers required for this device.",
    32: "Code 32: A driver (service) for this device has been disabled. "
    "An alternate driver may be providing this functionality.",
    33: "Code 33: Windows cannot determine which resources are required for this device.",
    34: "Code 34: Windows cannot determine the settings for this device.  Consult the documentation that "
    "came with this device and use the Resource tab to set the configuration.",
    35: "Code 35: Your computer's system firmware does not include enough information to properly "
    "configure and use this device. To use this device, contact your computer manufacturer to "
    "obtain a firmware or BIOS update.",
    36: "Code 36: This device is requesting a PCI interrupt but is configured for an ISA interrupt "
    "(or vice versa). Please use the computer's system setup program to reconfigure the interrupt for this device.",
    37: "Code 37: Windows cannot initialize the device driver for this hardware.",
    38: "Code 38: Windows cannot load the device driver for this hardware because a previous instance "
    "of the device driver is still in memory.",
    39: "Code 39: Windows cannot load the device driver for this hardware.  The driver may be "
    "corrupted or missing.  Typically this is a signing issue.",
    40: "Code 40: Windows cannot access this hardware because its service key information in the registry "
    "is missing or recorded incorrectly",
    41: "Code 41: Windows successfully loaded the device driver for this hardware but cannot find the hardware device.",
    42: "Code 42: Windows cannot load the device driver for this hardware because there is a duplicate "
    " device already running in the system.",
    43: "Code 43: Windows has stopped this device because it has reported problems.",
    44: "Code 44: An application or service has shut down this hardware device.",
    45: "Code 45: Currently, this hardware device is not connected to the computer.",
    46: "Code 46: Windows cannot gain access to this hardware device because "
    "the operating system is in process of shutting down.",
    47: "Code 47: Windows cannot use this hardware device because it has been prepared for safe removal, "
    "but it has not been removed from the computer.",
    48: "Code 48: The software for this device has been blocked from starting because it is known "
    "to have problems with Windows.  Contact the hardware vendor for a new driver.",
    49: "Code 49: Windows cannot start new hardware devices because the system hive "
    "is too large (exceeds the Registry Size Limit).",
}
