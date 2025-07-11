# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
from textwrap import dedent

import pytest
from mfd_connect import RPyCConnection
from mfd_connect.base import ConnectionCompletedProcess
from mfd_typing import OSName, OSBitness

from mfd_host import Host


class TestFreeBsdStats:
    @pytest.fixture
    def host(self, mocker):
        _connection = mocker.create_autospec(RPyCConnection)
        _connection.get_os_name.return_value = OSName.FREEBSD
        _connection.get_os_bitness.return_value = OSBitness.OS_64BIT

        host = Host(connection=_connection)
        host.stats._sysctl._connection.get_os_name.return_value = OSName.FREEBSD
        yield host
        mocker.stopall()

    def test_get_cpu_utilization(self, host: "Host") -> None:
        cmd_out1 = dedent("""318296 0 851573 1184 48928953 741982 0 508403 29 48748606""")
        cmd_out2 = dedent("""318296 0 851614 1184 48980982 825573 0 525792 33 48901640""")
        expected_out1 = {
            "0": {"user": 0.64, "nice": 0.0, "system": 1.7, "interrupt": 0.0, "idle": 97.66},
            "1": {"user": 1.48, "nice": 0.0, "system": 1.02, "interrupt": 0.0, "idle": 97.5},
            "all": {"user": 1.06, "nice": 0.0, "system": 1.36, "interrupt": 0.0, "idle": 97.58},
        }
        expected_out2 = {
            "0": {"user": 0.0, "nice": 0.0, "system": 0.08, "interrupt": 0.0, "idle": 99.92},
            "1": {"user": 32.91, "nice": 0.0, "system": 6.85, "interrupt": 0.0, "idle": 60.25},
            "all": {"user": 27.31, "nice": 0.0, "system": 5.69, "interrupt": 0.0, "idle": 66.99},
        }
        host.connection.execute_command.side_effect = [
            ConnectionCompletedProcess(return_code=0, args="", stdout=cmd_out1, stderr=""),
            ConnectionCompletedProcess(return_code=0, args="", stdout=cmd_out2, stderr=""),
        ]
        out = host.stats.get_cpu_utilization()
        assert out == expected_out1
        out = host.stats.get_cpu_utilization()
        assert out == expected_out2

    def test_get_mem_available(self, host: "Host") -> None:
        cmd_out1 = "47251457"
        cmd_out2 = "4096"
        expected_out = 184576
        host.connection.execute_command.side_effect = [
            ConnectionCompletedProcess(return_code=0, args="", stdout=cmd_out1, stderr=""),
            ConnectionCompletedProcess(return_code=0, args="", stdout=cmd_out2, stderr=""),
        ]
        out = host.stats.get_free_memory()
        assert out == expected_out

    def test_get_wired_memory(self, host: "Host") -> None:
        cmd_out1 = "678814"
        cmd_out2 = "4096"
        expected_out = 2651
        host.connection.execute_command.side_effect = [
            ConnectionCompletedProcess(return_code=0, args="", stdout=cmd_out1, stderr=""),
            ConnectionCompletedProcess(return_code=0, args="", stdout=cmd_out2, stderr=""),
        ]
        out = host.stats.get_wired_memory()
        assert out == expected_out
