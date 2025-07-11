# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for CPU feature."""

from typing import Union

from .base import BaseFeatureCPU
from .esxi import ESXiCPU
from .freebsd import FreeBSDCPU
from .linux import LinuxCPU
from .windows import WindowsCPU

CPUFeatureType = Union[BaseFeatureCPU, ESXiCPU, FreeBSDCPU, LinuxCPU, WindowsCPU]
