# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
from textwrap import dedent
from unittest.mock import call

import pytest
from mfd_connect import RPyCConnection
from mfd_connect.base import ConnectionCompletedProcess
from mfd_host import Host
from mfd_host.exceptions import CPUFeatureExecutionError, CPUFeatureException
from mfd_host.feature.cpu.const import COREINFO_REGISTRY_PATH, COREINFO_EXE_PATH
from mfd_host.feature.cpu.windows import WindowsCPU
from mfd_network_adapter.data_structures import State
from mfd_typing import OSName


class TestWindowsCPU:
    core_info_output = [
        {"DeviceID": "CPU0", "NumberOfCores": "18", "NumberOfLogicalProcessors": "36"},
        {"DeviceID": "CPU1", "NumberOfCores": "18", "NumberOfLogicalProcessors": "36"},
    ]

    @pytest.fixture
    def host(self, mocker):
        _connection = mocker.create_autospec(RPyCConnection)
        _connection.get_os_name.return_value = OSName.WINDOWS
        yield Host(connection=_connection)
        mocker.stopall()

    def test_get_core_info(self, host):
        output = dedent(
            """DeviceID                  : CPU0
            NumberOfCores             : 18
            NumberOfLogicalProcessors : 36

            DeviceID                  : CPU1
            NumberOfCores             : 18
            NumberOfLogicalProcessors : 36"""
        )
        host.connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr=""
        )
        cmd = "Get-WmiObject -class Win32_processor | select DeviceID, NumberOfCores, NumberOfLogicalProcessors | fl"
        assert self.core_info_output == host.cpu.get_core_info()
        host.connection.execute_powershell.assert_called_once_with(cmd, custom_exception=CPUFeatureExecutionError)

    def test_is_hyperthreading_enabled(self, host, mocker):
        mocker.patch(
            "mfd_host.feature.cpu.windows.WindowsCPU.get_core_info",
            mocker.create_autospec(WindowsCPU.get_core_info, return_value=self.core_info_output),
        )
        assert host.cpu.get_hyperthreading_state() is State.ENABLED
        host.cpu.get_core_info.assert_called()

    def test_is_hyperthreading_disabled(self, host, mocker):
        core_info_output = [
            {"DeviceID": "CPU0", "NumberOfCores": "36", "NumberOfLogicalProcessors": "18"},
            {"DeviceID": "CPU1", "NumberOfCores": "36", "NumberOfLogicalProcessors": "18"},
        ]
        mocker.patch(
            "mfd_host.feature.cpu.windows.WindowsCPU.get_core_info",
            mocker.create_autospec(WindowsCPU.get_core_info, return_value=core_info_output),
        )
        assert host.cpu.get_hyperthreading_state() is State.DISABLED
        host.cpu.get_core_info.assert_called()

    def test_get_phy_cpu_no(self, host):
        output = dedent(
            """__GENUS          : 2
            __CLASS          : Win32_Processor
            __SUPERCLASS     :
            __DYNASTY        :
            __RELPATH        :
            __PROPERTY_COUNT : 1
            __DERIVATION     : {}
            __SERVER         :
            __NAMESPACE      :
            __PATH           :
            NumberOfCores    : 18
            PSComputerName   :

            __GENUS          : 2
            __CLASS          : Win32_Processor
            __SUPERCLASS     :
            __DYNASTY        :
            __RELPATH        :
            __PROPERTY_COUNT : 1
            __DERIVATION     : {}
            __SERVER         :
            __NAMESPACE      :
            __PATH           :
            NumberOfCores    : 18
            PSComputerName   :"""
        )
        host.connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr=""
        )
        cmd = "gwmi win32_processor -Property NumberOfCores"
        assert 36 == host.cpu.get_phy_cpu_no()
        host.connection.execute_powershell.assert_called_once_with(cmd, custom_exception=CPUFeatureExecutionError)

    def test_get_phy_cpu_no_exception(self, host):
        host.connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout="", stderr=""
        )
        cmd = "gwmi win32_processor -Property NumberOfCores"
        with pytest.raises(CPUFeatureException, match="Cannot find number of physical processors: "):
            assert 36 == host.cpu.get_phy_cpu_no()
            host.connection.execute_powershell.assert_called_once_with(cmd, custom_exception=CPUFeatureExecutionError)

    def test_accept_sysinternals_eula(self, host, mocker):
        host.connection.execute_powershell.side_effect = [
            ConnectionCompletedProcess(return_code=0, args="command", stdout="", stderr="stderr"),
            ConnectionCompletedProcess(return_code=0, args="command", stdout="", stderr="stderr"),
        ]
        eula_new_item = rf"new-item -path '{COREINFO_REGISTRY_PATH}' -Force"
        set_eula = f"set-itemproperty -path '{COREINFO_REGISTRY_PATH}' -Name {'EulaAccepted'} -Value {1}"
        assert host.cpu._accept_sysinternals_eula(COREINFO_REGISTRY_PATH) is None
        host.connection.execute_powershell.assert_has_calls(
            [
                call(eula_new_item, custom_exception=CPUFeatureExecutionError),
                call(set_eula, custom_exception=CPUFeatureExecutionError),
            ]
        )

    def test_get_numa_node_count(self, host, mocker):
        output = dedent(
            """
            Logical Processor to NUMA Node Map:
            NUMA Node 0:
            ************************************
            ------------------------------------
            NUMA Node 1:
            ------------------------------------
            ************************************"""
        )
        mocker.patch(
            "mfd_host.feature.cpu.windows.WindowsCPU._accept_sysinternals_eula",
            mocker.create_autospec(WindowsCPU._accept_sysinternals_eula, return_value=None),
        )
        host.connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr="stderr"
        )
        assert host.cpu.get_numa_node_count() == 2
        host.connection.execute_powershell.assert_called_with(
            f"{COREINFO_EXE_PATH}\\Coreinfo.exe -n", custom_exception=CPUFeatureExecutionError
        )
        host.cpu._accept_sysinternals_eula.assert_called()

    def test_get_log_cpu_no(self, host):
        output = dedent(
            """\
            __GENUS                   : 2
            __CLASS                   : Win32_ComputerSystem
            __SUPERCLASS              :
            __DYNASTY                 :
            __RELPATH                 :
            __PROPERTY_COUNT          : 1
            __DERIVATION              : {}
            __SERVER                  :
            __NAMESPACE               :
            __PATH                    :
            NumberOfLogicalProcessors : 72
            PSComputerName            : """
        )
        host.connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr=""
        )
        cmd = "gwmi win32_computersystem -Property NumberOfLogicalProcessors"
        assert 72 == host.cpu.get_log_cpu_no()
        host.connection.execute_powershell.assert_called_once_with(cmd)

    def test_get_log_cpu_no_fail(self, host):
        host.connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout="Output", stderr=""
        )
        with pytest.raises(CPUFeatureException, match="Failed to fetch the processors count on interface"):
            host.cpu.get_log_cpu_no()

    def test_set_groupsize(self, host, mocker):
        output = "The operation completed successfully.\n"
        mocker.patch(
            "mfd_host.feature.cpu.windows.WindowsCPU.get_log_cpu_no",
            mocker.create_autospec(WindowsCPU.get_log_cpu_no, return_value=72),
        )
        host.connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr=""
        )
        maxsize = 64
        cmd = f"bcdedit /set groupsize {maxsize}"
        assert host.cpu.set_groupsize(maxsize) is None
        host.connection.execute_powershell.assert_called_once_with(cmd, custom_exception=CPUFeatureExecutionError)

    def test_set_groupsize_cpu_less_than_logical(self, host, mocker):
        mocker.patch(
            "mfd_host.feature.cpu.windows.WindowsCPU.get_log_cpu_no",
            mocker.create_autospec(WindowsCPU.get_log_cpu_no, return_value=72),
        )
        host.connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout="", stderr=""
        )
        maxsize = 65
        with pytest.raises(
            CPUFeatureException, match="Maxsize for processors should be less than logical processors and power of two"
        ):
            assert host.cpu.set_groupsize(maxsize)

    def test_set_groupsize_failed(self, host, mocker):
        output = "The operation Failed.\n"
        mocker.patch(
            "mfd_host.feature.cpu.windows.WindowsCPU.get_log_cpu_no",
            mocker.create_autospec(WindowsCPU.get_log_cpu_no, return_value=72),
        )
        host.connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="command", stdout=output, stderr=""
        )
        maxsize = 64
        cmd = f"bcdedit /set groupsize {maxsize}"
        with pytest.raises(CPUFeatureException, match="Failed to set CPU groupsize"):
            assert host.cpu.set_groupsize(maxsize) is None
        host.connection.execute_powershell.assert_called_once_with(cmd, custom_exception=CPUFeatureExecutionError)
