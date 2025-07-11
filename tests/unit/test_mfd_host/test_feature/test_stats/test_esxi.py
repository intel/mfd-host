# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
from textwrap import dedent

import pytest
from mfd_connect import RPyCConnection
from mfd_connect.base import ConnectionCompletedProcess
from mfd_typing import OSName

from mfd_host import Host
from mfd_host.exceptions import StatisticNotFoundException


class TestESXiStats:
    """Module to Test ESXi Stats."""

    @pytest.fixture
    def host(self, mocker):
        _connection = mocker.create_autospec(RPyCConnection)
        _connection.get_os_name.return_value = OSName.ESXI
        yield Host(connection=_connection)
        mocker.stopall()

    def test_get_meminfo(self, host):
        vsish_out = dedent(
            """\
                Memory information {
                    System memory usage (pages):228763
                    Number of NUMA nodes:2
                    Number of memory nodes:3
                    Number of memory tiers:1
                    First valid MPN:1
                    Last valid MPN:25690111
                    Max valid MPN:274877906944
                    Max support RAM (in MB):33585088
                    System heap free (pages):58855
                }
                """
        )
        out_dict = {"mem_usage": "228763", "heap_free": "58855"}
        host.stats._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=vsish_out, return_code=0
        )
        assert host.stats.get_meminfo() == out_dict

    def test_get_meminfo_with_no_heap_value(self, host):
        vsish_out = dedent(
            """\
                Memory information {
                    System memory usage (pages):228763
                    Number of NUMA nodes:2
                    Number of memory nodes:3
                    Number of memory tiers:1
                    First valid MPN:1
                    Last valid MPN:25690111
                    Max valid MPN:274877906944
                    Max support RAM (in MB):33585088
                }
                """
        )
        out_dict = {"mem_usage": "228763", "heap_free": None}
        host.stats._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=vsish_out, return_code=0
        )
        assert host.stats.get_meminfo() == out_dict

    def test_get_meminfo_error_with_no_mem_value(self, host):
        vsish_out = dedent(
            """\
                Memory information {
                    Number of NUMA nodes:2
                    Number of memory nodes:3
                    Number of memory tiers:1
                    First valid MPN:1
                    Last valid MPN:25690111
                    Max valid MPN:274877906944
                    Max support RAM (in MB):33585088
                    System heap free (pages):58855
                }
                """
        )
        host.stats._connection.execute_command.return_value = ConnectionCompletedProcess(
            args="", stdout=vsish_out, return_code=0
        )
        with pytest.raises(StatisticNotFoundException):
            host.stats.get_meminfo()
