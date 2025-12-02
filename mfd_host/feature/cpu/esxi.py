# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for ESXi CPU."""

import logging
import re
from time import sleep

from mfd_common_libs import add_logging_level, log_levels, TimeoutCounter
from mfd_connect.process import RemoteProcess

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

    def start_cpu_measurement(self) -> RemoteProcess:
        """
        Start CPU measurement on host.

        :return: Handle to process
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg="Start CPU measurement on host")
        return self._connection.start_process(command="esxtop -b -n 8 -d3", log_file=True, shell=True)

    def stop_cpu_measurement(self, process: RemoteProcess, process_name: str) -> int:
        """
        Stop CPU measurement process.

        :param process: Process handle
        :param process_name: process name to filter CPU usage
        :return: Average CPU usage percentage
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg="Stop CPU measurement on host")
        if process.running:
            process.stop()
            timeout = TimeoutCounter(5)
            while not timeout:
                if not process.running:
                    break
                sleep(1)
            else:
                process.kill()
                timeout = TimeoutCounter(5)
                while not timeout:
                    if not process.running:
                        break
                    sleep(1)
                if process.running:
                    raise RuntimeError("CPU measurement process is still running after stop and kill.")

        return self.parse_cpu_usage(process_name=process_name, process=process)

    def parse_cpu_usage(self, process_name: str, process: RemoteProcess) -> int:
        """
        Parse CPU usage from esxtop output.

        :param process_name: process_name name to filter CPU usage
        :param process: Process handle
        :return: average CPU usage percentage
        """
        parsed_file_path = "/tmp/parsed_output.txt"
        command = (
            f"cut -d, -f`awk -F, '{{for (i=1;i<=NF;i++){{if ($i ~/Group Cpu.*{process_name}).*Used/) "
            f"{{print i}}}}}}' {process.log_path}` {process.log_path}>{parsed_file_path}"
        )
        self._connection.execute_command(command=command, shell=True)
        p = self._connection.path(process.log_path)
        p.unlink()
        try:
            parsed_file_path = self._connection.path(parsed_file_path)
            file_content = parsed_file_path.read_text()
            cpu_list = []
            for line in file_content.splitlines()[1:]:
                try:
                    cpu_list.append(float(line.strip('"')))
                except ValueError:
                    continue

        except Exception as e:
            raise RuntimeError(f"Failed to read parsed CPU usage output file due to - {e}.")

        p = self._connection.path(parsed_file_path)
        p.unlink()
        return round(sum(cpu_list) / len(cpu_list)) if cpu_list else 0
