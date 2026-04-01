# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: MIT

import pytest
from mfd_common_libs import log_levels
from mfd_connect import RPyCConnection
from mfd_connect.base import ConnectionCompletedProcess
from mfd_typing import OSName

from mfd_host import Host
from mfd_host.feature.service.windows import WindowsService


class TestWindowsService:
    @pytest.fixture
    def host(self, mocker):
        _connection = mocker.create_autospec(RPyCConnection)
        _connection.get_os_name.return_value = OSName.WINDOWS
        yield Host(connection=_connection)
        mocker.stopall()

    @pytest.fixture
    def windows_service(self, host):
        yield host.service

    def test_restart_service(self, windows_service: WindowsService):
        service_name = "TestService"
        windows_service.restart_service(service_name)
        windows_service._connection.execute_powershell.assert_called_once_with(
            'Restart-Service -Name "TestService" -Force',
            expected_return_codes={0},
        )

    def test_restart_service_logs(self, windows_service: WindowsService, caplog):
        caplog.set_level(log_levels.MODULE_DEBUG)
        service_name = "TestService"
        windows_service.restart_service(service_name)
        assert f"Restarting service '{service_name}'" in caplog.text

    def test_restart_service_raises_on_error(self, windows_service: WindowsService):
        service_name = "TestService"
        windows_service._connection.execute_powershell.side_effect = RuntimeError("Command failed")
        with pytest.raises(RuntimeError):
            windows_service.restart_service(service_name)

    def test_get_service_status(self, windows_service: WindowsService):
        service_name = "TestService"
        expected_status = "Running"
        windows_service._connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=f"  {expected_status}  ", stderr=""
        )
        result = windows_service.get_service_status(service_name)
        windows_service._connection.execute_powershell.assert_called_once_with(
            '(Get-Service -Name "TestService").Status',
            expected_return_codes={0},
        )
        assert result == expected_status

    def test_get_service_status_stopped(self, windows_service: WindowsService):
        service_name = "TestService"
        windows_service._connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout="Stopped\n", stderr=""
        )
        result = windows_service.get_service_status(service_name)
        assert result == "Stopped"

    def test_get_service_status_logs(self, windows_service: WindowsService, caplog):
        caplog.set_level(log_levels.MODULE_DEBUG)
        service_name = "TestService"
        windows_service._connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout="Running\n", stderr=""
        )
        windows_service.get_service_status(service_name)
        assert f"Getting service '{service_name}'" in caplog.text

    def test_get_service_status_raises_on_error(self, windows_service: WindowsService):
        service_name = "TestService"
        windows_service._connection.execute_powershell.side_effect = RuntimeError("Command failed")
        with pytest.raises(RuntimeError):
            windows_service.get_service_status(service_name)
