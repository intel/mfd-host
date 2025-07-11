# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for Linux CPU."""

import logging
import re
from typing import Dict

from mfd_common_libs import add_logging_level, log_levels
from mfd_host.exceptions import CPUFeatureExecutionError, CPUFeatureException
from mfd_host.feature.cpu.base import BaseFeatureCPU

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class LinuxCPU(BaseFeatureCPU):
    """Linux class for CPU feature."""

    def display_cpu_stats_only(self) -> str:
        """Display the cpu stats only.

        :return: Output of stats
        """
        cmd = "mpstat -P ALL"
        output = self._connection.execute_command(cmd, custom_exception=CPUFeatureExecutionError).stdout
        return output.strip()

    def _parse_cpu_stats(self, output: str) -> Dict[str, Dict[str, str]]:
        """To parse CPU stats output.

        :param output: Output from mpstat -A
        :return: CPU Stats in below format
                {cpu:{stat1:value1, stat2:value2}, cpu:...}
        """
        output = output.split("\n\n")
        result = {}

        regex = r"\s(?:AM\s|PM\s)?\s*(?P<cpu_stats>\S+)\s+(?P<cpu_stats_values>.+)"
        for op in output[1:3]:
            data = op.splitlines()
            match_titles = re.search(regex, data[0])
            titles = match_titles.group("cpu_stats_values").split()
            for line in data[1:]:
                match = re.search(regex, line)
                entry = match.group("cpu_stats")
                if entry not in result:
                    result[entry] = {}
                values = match.group("cpu_stats_values").split()
                for title, value in zip(titles, values):
                    # Remove % sign from key's name
                    title = title.replace("%", "")
                    result[entry][title] = value
        return result

    def get_cpu_stats(self) -> Dict[str, Dict[str, str]]:
        """To fetch CPU stats.

        :return: CPU Stats in below format
                {cpu:{stat1:value1, stat2:value2}, cpu:...}
        """
        cmd = "mpstat -A"
        output = self._connection.execute_command(cmd, custom_exception=CPUFeatureExecutionError).stdout
        return self._parse_cpu_stats(output)

    def get_log_cpu_no(self) -> int:
        """Get the number of logical CPUs.

        :return: Number of logical cpus
        :raises CPUFeatureException: if failed to get logical cpus
        """
        command = "nproc"
        output = self._connection.execute_command(command, custom_exception=CPUFeatureExecutionError).stdout
        try:
            lines = output.splitlines()
            output = int(lines[-1])
        except ValueError:
            raise CPUFeatureException(f"Invalid number of logical CPU found: {output}")
        return output

    def affinitize_queues_to_cpus(self, adapter: str, scriptdir: str) -> None:
        """Execute set_irq_affinity script on given adapter.

        :param adapter: adapter related with affinitized queues
        :param scriptdir: path to the set_irq_affinity script
        :raises CPUFeatureException: if error while executing set_irq_affinity script
        """
        cmd_line = f"./{'set_irq_affinity'} {adapter}"
        output = self._connection.execute_command(
            command=cmd_line,
            cwd=scriptdir,
            custom_exception=CPUFeatureExecutionError,
            shell=True,
            expected_return_codes={0, 2},
        ).stderr
        if output:
            raise CPUFeatureException("Found Error while executing set_irq_affinity script")
