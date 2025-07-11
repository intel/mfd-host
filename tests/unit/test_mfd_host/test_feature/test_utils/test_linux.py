# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
from ipaddress import IPv4Address
from textwrap import dedent
from unittest.mock import call

import pytest
from mfd_common_libs import log_levels
from mfd_connect import RPyCConnection
from mfd_connect.base import ConnectionCompletedProcess
from mfd_base_tool.exceptions import ToolNotAvailable
from mfd_typing import OSName
from mfd_model.config import HostModel

from mfd_host import Host
from mfd_host.exceptions import HostModuleException, UtilsFeatureExecutionError


class TestLinuxUtils:
    @pytest.fixture
    def host(self, mocker):
        _connection = mocker.create_autospec(RPyCConnection)
        _connection.get_os_name.return_value = OSName.LINUX

        model = HostModel(role="sut")

        yield Host(connection=_connection, topology=model)
        mocker.stopall()

    def test_remove_ssh_known_host(self, host):
        host.utils.remove_ssh_known_host(host_ip=IPv4Address("10.0.0.1"), ssh_client_config_dir="~/.ssh")
        host.connection.execute_command.assert_called_once_with("sed -i '/10.0.0.1/d' ~/.ssh/known_hosts", shell=True)

    @pytest.fixture()
    def get_program_cmd_patch(self, host, mocker):
        host.utils._get_program_cmd = mocker.create_autospec(
            host.utils._get_program_cmd, return_value="/usr/local/bin/kedr"
        )

    @pytest.mark.usefixtures("get_program_cmd_patch")
    def test_start_kedr(self, host):
        start_kedr_output = dedent(
            """\
        Starting KEDR...
       /sbin/insmod /lib/modules/3.10.0-514.el7.x86_64/extra/kedr.ko target_name=i40e
       /sbin/insmod /lib/modules/3.10.0-514.el7.x86_64/extra/kedr_leak_check.ko
       /sbin/insmod /lib/modules/3.10.0-514.el7.x86_64/extra/kedr_lc_common_mm.ko
       KEDR started."""
        )
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=start_kedr_output, return_code=0
        )
        host.utils.start_kedr("i40e")

    @pytest.mark.usefixtures("get_program_cmd_patch")
    def test_start_kedr_already_running(self, host):
        start_kedr_output = "kedr: Service is already running. To stop it, execute '/usr/local/bin/kedr stop'."

        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=start_kedr_output, return_code=1
        )
        with pytest.raises(
            HostModuleException, match="Attempted to start KEDR when it is already running. Bad cleanup?"
        ):
            host.utils.start_kedr("i40e")

    @pytest.mark.usefixtures("get_program_cmd_patch")
    def test_start_kedr_module_loaded(self, host):
        start_kedr_output = (
            "kedr: Service cannot be started because the target module is already loaded. "
            "Please unload the target module first."
        )
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=start_kedr_output, return_code=1
        )
        with pytest.raises(HostModuleException, match="You must unload the driver before starting KEDR"):
            host.utils.start_kedr("i40e")

    @pytest.mark.usefixtures("get_program_cmd_patch")
    def test_stop_kedr_success(self, host):
        stop_kedr_output = """Stopping KEDR...
        /sbin/rmmod /lib/modules/3.10.0-514.el7.x86_64/extra/kedr_lc_common_mm.ko
        /sbin/rmmod /lib/modules/3.10.0-514.el7.x86_64/extra/kedr_leak_check.ko
        /sbin/rmmod /lib/modules/3.10.0-514.el7.x86_64/extra/kedr.ko"""
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=stop_kedr_output, return_code=0
        )
        host.utils.stop_kedr()

    @pytest.mark.usefixtures("get_program_cmd_patch")
    def test_stop_kedr_module_loaded(self, host):
        stop_kedr_output = (
            "kedr: Service cannot be stopped because the target module is still loaded. "
            "Please unload the target module first"
        )
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=stop_kedr_output, return_code=1
        )
        with pytest.raises(HostModuleException, match="You must unload the driver before stopping KEDR"):
            host.utils.stop_kedr()

    @pytest.mark.usefixtures("get_program_cmd_patch")
    def test_stop_kedr_not_running(self, host, caplog):
        caplog.set_level(log_levels.MODULE_DEBUG)
        stop_kedr_output = "kedr: Service is not running."
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=stop_kedr_output, return_code=1
        )
        host.utils.stop_kedr()
        assert "KEDR was not running, no stop needed" in caplog.text

    def test_stop_kedr_missing_kedr(self, host, mocker):
        host.utils._get_program_cmd = mocker.create_autospec(
            host.utils._get_program_cmd, side_effect=ToolNotAvailable(returncode=1, cmd="")
        )
        with pytest.raises(ToolNotAvailable):
            host.utils.stop_kedr()

    def test_create_unprivileged_user(self, host):
        host.connection.execute_command.return_value = ConnectionCompletedProcess(args="", stdout="", return_code=0)
        cmd = "adduser user && echo 'user:password' | chpasswd"
        host.utils.create_unprivileged_user("user", "password")
        host.connection.execute_command.assert_called_once_with(cmd, shell=True)

    def test_delete_unprivileged_user(self, host):
        host.connection.execute_command.return_value = ConnectionCompletedProcess(args="", stdout="", return_code=0)
        cmd = "userdel -r user"
        host.utils.delete_unprivileged_user("user")
        host.connection.execute_command.assert_called_once_with(cmd)

    def test_set_icmp_echo(self, host):
        cmd_all = "echo '{}' > /proc/sys/net/ipv4/icmp_echo_ignore_all"
        cmd_broadcasts = "echo '{}' > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts"

        host.utils.set_icmp_echo(ignore_all=True, ignore_broadcasts=True)
        host.connection.execute_command.assert_has_calls(
            [
                call(cmd_all.format(1), shell=True),
                call(cmd_broadcasts.format(1), shell=True),
            ]
        )

        host.utils.set_icmp_echo(ignore_all=False, ignore_broadcasts=False)
        host.connection.execute_command.assert_has_calls(
            [
                call(cmd_all.format(0), shell=True),
                call(cmd_broadcasts.format(0), shell=True),
            ]
        )

    def test_get_pretty_name_found(self, host):
        output = ConnectionCompletedProcess(
            "",
            stdout='PRETTY_NAME="SUSE Linux Enterprise Server 15 SP7"',
            return_code=0,
        )
        expected_output = "SUSE Linux Enterprise Server 15 SP7"

        host.connection.execute_command.return_value = output

        assert expected_output == host.utils.get_pretty_name()

    def test_get_pretty_name_not_found(self, host):
        host.connection.execute_command.side_effect = UtilsFeatureExecutionError(returncode=1, cmd="")

        with pytest.raises(UtilsFeatureExecutionError):
            host.utils.get_pretty_name()
