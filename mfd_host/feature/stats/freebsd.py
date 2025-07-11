# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for FreeBSD stats."""

import logging
from typing import TYPE_CHECKING

from mfd_common_libs import add_logging_level, log_levels
from mfd_host.feature.stats.base import BaseFeatureStats
from mfd_sysctl.freebsd import FreebsdSysctl

if TYPE_CHECKING:
    from mfd_connect import Connection
    from mfd_host import Host

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class FreeBSDStats(BaseFeatureStats):
    """FreeBSD class for Stats feature."""

    def __init__(self, *, connection: "Connection", host: "Host") -> None:
        """Initialize the FreeBSD Stats feature.

        :param connection: Object of mfd-connect
        :param host: Object of mfd-host
        """
        super().__init__(connection=connection, host=host)
        self._connection = connection
        self._sysctl = FreebsdSysctl(connection=connection)
        self._cp_times_last = None

    def get_cpu_utilization(self) -> dict[str, dict[str, str]]:
        """Get CPU utilization.

        CPU utilization based on the time spent by the cores in different states since the last function call.

        :return: dictionary in format:
                 {'core_number': {'stat1': value,
                                  'stat2': value ...}}
        """
        # Obtain data on the time spent by each core in different states
        sysctl_out = self._sysctl.get_sysctl_value("kern.cp_times")
        cp_times_raw = list(map(int, sysctl_out.split()))
        cp_times = {
            str(int(i // 5)): {
                "user": cp_times_raw[i],
                "nice": cp_times_raw[i + 1],
                "system": cp_times_raw[i + 2],
                "interrupt": cp_times_raw[i + 3],
                "idle": cp_times_raw[i + 4],
            }
            for i in range(0, len(cp_times_raw), 5)
        }
        # For the first call will return average CPU usage since the system booted
        if not self._cp_times_last:
            self._cp_times_last = {c: {metric: 0 for metric in metrics.keys()} for c, metrics in cp_times.items()}
        # Calculate the difference for each core since the last call
        cp_times_diff = {
            c: {k: cp_times[c][k] - self._cp_times_last[c][k] for k in cp_times[c].keys()} for c in cp_times.keys()
        }
        # Save current cp_times ​​to calculate the difference on subsequent calls
        self._cp_times_last = cp_times
        # Sum up the differences for each core
        sum_cp_times_diff = {c: sum(cp_times_diff[c].values()) for c in cp_times_diff.keys()}
        # Calculate CPU load by the ratio of the metric difference to the sum of the differences for a specific core
        # coreN.sum_diff=coreN.user_diff+coreN.nice_diff+...+coreN.idle_diff
        # cpu_usage.coreN.user=coreN.user_diff/coreN.sum_diff,...,cpu_usage.coreN.idle=coreN.idle_diff/coreN.sum_diff
        cpu_usage = {
            core: {
                metric: (
                    round(cp_times_diff[core][metric] / sum_cp_times_diff[core] * 100.0, 2)
                    if sum_cp_times_diff[core]
                    else 0.0
                )
                for metric in cp_times_diff[core].keys()
            }
            for core in cp_times_diff.keys()
        }
        # Calculate the total CPU load
        total_cpu_usage = {}
        for d in cp_times_diff.values():
            for metric, value in d.items():
                total_cpu_usage[metric] = value + (total_cpu_usage[metric] if metric in total_cpu_usage.keys() else 0)
        total_sum_cp_times_diff = sum(sum_cp_times_diff.values())
        total_cpu_usage = {
            k: round(v / total_sum_cp_times_diff * 100.0, 2) if total_sum_cp_times_diff else 0.0
            for k, v in total_cpu_usage.items()
        }
        # Add the total CPU load to the final statistics
        cpu_usage["all"] = total_cpu_usage
        logger.log(log_levels.MODULE_DEBUG, f"CPU usage: {cpu_usage}")
        return cpu_usage

    def get_free_memory(self) -> int:
        """Get free memory.

        :return: Memory free in MB
        """
        v_free_count = int(self._sysctl.get_sysctl_value("vm.stats.vm.v_free_count"))
        pagesize = int(self._sysctl.get_sysctl_value("hw.pagesize"))
        freemem = (v_free_count * pagesize) >> 20
        return freemem

    def get_wired_memory(self) -> int:
        """Get wired (non-pageable) memory.

        :return: Wired memory in MB
        """
        v_wire_count = int(self._sysctl.get_sysctl_value("vm.stats.vm.v_wire_count"))
        pagesize = int(self._sysctl.get_sysctl_value("hw.pagesize"))
        wiredmem = (v_wire_count * pagesize) >> 20
        return wiredmem
