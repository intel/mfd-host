# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT

import pytest
from mfd_connect import RPyCConnection
from mfd_typing import OSName
from mfd_model.config import HostModel

from mfd_host import Host


class TestFreeBSDUtils:
    @pytest.fixture
    def host(self, mocker):
        connection = mocker.create_autospec(RPyCConnection)
        connection.get_os_name.return_value = OSName.FREEBSD

        model = HostModel(role="sut")

        yield Host(connection=connection, topology=model)

        mocker.stopall()

    def test_set_icmp_echo(self, host):
        cmd_broadcasts = "sysctl net.inet.icmp.bmcastecho={}"

        host.utils.set_icmp_echo(ignore_broadcasts=True)
        host.connection.execute_command.assert_called_once_with(cmd_broadcasts.format(0))

        host.connection.execute_command.reset_mock()
        host.utils.set_icmp_echo(ignore_broadcasts=False)
        host.connection.execute_command.assert_called_once_with(cmd_broadcasts.format(1))
