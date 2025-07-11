# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for utils feature."""

from typing import Union

from .base import BaseFeatureUtils
from .linux import LinuxUtils
from .windows import WindowsUtils
from .freebsd import FreeBSDUtils
from .esxi import ESXiUtils

UtilsFeatureType = Union[BaseFeatureUtils, LinuxUtils, WindowsUtils, FreeBSDUtils, ESXiUtils]
