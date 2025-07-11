# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT

import pytest
from mfd_connect import SSHConnection
from mfd_host import Host
from mfd_sysctl import Sysctl
from mfd_sysctl.freebsd import FreebsdSysctl
from mfd_typing import OSName


class TestFreeBSDCPU:
    @pytest.fixture
    def host(self, mocker):
        mocker.patch("mfd_sysctl.Sysctl.check_if_available", mocker.create_autospec(Sysctl.check_if_available))
        mocker.patch(
            "mfd_sysctl.Sysctl.get_version",
            mocker.create_autospec(Sysctl.get_version, return_value="N/A"),
        )
        mocker.patch(
            "mfd_sysctl.Sysctl._get_tool_exec_factory",
            mocker.create_autospec(Sysctl._get_tool_exec_factory, return_value="sysctl"),
        )
        _connection = mocker.create_autospec(SSHConnection)
        _connection.get_os_name.return_value = OSName.FREEBSD
        yield Host(connection=_connection)
        mocker.stopall()

    def test_get_log_cpu_no(self, host, mocker):
        mocker.patch(
            "mfd_sysctl.freebsd.FreebsdSysctl.get_log_cpu_no",
            mocker.create_autospec(FreebsdSysctl.get_log_cpu_no, return_value=96),
        )
        assert host.cpu.get_log_cpu_no() == 96
        FreebsdSysctl.get_log_cpu_no.assert_called()
