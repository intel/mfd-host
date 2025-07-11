# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT

import pytest
from mfd_common_libs import log_levels
from mfd_connect import SSHConnection
from mfd_typing import OSName
from netaddr.ip import IPAddress

from mfd_host import Host
from mfd_host.exceptions import ServiceFeatureException


class TestLinuxService:
    @pytest.fixture
    def host(self, mocker):
        _connection = mocker.create_autospec(SSHConnection)
        _connection.get_os_name.return_value = OSName.LINUX
        _connection.ip = IPAddress("1.1.1.1")
        yield Host(connection=_connection)
        mocker.stopall()

    @pytest.fixture
    def linux_service(self, host):
        yield host.service

    def test_restart_service(self, linux_service, caplog):
        linux_service._connection.execute_command.return_value.return_code = 0
        linux_service.restart_service("test_service")
        linux_service._connection.execute_command.assert_called_with(
            "service test_service restart", expected_return_codes={0, 1, 127}
        )

    def test_restart_service_systemctl(self, linux_service, caplog):
        linux_service._connection.execute_command.return_value.return_code = 1
        linux_service.restart_service("test_service")
        linux_service._connection.execute_command.assert_called_with(
            "systemctl restart test_service", expected_return_codes={0}
        )

    def test_restart_libvirtd(self, linux_service):
        linux_service._connection.execute_command.return_value.return_code = 0
        linux_service.restart_libvirtd()
        linux_service._connection.execute_command.assert_called_with(
            "service libvirtd restart", expected_return_codes={0, 1, 127}
        )

    def test_start_irqbalance(self, linux_service):
        linux_service.start_irqbalance()
        linux_service._connection.execute_command.assert_called_with("irqbalance")

    def test_stop_irqbalance(self, linux_service, mocker):
        stop_mock = mocker.patch("mfd_host.feature.service.linux.stop_process_by_name")
        linux_service.stop_irqbalance()
        stop_mock.assert_called_with(linux_service._connection, "irqbalance")

    def test_get_service_state_running(self, linux_service, caplog):
        caplog.set_level(log_levels.MODULE_DEBUG)
        linux_service._connection.execute_command.return_value.stdout = "1\n"
        assert linux_service.is_service_running("test_service")
        assert "test_service is present and running" in caplog.text

    def test_get_service_state_not_running(self, linux_service, caplog):
        caplog.set_level(log_levels.MODULE_DEBUG)
        linux_service._connection.execute_command.return_value.stdout = "0\n"
        assert not linux_service.is_service_running("test_service")
        assert "test_service is not running or no service is present" in caplog.text

    def test_nm_get_service_state(self, linux_service):
        linux_service.is_network_manager_running()
        linux_service._connection.execute_command.assert_called_with(
            'systemctl status NetworkManager 2>&1 | grep -i "active" | grep "running" | wc -l',
            shell=True,
            expected_return_codes={0},
        )

    def test_set_network_manager_enable(self, linux_service, caplog, mocker):
        linux_service._connection.execute_command.return_value.return_code = 0
        caplog.set_level(log_levels.MODULE_DEBUG)
        calls = [
            mocker.call("systemctl unmask NetworkManager.service", expected_return_codes=None),
            mocker.call("systemctl start NetworkManager.service", expected_return_codes=None),
            mocker.call("systemctl enable NetworkManager.service", expected_return_codes=None),
        ]
        linux_service.set_network_manager(enable=True)
        linux_service._connection.execute_command.assert_has_calls(calls)

    def test_set_network_manager_disable(self, linux_service, caplog, mocker):
        caplog.set_level(log_levels.MODULE_DEBUG)
        linux_service._connection.execute_command.return_value.return_code = 0
        linux_service.set_network_manager(enable=False)
        calls = [
            mocker.call("systemctl stop NetworkManager.service", expected_return_codes=None),
            mocker.call("systemctl disable NetworkManager.service", expected_return_codes=None),
            mocker.call("systemctl mask NetworkManager.service", expected_return_codes=None),
        ]
        linux_service._connection.execute_command.assert_has_calls(calls)

    def test_set_network_manager_exception(self, linux_service):
        linux_service._connection.execute_command.return_value.return_code = 1
        with pytest.raises(ServiceFeatureException, match="Unable to unmask on 1.1.1.1"):
            linux_service.set_network_manager(enable=True)

    def test_set_network_manager_already_disable(self, linux_service, caplog, mocker):
        caplog.set_level(log_levels.MODULE_DEBUG)
        linux_service._connection.execute_command.return_value.return_code = 1
        linux_service._connection.execute_command.return_value.stdout = "Unit NetworkManager.service not loaded."
        linux_service.set_network_manager(enable=False)
        calls = [
            mocker.call("systemctl stop NetworkManager.service", expected_return_codes=None),
            mocker.call("systemctl disable NetworkManager.service", expected_return_codes=None),
            mocker.call("systemctl mask NetworkManager.service", expected_return_codes=None),
        ]
        linux_service._connection.execute_command.assert_has_calls(calls)
        assert any("NetworkManager stop on 1.1.1.1 is already done." in record.message for record in caplog.records)
