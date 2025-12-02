# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
from textwrap import dedent

import pytest
from mfd_common_libs import log_levels
from mfd_connect import SSHConnection
from mfd_connect.base import ConnectionCompletedProcess
from mfd_host import Host
from mfd_host.exceptions import CPUFeatureExecutionError, CPUFeatureException
from mfd_network_adapter.data_structures import State
from mfd_typing import OSName

from mfd_host.feature.cpu import ESXiCPU


class TestESXiCPU:
    cpu_attribute_output = dedent(
        """
        CPU Packages: 2
        CPU Cores: 64
        CPU Threads: 128
        Hyperthreading Active: true
        Hyperthreading Supported: true
        Hyperthreading Enabled: true
        HV Support: 3"""
    )

    @pytest.fixture
    def host(self, mocker):
        _connection = mocker.create_autospec(SSHConnection)
        _connection.get_os_name.return_value = OSName.ESXI
        yield Host(connection=_connection)
        mocker.stopall()

    def test_cpu_packages(self, host, mocker):
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=self.cpu_attribute_output, stderr=""
        )
        cmd = "esxcli hardware cpu global get"
        assert host.cpu.packages() == 2
        host.connection.execute_command.assert_called_once_with(cmd, custom_exception=CPUFeatureExecutionError)

    def test_cpu_cores(self, host, mocker):
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=self.cpu_attribute_output, stderr=""
        )
        cmd = "esxcli hardware cpu global get"
        assert host.cpu.cores() == 64
        host.connection.execute_command.assert_called_once_with(cmd, custom_exception=CPUFeatureExecutionError)

    def test_cpu_threads(self, host, mocker):
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=self.cpu_attribute_output, stderr=""
        )
        cmd = "esxcli hardware cpu global get"
        assert host.cpu.threads() == 128
        host.connection.execute_command.assert_called_once_with(cmd, custom_exception=CPUFeatureExecutionError)

    def test_cpu_attributes_fail(self, host, mocker):
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout="", stderr=""
        )
        cmd = "esxcli hardware cpu global get"
        with pytest.raises(CPUFeatureException, match="Unable to fetch CPU Attribute: CPU Packages"):
            host.cpu._cpu_attributes("CPU Packages")
        host.connection.execute_command.assert_called_once_with(cmd, custom_exception=CPUFeatureExecutionError)

    def test_set_numa_affinity_enabled(self, host, mocker):
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout="", stderr=""
        )
        cmd = 'esxcli system settings advanced set --default -o "/Numa/LocalityWeightActionAffinity"'
        assert host.cpu.set_numa_affinity(State.ENABLED) is None
        host.connection.execute_command.assert_called_once_with(cmd, custom_exception=CPUFeatureExecutionError)

    def test_set_numa_affinity_disabled(self, host, mocker):
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout="", stderr=""
        )
        cmd = 'esxcli system settings advanced set -i 0 -o "/Numa/LocalityWeightActionAffinity"'
        assert host.cpu.set_numa_affinity(State.DISABLED) is None
        host.connection.execute_command.assert_called_once_with(cmd, custom_exception=CPUFeatureExecutionError)

    def test_start_cpu_measurement_returns_process_handle(self, host, mocker):
        mock_connection = mocker.Mock()
        mock_process = mocker.Mock()
        mock_connection.start_process.return_value = mock_process
        host.cpu._connection = mock_connection

        result = host.cpu.start_cpu_measurement()

        assert result == mock_process
        mock_connection.start_process.assert_called_once_with(command="esxtop -b -n 8 -d3", log_file=True, shell=True)

    def test_logs_debug_message_when_starting_cpu_measurement(self, host, mocker):
        mock_logger = mocker.patch("mfd_host.feature.cpu.esxi.logger")

        host.cpu.start_cpu_measurement()

        mock_logger.log.assert_called_once_with(level=log_levels.MODULE_DEBUG, msg="Start CPU measurement on host")

    def test_parses_average_cpu_usage(self, host, mocker):
        mock_connection = mocker.MagicMock()
        mock_process = mocker.MagicMock()
        mock_process.log_path = "/tmp/esxtop.log"
        mock_connection.path.return_value.read_text.return_value = 'Header\n"10"\n"20"\n"30"\n"40"\n"50"\n'
        mock_connection.path.return_value.__enter__.return_value = mock_connection.path.return_value
        host.cpu._connection = mock_connection

        result = host.cpu.parse_cpu_usage("vm1", mock_process)
        assert result == 30  # (10+20+30+40+50)//5

    def test_returns_zero_when_no_cpu_samples_found(self, host, mocker):
        mock_connection = mocker.MagicMock()
        mock_process = mocker.MagicMock()
        mock_process.log_path = "/tmp/esxtop.log"
        mock_connection.path.return_value.read_text.return_value = "Header\n"
        mock_connection.path.return_value.__enter__.return_value = mock_connection.path.return_value
        host.cpu._connection = mock_connection

        result = host.cpu.parse_cpu_usage("vm1", mock_process)
        assert result == 0

    def test_skips_lines_that_cannot_be_converted_to_float(self, host, mocker):
        mock_connection = mocker.MagicMock()
        mock_process = mocker.MagicMock()
        mock_process.log_path = "/tmp/esxtop.log"
        mock_connection.path.return_value.read_text.return_value = 'Header\n"10"\n"invalid"\n"30"\n"40"\n"50"\n'
        mock_connection.path.return_value.__enter__.return_value = mock_connection.path.return_value
        host.cpu._connection = mock_connection

        result = host.cpu.parse_cpu_usage("vm1", mock_process)
        assert result == 32  # (10+30+40+50)//4

    def test_raises_runtime_error_when_file_read_fails(self, host, mocker):
        mock_connection = mocker.MagicMock()
        mock_process = mocker.MagicMock()
        mock_process.log_path = "/tmp/esxtop.log"
        mock_connection.path.return_value.read_text.side_effect = Exception("File error")
        mock_connection.path.return_value.__enter__.return_value = mock_connection.path.return_value
        host.cpu._connection = mock_connection

        with pytest.raises(
            RuntimeError,
            match="Failed to read parsed CPU usage output file due to - File error.",
        ):
            host.cpu.parse_cpu_usage("vm1", mock_process)

    def test_parses_cpu_usage_when_process_not_running(self, host, mocker):
        mock_process = mocker.Mock()
        mock_process.running = False
        mock_parse = mocker.patch.object(ESXiCPU, "parse_cpu_usage", return_value=7)
        host.cpu._connection = mocker.Mock()
        result = host.cpu.stop_cpu_measurement(mock_process, "vm4")
        assert result == 7
        mock_parse.assert_called_once_with(process_name="vm4", process=mock_process)

    def test_stop_fail_when_process_running(self, host, mocker):
        mock_process = mocker.Mock()
        mock_process.running = True
        mocker.patch("mfd_host.feature.cpu.esxi.TimeoutCounter", autospec=True, spec_set=True)
        host.cpu._connection = mocker.Mock()
        with pytest.raises(RuntimeError, match="CPU measurement process is still running after stop and kill."):
            host.cpu.stop_cpu_measurement(mock_process, "vm4")
