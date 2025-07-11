# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for linux stats."""

import logging
import re
from typing import Dict, List, Optional, Union


from mfd_common_libs import add_logging_level, log_levels

from mfd_connect.base import ConnectionCompletedProcess
from mfd_host.exceptions import StatisticNotFoundException
from mfd_host.feature.stats.base import BaseFeatureStats

from .data_structures import cpu_actual_labels, cpu_friendly_labels, mem_labels, swap_labels, StatsOutput

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class LinuxStats(BaseFeatureStats):
    """Linux class for Stats feature."""

    def get_meminfo(self) -> Dict[str, str]:
        """Get information about memory in system.

        :return: dictionary represents /proc/meminfo data
        """
        out = self._connection.execute_command("cat /proc/meminfo", shell=True).stdout
        return {line[0].replace(":", ""): line[1] for line in (line.split() for line in out.splitlines())}

    def get_cpu_utilization(self) -> Dict[str, Dict[str, str]]:
        """Get sar CPU utilization values for all cores. Output data is in percentages which sums up to 1 for each core.

        :return: dictionary in format:
                 {'core_number': {'stat1': value,
                                  'stat2': value ...}}
        """
        out = self._connection.execute_command("sar -P ALL", shell=True).stdout
        return_dictionary = {}
        regex = (
            r"Average:[\s]*"
            r"(?P<cpu_number>[\d\w]*)[\s]*"
            r"(?P<user>[\d\.]*)[\s]*"
            r"(?P<nice>[\d\.]*)[\s]*"
            r"(?P<system>[\d\.]*)[\s]*"
            r"(?P<iowait>[\d\.]*)[\s]*"
            r"(?P<steal>[\d\.]*)[\s]*"
            r"(?P<idle>[\d\.]*)"
        )
        matches = re.finditer(regex, out)

        for match in matches:
            if match["cpu_number"] == "CPU":
                continue
            match = match.groupdict()
            return_dictionary[str(match["cpu_number"])] = match
        return return_dictionary

    def get_slabinfo(self) -> Dict[str, str]:
        """Capture slabinfo results.

        :return: dictionary slab output
        """
        out = self._connection.execute_command("cat /proc/slabinfo", shell=True).stdout

        pattern = r"(?P<slab_name>[\w-]*kmalloc[\w-]+)\s+(?P<slab_count>\d+)"
        matches = re.finditer(pattern, out)
        return {match.group("slab_name"): match.group("slab_count") for match in matches}

    def get_mem_used(self) -> int:
        """Get total memory used.

        :return: int memory used
        :raises StatisticNotFoundException: when unable to determine memory usage
        """
        out = self._connection.execute_command("cat /proc/meminfo", shell=True).stdout

        mem_total_pattern = r"MemTotal:\s+(?P<mem_total>\d+).*"
        mem_free_pattern = r"MemFree:\s+(?P<mem_free>\d+).*"
        mem_total_match = re.search(mem_total_pattern, out)
        mem_free_match = re.search(mem_free_pattern, out)
        if mem_free_match and mem_total_match:
            memory_total = int(mem_total_match.group("mem_total"))
            memory_free = int(mem_free_match.group("mem_free"))
            return memory_total - memory_free
        raise StatisticNotFoundException(f"Unable to find memory usage: {out}")

    def get_top_stats(
        self,
        separate_cpu: Optional[bool] = True,
        memory_scaling: Optional[str] = "",
        options: Optional[str] = "",
        friendly_labels: Optional[bool] = True,
        filter_proc: Optional[List[str]] = [],
    ) -> StatsOutput:
        """
        Get the top values and build a text output from the values themselves.

        Note: Different distributions of linux may include older versions of top which do not support some
                flags such as -1 and -E. Set separate_cpu=False and memory_scaling=""
        Note: This script will add a total to each cpu line, total = user + system + nice.  A grand total will be
                added as cpu 999
        :param separate_cpu: If True, set -1 flag to display stats for all CPUs, False for just a one line total
        :param memory_scaling: top -E flag, set memory scaling, use 'g', 'k', etc. see 'man top'
        :param options: Additional command line flags for top.
        :param friendly_labels: Instead of "us", "sys", etc., use "user", "system", etc. Only applies to cpu usage.
        :param filter_proc: Only return lines if filter_procs are anywhere in the entire proc line.
        :return: StatsOutput with cpu_raw_output, memory_raw_output, process_raw_output,
                cpu_stats, memory_stat, process_stat
        """
        top_out = self._get_top_values(separate_cpu, memory_scaling, options, friendly_labels, filter_proc)

        cpu_text = self._build_cpu_raw_output(cpu_stats=top_out.cpu_stat)
        mem_text = self._build_memory_raw_output(mem_stats=top_out.memory_stat)
        proc_text = self._build_process_raw_output(proc_stats=top_out.process_stat)

        return StatsOutput(
            cpu_stat=top_out.cpu_stat,
            memory_stat=top_out.memory_stat,
            process_stat=top_out.process_stat,
            cpu_raw_output=cpu_text,
            memory_raw_output=mem_text,
            process_raw_output=proc_text,
        )

    def _build_cpu_raw_output(self, cpu_stats: Dict[str, Dict[str, float]]) -> str:
        """
        Get the raw CPU stat string.

        :param cpu_stats: Dictonary containing CPU stats
        :return CPU stat text as seen in the top output.
        """
        cpu_lines = []
        for cpu_number, stats in cpu_stats.items():
            if cpu_number == 999:
                cpu_line = "Total  :"
            else:
                cpu_line = f"%CPU{cpu_number:<3}:"

            cpu_line += " ".join([f"{value:>6} {label}," for label, value in stats.items()])
            cpu_lines.append(cpu_line.rstrip(","))

        return "\n".join(cpu_lines)

    def _build_memory_raw_output(self, mem_stats: Dict[str, Dict[str, float]]) -> str:
        """
        Get the raw Memory stat string.

        :param mem_stats: Dictonary containing Memory stats
        :return memory stat text as seen in the top output.
        """
        mem_text = []

        mem_text.append(f"{mem_stats['Scale']:.3} Mem :")
        mem_text.append(" ".join([f"{value:>8} {label}," for label, value in mem_stats["Mem"].items()]))
        mem_text[-1] = mem_text[-1].rstrip(",")

        mem_text.append(f"{mem_stats['Scale']:.3} Swap:")
        mem_text.append(" ".join([f"{value:>8} {label}," for label, value in mem_stats["Swap"].items()]))
        mem_text[-1] = mem_text[-1].rstrip(",")

        return "\n".join(mem_text)

    def _build_process_raw_output(self, proc_stats: Dict[str, List[Union[int, float, str]]]) -> str:
        """
        Get the raw Process stat string.

        :param proc_stats: Dictonary containing Process stats
        :return Process stat text as seen in the top output.
        """
        proc_text = []
        proc_field_widths = {}

        # Calculate the max width for each field
        for field in proc_stats:
            proc_field_widths[field] = len(str(max(proc_stats[field], key=lambda s: len(str(s)))))

        # Build the proc list header label line
        proc_header = []
        for field in proc_stats:
            justify = "<" if isinstance(proc_stats[field][0], str) else ">"
            proc_header.append(f"{field:{justify}{(proc_field_widths[field] + 2)}.{(proc_field_widths[field] + 2)}} ")
        proc_text.append("".join(proc_header))

        # Build the proc list text
        for counter in range(len(proc_stats[field])):
            row = []
            for field in proc_stats:
                justify = "<" if isinstance(proc_stats[field][0], str) else ">"
                row.append(f"{proc_stats[field][counter]:{justify}{(proc_field_widths[field] + 2)}}")
            proc_text.append(" ".join(row))

        return "\n".join(proc_text)

    def _get_top_values(
        self,
        separate_cpu: Optional[bool] = True,
        memory_scaling: Optional[str] = "",
        options: Optional[str] = "",
        friendly_labels: Optional[bool] = True,
        filter_proc: Optional[List[str]] = [],
    ) -> StatsOutput:
        """
        Get the top values and build a text output from the values themselves.

        Note: Different distributions of linux may include older versions of top which do not support some
                flags such as -1 and -E. Set separate_cpu=False and memory_scaling=""
        Note: This script will add a total to each cpu line, total = user + system + nice.  A grand total will be
                added as cpu 999
        :param separate_cpu: If True, set -1 flag to display stats for all CPUs, False for just a one line total
        :param memory_scaling: top -E flag, set memory scaling, use 'g', 'k', etc. see 'man top'
        :param options: Additional command line flags for top.
        :param friendly_labels: Instead of "us", "sys", etc., use "user", "system", etc. Only applies to cpu usage.
        :param filter_proc: Only return lines if filter_procs are anywhere in the entire proc line.
        :return: StatsOutput with cpu_stats, memory_stat, process_stat
        :raises StatisticNotFoundException: When statistics collection fails.
        """
        output = self._execute_top_command(separate_cpu, memory_scaling, options)

        if output.return_code:
            if "inappropriate '1'" in output.stderr:
                output = self._handle_separate_cpu_warning(memory_scaling, options)
            else:
                raise StatisticNotFoundException(f"gathering stats failed with error: {output.stderr}")

        cpu_stats = self._get_cpu_from_top_output(output.stdout, friendly_labels)
        mem_stats = self._get_mem_from_top_output(output.stdout)
        proc_stats = self._get_proc_from_top_output(output.stdout, filter_proc)

        return StatsOutput(
            cpu_stat=cpu_stats,
            memory_stat=mem_stats,
            process_stat=proc_stats,
        )

    def _execute_top_command(self, separate_cpu: bool, memory_scaling: str, options: str) -> ConnectionCompletedProcess:
        """
        Execute the top command with specified parameters.

        :param separate_cpu: Flag indicating whether to use separate CPU reporting.
        :param memory_scaling: Memory scaling option.
        :param options: Additional command line flags for top.
        :return: Output of the executed command.
        """
        cmd = "top -b -n1"
        # -b = batch mode, -n1 = just once
        if separate_cpu:
            cmd += " -1"
        if memory_scaling:
            cmd += f" -E {memory_scaling}"
        if options:
            cmd += f" {str(options)}"
        return self._connection.execute_command(cmd, shell=True)

    def _handle_separate_cpu_warning(self, memory_scaling: str, options: str) -> ConnectionCompletedProcess:
        """
        Handle the warning about inappropriate '1' flag in the top command.

        :param memory_scaling: Memory scaling option.
        :param options: Additional command line flags for top.
        :return: Output of the executed command.
        :raises StatisticNotFoundException: When statistics collection fails.
        """
        logger.log(
            level=log_levels.MODULE_DEBUG,
            msg="Separate CPU reporting not supported, switch to single line reporting ",
        )
        separate_cpu = False
        output = self._execute_top_command(separate_cpu, memory_scaling, options)

        if output.return_code:
            raise StatisticNotFoundException(f"gathering stats failed with error: {output.stderr}")

        return output

    def _get_cpu_from_top_output(self, output: str, friendly_labels: bool) -> Dict[str, Dict[str, float]]:
        """
        Extract the CPU values from the provided top output.

        :param output: The text output from the top command.
        :param friendly_labels: Use friendly labels (e.g., "user" instead of "us") for CPU stats.
        :return: A dictionary with CPU stats as float values.
        """
        cpu_stats = {}
        cpu_labels = cpu_friendly_labels.copy() if friendly_labels else cpu_actual_labels.copy()
        cpu_labels.append("total")
        cpu_counter = 0
        grand_total = dict([(label, 0.0) for label in cpu_labels])

        for line in output.splitlines():
            if "Cpu" in line:
                line = line.replace(":", " ").replace(",", " ")
                stats = {}
                values = line.split()
                for label in cpu_actual_labels:
                    stats[cpu_labels[cpu_actual_labels.index(label)]] = float(values[values.index(label) - 1])
                stats["total"] = (
                    stats["user"] + stats["sys"] + stats["nice"]
                    if friendly_labels
                    else stats["us"] + stats["sy"] + stats["ni"]
                )
                for label in cpu_labels:
                    grand_total[label] += stats[label]
                cpu_stats[cpu_counter] = stats
                cpu_counter += 1
        cpu_stats[999] = grand_total
        return cpu_stats

    def _get_mem_from_top_output(self, output: str) -> Dict[str, Dict[str, float]]:
        """
        Extract the cpu values from provided top output.

        :param output: The unchanged text output from the top command
        :return: A dictionary with mem stats as float values
        """
        mem_stats = {}

        for line in output.splitlines():
            line = line.replace(":", " ").replace(",", " ")
            stats = {}
            buffer_pattern = "buff/cache" if "buff/cache" in line else "buffers"
            mem_labels.append(buffer_pattern)
            if buffer_pattern in line:
                for label in mem_labels:
                    label_pattern = re.search(rf"(?P<value>\d+.\d+)(\s+|\+)({label})", line)
                    if label_pattern:
                        stats[label] = float(label_pattern.group("value"))
                mem_stats["Mem"] = stats
                # add the memory scale
                mem_stats["Scale"] = line.split("Mem")[0]
            if "Swap" in line:
                swap_pattern = "avail" if "avail" in line else "cached Mem"
                swap_labels.append(swap_pattern)
                for label in swap_labels:
                    label_pattern = re.search(rf"(?P<value>\d+.\d+)(\s+|\+)({label})", line)
                    if label_pattern:
                        stats[label] = float(label_pattern.group("value"))
                mem_stats["Swap"] = stats

        return mem_stats

    def _get_proc_from_top_output(self, output: str, filter_proc: List) -> Dict[str, List[Union[int, float, str]]]:
        """
        Extract the Process values from the provided top output.

        :param output: The text output from the top command.
        :param filter_proc: List of filter words to match against the entire proc line.
        :return: A dictionary with process stats. Each key is a field label (COMMAND, PID, etc.).
        """
        proc_stats = {}
        section = "skip"
        for line in output.splitlines():
            if "Swap" in line and section == "skip":
                section = "start proc"
                continue
            if section == "start proc" and line:
                proc_labels = [field for field in line.split() if field.strip()]
                proc_stats = {label: [] for label in proc_labels}
                section = "proc"
            elif section == "proc" and all(filter_word in line for filter_word in filter_proc):
                field_values = line.split()
                proc_stats = self._update_proc_stats(proc_labels, field_values, proc_stats)
        return proc_stats

    def _update_proc_stats(self, proc_labels: List, values: List, proc_stats: Dict[str, List]) -> Dict[str, str]:
        """
        Update the process stat dictionary.

        :param proc_labels: Headers for the process stats.
        :param values: str/float/int value obtained from the top output
        :param proc_stats: dictionary containing the process stats
        :return: Dict with updated process stats.
        """
        for i, value in enumerate(values):
            try:
                if "." in value:
                    value = float(value)
                else:
                    value = int(value)
            except (TypeError, ValueError):
                pass
            try:
                if i < len(proc_labels):
                    proc_stats[proc_labels[i]].append(value)
                else:
                    proc_stats[proc_labels[-1]].append(f"{proc_stats[proc_labels[-1]][-1]} {value}")
            except IndexError:
                pass
        return proc_stats
