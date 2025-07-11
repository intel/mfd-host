# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
from textwrap import dedent

import pytest
from mfd_connect import SSHConnection
from mfd_connect.base import ConnectionCompletedProcess
from mfd_host import Host
from mfd_host.exceptions import CPUFeatureExecutionError, CPUFeatureException
from mfd_network_adapter.data_structures import State
from mfd_typing import OSName


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
