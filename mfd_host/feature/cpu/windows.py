# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for Windows CPU."""

import logging
import re
from typing import Dict, List

from mfd_common_libs import add_logging_level, log_levels
from mfd_connect.util.powershell_utils import parse_powershell_list
from mfd_host.exceptions import CPUFeatureExecutionError, CPUFeatureException
from mfd_host.feature.cpu.base import BaseFeatureCPU
from mfd_host.feature.cpu.const import COREINFO_REGISTRY_PATH, COREINFO_EXE_PATH
from mfd_network_adapter.data_structures import State

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class WindowsCPU(BaseFeatureCPU):
    """Windows class for CPU feature."""

    def get_core_info(self) -> List[Dict[str, str]]:
        """Get device id, number of cores and number of logical processors.

        :return: list of CPUs
        :raise CPUFeatureExecutionError: if unable to fetch core information
        """
        cmd = "Get-WmiObject -class Win32_processor | select DeviceID, NumberOfCores, NumberOfLogicalProcessors | fl"
        output = self._connection.execute_powershell(cmd, custom_exception=CPUFeatureExecutionError).stdout
        return parse_powershell_list(output)

    def get_hyperthreading_state(self) -> State:
        """Check if hyperthreading enabled.

        :return: Enabled is hyperthreading is on, Disabled otherwise
        :raise CPUFeatureExecutionError: if unable to fetch core information
        """
        core_info = self.get_core_info()
        for cpu in core_info:
            number_of_cores = int(cpu["NumberOfCores"])
            number_of_logical_proc = int(cpu["NumberOfLogicalProcessors"])
            if number_of_logical_proc > number_of_cores:
                return State.ENABLED
        return State.DISABLED

    def get_phy_cpu_no(self) -> int:
        """Get the number of physical cpus.

        :return: Number of physical cores
        :raise CPUFeatureException: if unable to fetch physical processors
        """
        cmd = "gwmi win32_processor -Property NumberOfCores"
        output = self._connection.execute_powershell(cmd, custom_exception=CPUFeatureExecutionError).stdout

        match = re.findall(r"NumberOfCores\s+:\s+(\d+)", output)
        if match:
            return sum(map(int, match))
        else:
            raise CPUFeatureException(f"Cannot find number of physical processors: {output}")

    def _accept_sysinternals_eula(self, registry_path: str) -> None:
        """Accept eula for given sysinternals executable.

        :param registry_path: Registry path of sysinternals executable
        :raises CPUFeatureException: if error while trying to accept EULA
        """
        cmd = f"new-item -path '{registry_path}' -Force"
        self._connection.execute_powershell(cmd, custom_exception=CPUFeatureExecutionError)

        cmd = f"set-itemproperty -path '{registry_path}' -Name {'EulaAccepted'} -Value {1}"
        self._connection.execute_powershell(cmd, custom_exception=CPUFeatureExecutionError)

    def get_numa_node_count(self) -> int:
        """Get NUMA node count.

        :return: Number of numa nodes
        :raises CPUFeatureException: if error while trying to accept EULA
        """
        self._accept_sysinternals_eula(COREINFO_REGISTRY_PATH)

        cmd = f"{COREINFO_EXE_PATH}\\Coreinfo.exe -n"
        output = self._connection.execute_powershell(cmd, custom_exception=CPUFeatureExecutionError).stdout

        return len(re.findall(r".*NUMA Node\s*(\d+).*", output))

    def get_log_cpu_no(self) -> int:
        """Get the number of logical CPUs.

        :return: Number of logical cpus
        :raises CPUFeatureException: if failed to get logical cpus
        """
        cmd = "gwmi win32_computersystem -Property NumberOfLogicalProcessors"
        output = self._connection.execute_powershell(cmd).stdout
        match = re.search(r"NumberOfLogicalProcessors : (?P<logical_processors_num>\d+)", output)
        if match:
            return int(match.group("logical_processors_num"))
        else:
            raise CPUFeatureException("Failed to fetch the processors count on interface")

    def _is_power_of_two(self, power_two: int) -> bool:
        """To check if given value is power of two.

        :param power_two: Value to check if it is power of two
        :return: True if power of two else False
        """
        return power_two != 0 and ((power_two & (power_two - 1)) == 0)

    def _check_maxsize(self, maxsize: int) -> None:
        """To check maxsize is correct.

        :param maxsize: maximum processor group size
        :raises CPUFeatureException: if maxsize given user is not less than logical processors or power of two
        """
        if not (maxsize < self.get_log_cpu_no() and self._is_power_of_two(maxsize)):
            raise CPUFeatureException("Maxsize for processors should be less than logical processors and power of two")

    def set_groupsize(self, maxsize: int) -> None:
        """Set maximum processor group size.

        Note: maxsize must be a power of two: 2, 4, 8, 16, 32, or 64
            maxsize should be a value lower than your current number of logical processors

        :param maxsize: maximum processor group size
        :raises CPUFeatureException: if operation failed/maxsize is not less than logical processors or power of two
        """
        self._check_maxsize(maxsize)
        cmd = f"bcdedit /set groupsize {maxsize}"
        output = self._connection.execute_powershell(cmd, custom_exception=CPUFeatureExecutionError).stdout
        if "successful" not in output.lower():
            raise CPUFeatureException("Failed to set CPU groupsize")
