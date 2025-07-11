# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
import pytest
from mfd_connect import SSHConnection
from mfd_typing import OSName
from pytest_mock import MockerFixture

from mfd_host import Host
from mfd_host.feature.service import ESXiService


class TestESXiService:
    @pytest.fixture
    def host(self, mocker):
        _connection = mocker.create_autospec(SSHConnection)
        _connection.get_os_name.return_value = OSName.ESXI
        yield Host(connection=_connection)
        mocker.stopall()

    @pytest.fixture
    def esxi_service(self, host):
        yield host.service

    def test_restart_service(self, esxi_service: ESXiService, mocker: MockerFixture):
        service = "testservice"
        cmd = f"/etc/init.d/{service} restart"
        mock_execute = mocker.patch.object(esxi_service._connection, "execute_command")
        esxi_service.restart_service(service)
        mock_execute.assert_called_once_with(cmd, expected_return_codes={0})

    def test_restart_service_error(self, esxi_service: ESXiService, mocker: MockerFixture):
        service = "testservice"
        cmd = f"/etc/init.d/{service} restart"
        mock_execute = mocker.patch.object(esxi_service._connection, "execute_command", side_effect=RuntimeError)
        with pytest.raises(RuntimeError):
            esxi_service.restart_service(service)
        mock_execute.assert_called_once_with(cmd, expected_return_codes={0})
