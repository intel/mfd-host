# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for stats feature."""

from typing import Union

from .base import BaseFeatureStats
from .esxi import ESXiStats
from .linux import LinuxStats
from .windows import WindowsStats
from .freebsd import FreeBSDStats

StatsFeatureType = Union[BaseFeatureStats, ESXiStats, LinuxStats, WindowsStats, FreeBSDStats]
