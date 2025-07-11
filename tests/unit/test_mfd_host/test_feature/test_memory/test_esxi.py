# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module to Test ESXi Memory."""

import pytest
from textwrap import dedent
from mfd_host import Host

from mfd_model.config import HostModel
from mfd_connect import RPyCConnection
from mfd_connect.base import ConnectionCompletedProcess
from mfd_typing.os_values import OSName

from mfd_host.feature.memory.exceptions import ServerMemoryNotFoundError


class TestESXIMemory:
    """Module to Test ESXi memory."""

    @pytest.fixture
    def host(self, mocker):
        _connection = mocker.create_autospec(RPyCConnection)
        _connection.get_os_name.return_value = OSName.ESXI
        model = HostModel(role="sut")
        yield Host(connection=_connection, topology=model)
        mocker.stopall()

    def test_ram(self, host):
        output = dedent(
            """\
        Physical Memory: 17169526784
        Reliable Memory: 0 Bytes
        NUMA Node Count: 1
        """
        )
        expected_output = 17169526784
        host.memory._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0
        )
        assert host.memory.ram == expected_output

    def test_ram_not_found(self, host):
        output = ""
        host.memory._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=output, return_code=0
        )
        with pytest.raises(ServerMemoryNotFoundError):
            _ = host.memory.ram
