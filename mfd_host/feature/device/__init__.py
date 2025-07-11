# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for device feature."""

from .base import BaseFeatureDevice
from .windows import WindowsDevice

DeviceFeatureType = BaseFeatureDevice | WindowsDevice
