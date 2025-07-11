# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for host stats data structures."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class StatsOutput:
    """Dataclass for the host stats parameters."""

    cpu_stat: str
    memory_stat: str
    process_stat: str
    cpu_raw_output: Optional[str] = None
    memory_raw_output: Optional[str] = None
    process_raw_output: Optional[str] = None


cpu_actual_labels = ["us", "sy", "ni", "id", "wa", "hi", "si", "st"]
cpu_friendly_labels = ["user", "sys", "nice", "idle", "IO-wait", "HW-int", "SOFT-int", "stolen"]
mem_labels = ["total", "free", "used"]
swap_labels = ["total", "free", "used"]

"""Windows Counter Path"""

AvailableMemory = '"\\Memory\\Available Bytes"'
PagedMemory = '"\\Memory\\Pool Paged Bytes"'
NonPagedMemory = '"\\Memory\\Pool Nonpaged Bytes"'
CPUTimeUtilization = '"\\Processor(_Total)\\% Processor Time"'
DPCRate = r"\Processor(*)\DPC Rate"
