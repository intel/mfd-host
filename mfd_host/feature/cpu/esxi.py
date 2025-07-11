# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for ESXi CPU."""

import logging
import re

from mfd_common_libs import add_logging_level, log_levels
from mfd_host.exceptions import CPUFeatureExecutionError, CPUFeatureException
from mfd_host.feature.cpu.base import BaseFeatureCPU
from mfd_network_adapter.data_structures import State

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class ESXiCPU(BaseFeatureCPU):
    """ESXi class for CPU feature."""

    def packages(self) -> int:
        """To fetch the number of numa nodes.

        :return: numa nodes number (packages)
        """
        return self._cpu_attributes(search_pattern="CPU Packages")

    def cores(self) -> int:
        """To fetch the number of cores.

        :return: cores number
        """
        return self._cpu_attributes(search_pattern="CPU Cores")

    def threads(self) -> int:
        """To fetch the numbers of threads.

        :return: threads number
        """
        return self._cpu_attributes(search_pattern="CPU Threads")

    def _cpu_attributes(self, search_pattern: str) -> int:
        """To fetch cpu attributes.

        :param search_pattern: Pattern to fetch CPU Attribute
        :return: CPU Attribute value
        :raises CPUFeatureException: if unable to fetch the CPU Attribute
        """
        command = "esxcli hardware cpu global get"
        output = self._connection.execute_command(command, custom_exception=CPUFeatureExecutionError).stdout
        matched_cpu_attribute = re.search(rf"{search_pattern}:\s+(?P<cpu_attribute>\d+)", output)
        if not matched_cpu_attribute:
            raise CPUFeatureException(f"Unable to fetch CPU Attribute: {search_pattern}")
        return int(matched_cpu_attribute.group("cpu_attribute"))

    def set_numa_affinity(self, numa_state: State) -> None:
        """Set the advanced OS setting "LocalityWeightActionAffinity.

        :param numa_state: enable.ENABLED for enabling and enable.DISABLED for disabling
        """
        value = "--default" if numa_state is State.ENABLED else "-i 0"
        self._connection.execute_command(
            f'esxcli system settings advanced set {value} -o "/Numa/LocalityWeightActionAffinity"',
            custom_exception=CPUFeatureExecutionError,
        )
