# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for service feature."""

from .base import BaseFeatureService
from .esxi import ESXiService
from .freebsd import FreeBSDService
from .linux import LinuxService
from .windows import WindowsService

ServiceFeatureType = BaseFeatureService | ESXiService | FreeBSDService | LinuxService | WindowsService
