# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for Windows stats."""

import logging
import re
from typing import Dict


from mfd_common_libs import add_logging_level, log_levels

from mfd_host.exceptions import StatisticNotFoundException
from mfd_host.feature.stats.base import BaseFeatureStats

from . import data_structures

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class WindowsStats(BaseFeatureStats):
    """Windows class for Stats feature."""

    def get_meminfo(self) -> Dict[str, int]:
        r"""Get information about memory in system.

        return: Dict represents  \\Memory\\Available Bytes\
                                        \\Memory\\Pool Paged Bytes\
                                        \\Memory\\Pool Nonpaged Bytes\
        """
        return {
            "Available": int(self.get_performance_counter(data_structures.AvailableMemory)),
            "Paged": int(self.get_performance_counter(data_structures.PagedMemory)),
            "Nonpaged": int(self.get_performance_counter(data_structures.NonPagedMemory)),
        }

    def get_cpu_utilization(self) -> float:
        """Get the CPU utilization value.

        return: CPU Time Utilization
        """
        return self.get_performance_counter(data_structures.CPUTimeUtilization)

    def get_performance_counter(self, counter_name: str) -> float:
        """Get performance counter value.

        :param counter_name: counter name for which the data needs to be queried.
        :return: stats value.
        :raises StatisticNotFoundException when unable to parse the powershell output.
        """
        cmd = f"Get-counter -Counter {counter_name} | Format-List"

        cmd_output = self._connection.execute_powershell(cmd, expected_return_codes={0}).stdout

        if "Readings  : " in cmd_output:
            line = cmd_output.split("Readings  : ")[1].split(":")
            if len(line) == 2:
                line = re.sub(r"\s", "", line[1])
                try:
                    return float(line)
                except ValueError:
                    raise StatisticNotFoundException(f"Cannot read counter output: {cmd_output}")

        raise StatisticNotFoundException(f"Cannot parse counter output: {cmd_output}")

    def get_performance_collection(self, *counters, samples: int = 1, interval: int = 1) -> Dict[str, Dict[str, str]]:
        r"""Get performance counter data for a set of counters, Implementation based on powershell Get-Counter cmdlet.

        :param counters: list (one or more) of performance counters. Each counter path has the following format:
                "\<CounterSet>(<Instance>)\<CounterName>"
            Wildcards are permitted only in the Instance value, e.g.: "\Processor(*)\Interrupts/sec",
            "\Processor(*)\DPC Rate"

        :param samples: number of samples to get from each counter. The default is 1 sample
        :param interval: time between samples in seconds. The minimum value and the default value are 1 second.

        :return: Performance counter data
        """
        counters_name = ", ".join([rf"'{counter}'" for counter in counters])
        cmd_params = ""
        if samples:
            cmd_params = f"-MaxSamples {int(samples)} "
            if interval:
                cmd_params += f"-SampleInterval {int(interval)} "

        cmd = f"Get-counter -Counter {counters_name} {cmd_params} | Format-List"

        cmd_output = self._connection.execute_powershell(cmd, expected_return_codes={0}).stdout

        regex = re.compile(r"Timestamp : (?P<timestamp>.+)\n(?P<content>(?:(?:.+\n){3})+)")

        stats = {}
        for match in regex.finditer(cmd_output):
            result = match.groupdict()
            ts = result["timestamp"]
            content = result["content"]

            if "Readings  :" in content:
                lines = content.split("Readings  :")
                lines = lines[1]
                lines = re.split(r"^\s+$", lines, flags=re.MULTILINE)
                for line in lines:
                    if not line:
                        continue
                    item = re.sub(r"\n\s+", "", line)
                    key_val = item.split(" :")
                    if key_val:
                        stat_name = key_val[0]
                        val = key_val[1].replace("\n", "")
                        stats.setdefault(stat_name, {})[ts] = val
        return stats

    def _mean_data(self, time_data_dict: Dict[str, str]) -> float:
        """
        Calculate the mean/average data for a Windows performance counter dictionary.

        :param time_data_dict: Key value from the performance dictionary
        :return: mean value
        """
        data_len = len(time_data_dict)
        if data_len == 0:
            return 0.0

        total = sum(float(value) for value in time_data_dict.values())
        return total / data_len

    def parse_performance_collection(self, raw_perf_data: Dict[str, float]) -> Dict[str, float]:
        """
        Parse the raw data from get_performance_collection and calculate mean/average the data.

        :param raw_perf_data: raw data from get_performance_collection
        :return: parsed data
        """
        data_dict = {}
        for key in sorted(raw_perf_data):
            new_key = key.strip()[key.strip().find("(") + 1 :].replace(")\\", "_")
            data_dict[new_key] = self._mean_data(raw_perf_data[key])

        return data_dict

    def get_dpc_rate(self, interval: int = 5, samples: int = 5) -> Dict[str, int]:
        """Get DPC Rate values from performance monitor.

        :param interval: time between samples in seconds
        :param samples: number of samples to get from each counter
        :return: Dict parsed dpc_rate data
        """
        perf_data = self.get_performance_collection(data_structures.DPCRate, interval=interval, samples=samples)
        return self.parse_performance_collection(perf_data)
