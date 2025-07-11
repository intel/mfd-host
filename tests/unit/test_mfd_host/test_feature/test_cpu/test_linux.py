# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
from textwrap import dedent

import pytest
from mfd_connect import SSHConnection
from mfd_connect.base import ConnectionCompletedProcess
from mfd_host import Host
from mfd_host.exceptions import CPUFeatureExecutionError, CPUFeatureException
from mfd_typing import OSName


class TestLinuxCPU:
    @pytest.fixture
    def host(self, mocker):
        _connection = mocker.create_autospec(SSHConnection)
        _connection.get_os_name.return_value = OSName.LINUX
        yield Host(connection=_connection)
        mocker.stopall()

    def test_display_stats_only(self, host):
        output = dedent(
            """\
            Linux 4.4.0-127-generic (kmc-traffic4)12/01/2023 \t_x86_64_\t(32 CPU)
            12:16:23 PM  CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
            12:16:23 PM  all    0.06    0.00    0.03    0.00    0.00    0.00    0.00    0.00    0.00   99.91
            12:16:23 PM    0    0.26    0.00    0.09    0.00    0.00    0.00    0.00    0.00    0.00   99.65
            12:16:23 PM    1    0.16    0.00    0.05    0.00    0.00    0.00    0.00    0.00    0.00   99.79
            12:16:23 PM    2    0.11    0.00    0.04    0.00    0.00    0.00    0.00    0.00    0.00   99.86
            12:16:23 PM    3    0.08    0.00    0.03    0.00    0.00    0.00    0.00    0.00    0.00   99.88
            12:16:23 PM    4    0.08    0.00    0.03    0.00    0.00    0.00    0.00    0.00    0.00   99.88
            12:16:23 PM    5    0.12    0.00    0.04    0.00    0.00    0.00    0.00    0.00    0.00   99.85"""
        )
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr=""
        )
        assert host.cpu.display_cpu_stats_only() == output
        host.connection.execute_command.assert_called_once_with(
            "mpstat -P ALL", custom_exception=CPUFeatureExecutionError
        )

    def test_get_cpu_stats(self, host):
        expected = {
            "all": {
                "usr": "0.06",
                "nice": "0.00",
                "sys": "0.03",
                "iowait": "0.00",
                "irq": "0.00",
                "soft": "0.00",
                "steal": "0.00",
                "guest": "0.00",
                "gnice": "0.00",
                "idle": "99.91",
                "intr/s": "122.44",
            },
            "0": {
                "usr": "0.26",
                "nice": "0.00",
                "sys": "0.09",
                "iowait": "0.00",
                "irq": "0.00",
                "soft": "0.00",
                "steal": "0.00",
                "guest": "0.00",
                "gnice": "0.00",
                "idle": "99.65",
                "intr/s": "9.86",
            },
            "1": {
                "usr": "0.16",
                "nice": "0.00",
                "sys": "0.05",
                "iowait": "0.00",
                "irq": "0.00",
                "soft": "0.00",
                "steal": "0.00",
                "guest": "0.00",
                "gnice": "0.00",
                "idle": "99.79",
                "intr/s": "9.29",
            },
            "2": {
                "usr": "0.11",
                "nice": "0.00",
                "sys": "0.04",
                "iowait": "0.00",
                "irq": "0.00",
                "soft": "0.00",
                "steal": "0.00",
                "guest": "0.00",
                "gnice": "0.00",
                "idle": "99.86",
                "intr/s": "7.08",
            },
            "3": {
                "usr": "0.08",
                "nice": "0.00",
                "sys": "0.03",
                "iowait": "0.00",
                "irq": "0.00",
                "soft": "0.00",
                "steal": "0.00",
                "guest": "0.00",
                "gnice": "0.00",
                "idle": "99.88",
                "intr/s": "6.90",
            },
        }
        output = dedent(
            """\
            Linux 4.4.0-127-generic (kmc-traffic4) \t12/01/2023 \t_x86_64_\t(32 CPU)

            03:53:03 PM  CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
            03:53:03 PM  all    0.06    0.00    0.03    0.00    0.00    0.00    0.00    0.00    0.00   99.91
            03:53:03 PM    0    0.26    0.00    0.09    0.00    0.00    0.00    0.00    0.00    0.00   99.65
            03:53:03 PM    1    0.16    0.00    0.05    0.00    0.00    0.00    0.00    0.00    0.00   99.79
            03:53:03 PM    2    0.11    0.00    0.04    0.00    0.00    0.00    0.00    0.00    0.00   99.86
            03:53:03 PM    3    0.08    0.00    0.03    0.00    0.00    0.00    0.00    0.00    0.00   99.88

            03:53:03 PM  CPU    intr/s
            03:53:03 PM  all    122.44
            03:53:03 PM    0      9.86
            03:53:03 PM    1      9.29
            03:53:03 PM    2      7.08
            03:53:03 PM    3      6.90

            """
        )
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr=""
        )
        assert host.cpu.get_cpu_stats() == expected
        host.connection.execute_command.assert_called_once_with("mpstat -A", custom_exception=CPUFeatureExecutionError)

    def test_get_log_cpu_no(self, host):
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout="32\n", stderr=""
        )
        assert host.cpu.get_log_cpu_no() == 32
        host.connection.execute_command.assert_called_once_with("nproc", custom_exception=CPUFeatureExecutionError)

    def test_get_log_cpu_no_fail(self, host):
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout="output", stderr=""
        )
        with pytest.raises(CPUFeatureException, match="Invalid number of logical CPU found: output"):
            assert host.cpu.get_log_cpu_no()
        host.connection.execute_command.assert_called_once_with("nproc", custom_exception=CPUFeatureExecutionError)

    def test_affinitize_queues_to_cpus(self, host):
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout="", stderr=""
        )
        scriptdir = "/root/ice-1.7.0_rc75/scripts"
        assert host.cpu.affinitize_queues_to_cpus("ens5f1", scriptdir) is None
        host.connection.execute_command.assert_called_once_with(
            command="./set_irq_affinity ens5f1",
            cwd=scriptdir,
            custom_exception=CPUFeatureExecutionError,
            shell=True,
            expected_return_codes={0, 2},
        )

    def test_affinitize_queues_to_cpus_exception(self, host):
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=1, args="command", stdout="", stderr="stderr"
        )
        scriptdir = "/root/ice-1.7.0_rc75/scripts"
        with pytest.raises(CPUFeatureException, match="Found Error while executing set_irq_affinity script"):
            assert host.cpu.affinitize_queues_to_cpus("ens5f1", scriptdir) is None
        host.connection.execute_command.assert_called_once_with(
            command="./set_irq_affinity ens5f1",
            cwd=scriptdir,
            custom_exception=CPUFeatureExecutionError,
            shell=True,
            expected_return_codes={0, 2},
        )
