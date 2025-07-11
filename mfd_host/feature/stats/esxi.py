# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for ESXi stats."""

import logging
import re
from typing import Dict

from mfd_common_libs import add_logging_level, log_levels

from mfd_host.exceptions import StatisticNotFoundException
from mfd_host.feature.stats.base import BaseFeatureStats

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class ESXiStats(BaseFeatureStats):
    """ESXi class for Stats feature."""

    def get_meminfo(self) -> Dict[str, str]:
        """Get information about memory in system.

        :return: dictionary represents total memory usage and free heap (if available) data
        :raises StatisticNotFoundException: when unable to fetch system memory usage
        """
        out = self._connection.execute_command("vsish -e get /memory/memInfo", shell=True).stdout
        regex_heap_mem = r"System heap free \(pages\):(?P<heap_free>\d+)\n\s*"
        regex_memory_usage = r"System memory usage \(pages\):(?P<match_regex_memory>\d+)"
        match_regex_memory = re.search(regex_memory_usage, out, re.MULTILINE)
        match_regex_heap_mem = re.search(regex_heap_mem, out, re.MULTILINE)
        if match_regex_memory:
            return {
                "mem_usage": match_regex_memory.group("match_regex_memory"),
                "heap_free": match_regex_heap_mem.group("heap_free") if match_regex_heap_mem else None,
            }
        else:
            raise StatisticNotFoundException(f"Cannot get memory info for the host. CMD Output: {out}")
