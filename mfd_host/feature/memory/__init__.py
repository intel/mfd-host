# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for memory feature."""

from typing import Union
from .base import BaseFeatureMemory
from .linux import LinuxMemory
from .windows import WindowsMemory
from .esxi import ESXiMemory
from .freebsd import FreeBSDMemory

MemoryFeatureType = Union[BaseFeatureMemory, LinuxMemory, WindowsMemory, FreeBSDMemory, ESXiMemory]
