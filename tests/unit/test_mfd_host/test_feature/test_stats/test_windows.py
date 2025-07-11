# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
from textwrap import dedent
from unittest.mock import call

import pytest
from mfd_connect import RPyCConnection
from mfd_connect.base import ConnectionCompletedProcess
from mfd_typing import OSName
from mfd_model.config import HostModel

from mfd_host import Host
from mfd_host.feature.stats.windows import WindowsStats
from mfd_host.exceptions import StatisticNotFoundException


class TestLinuxUtils:
    performance_collection_out = {
        "\\b17-27878\\processor(0)\\dpc rate": {"11/28/2023 3:37:38 PM": "0", "11/28/2023 3:37:39 PM": "0"},
        "\\b17-27878\\processor(1)\\dpc rate": {"11/28/2023 3:37:38 PM": "0", "11/28/2023 3:37:39 PM": "0"},
        "\\b17-27878\\processor(2)\\dpc rate": {"11/28/2023 3:37:38 PM": "0", "11/28/2023 3:37:39 PM": "0"},
        "\\b17-27878\\processor(3)\\dpc rate": {"11/28/2023 3:37:38 PM": "0", "11/28/2023 3:37:39 PM": "0"},
        "\\b17-27878\\processor(4)\\dpc rate": {"11/28/2023 3:37:38 PM": "0", "11/28/2023 3:37:39 PM": "0"},
        "\\b17-27878\\processor(5)\\dpc rate": {"11/28/2023 3:37:38 PM": "0", "11/28/2023 3:37:39 PM": "0"},
        "\\b17-27878\\processor(6)\\dpc rate": {"11/28/2023 3:37:38 PM": "0", "11/28/2023 3:37:39 PM": "0"},
        "\\b17-27878\\processor(7)\\dpc rate": {"11/28/2023 3:37:38 PM": "0", "11/28/2023 3:37:39 PM": "0"},
        "\\b17-27878\\processor(8)\\dpc rate": {"11/28/2023 3:37:38 PM": "0", "11/28/2023 3:37:39 PM": "0"},
        "\\b17-27878\\processor(9)\\dpc rate": {"11/28/2023 3:37:38 PM": "1", "11/28/2023 3:37:39 PM": "0"},
        "\\b17-27878\\processor(_total)\\dpc rate": {"11/28/2023 3:37:38 PM": "1", "11/28/2023 3:37:39 PM": "1"},
    }

    @pytest.fixture
    def host(self, mocker):
        _connection = mocker.create_autospec(RPyCConnection)
        _connection.get_os_name.return_value = OSName.WINDOWS

        model = HostModel(role="sut")

        yield Host(connection=_connection, topology=model)
        mocker.stopall()

    def test_get_meminfo(self, host):
        output = dedent(
            """\
            Timestamp : 11/22/2023 12:17:07 PM
            Readings  : \\b17-27878\\memory\\pool nonpaged bytes :
                        421310464
            """
        )
        host.stats._connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=output, stderr=""
        )
        host.stats.get_meminfo()
        host.stats._connection.execute_powershell.assert_has_calls(
            [
                call('Get-counter -Counter "\\Memory\\Available Bytes" | Format-List', expected_return_codes={0}),
                call('Get-counter -Counter "\\Memory\\Pool Paged Bytes" | Format-List', expected_return_codes={0}),
                call('Get-counter -Counter "\\Memory\\Pool Nonpaged Bytes" | Format-List', expected_return_codes={0}),
            ]
        )

    def test_get_cpu_utilization(self, host):
        output = dedent(
            """\
            Timestamp : 11/22/2023 12:37:00 PM
            Readings  : \\b17-27878\\processor(_total)\\% processor time :
                        0.115766427735953
            """
        )
        host.stats._connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=output, stderr=""
        )
        assert host.stats.get_cpu_utilization() == 0.115766427735953
        host.stats._connection.execute_powershell.assert_has_calls(
            [
                call(
                    'Get-counter -Counter "\\Processor(_Total)\\% Processor Time" | Format-List',
                    expected_return_codes={0},
                ),
            ]
        )

    def test_get_performance_counter_error(self, host):
        output = dedent(
            """\
            Timestamp : 11/22/2023 12:37:00 PM
            Readings  : \\b17-27878\\processor(_total)\\% processor time :
                        Error_stat
            """
        )
        host.stats._connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=output, stderr=""
        )
        with pytest.raises(StatisticNotFoundException):
            host.stats.get_cpu_utilization()

    def test_get_performance_counter_error_out(self, host):
        output = dedent(
            """\
            Timestamp : 11/22/2023 12:37:00 PM
            error  : \\b17-27878\\processor(_total)\\% processor time :
                        0.115766427735953
            """
        )
        host.stats._connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=output, stderr=""
        )
        with pytest.raises(StatisticNotFoundException):
            host.stats.get_cpu_utilization()

    def test_get_performance_collection(self, host):
        output = dedent(
            """\
            Timestamp : 11/22/2023 1:30:07 PM
            Readings  : \\b17-27878\\processor(0)\\interrupts/sec :
                        93.7112213141639

                        \\b17-27878\\processor(1)\\interrupts/sec :
                        81.6194508220137

                        \\b17-27878\\processor(2)\\interrupts/sec :
                        88.6729836091013

                        \\b17-27878\\processor(3)\\interrupts/sec :
                        81.6194508220137

                        \\b17-27878\\processor(_total)\\interrupts/sec :
                        3252.6862623884

                        \\b17-27878\\processor(0)\\% processor time :
                        0.287481163058789

                        \\b17-27878\\processor(1)\\% processor time :
                        0.287481163058789

                        \\b17-27878\\processor(2)\\% processor time :
                        0.287481163058789

                        \\b17-27878\\processor(3)\\% processor time :
                        0.287481163058789

                        \\b17-27878\\processor(_total)\\% processor time :
                        0.374031629409255

            Timestamp : 11/22/2023 1:30:08 PM
            Readings  : \\b17-27878\\processor(0)\\interrupts/sec :
                        85.8730115694103

                        \\b17-27878\\processor(1)\\interrupts/sec :
                        74.2946279870179

                        \\b17-27878\\processor(2)\\interrupts/sec :
                        89.7324727635411

                        \\b17-27878\\processor(3)\\interrupts/sec :
                        81.0486850767468

                        \\b17-27878\\processor(_total)\\interrupts/sec :
                        3768.76385606873

                        \\b17-27878\\processor(0)\\% processor time :
                        0.499562149830823

                        \\b17-27878\\processor(1)\\% processor time :
                        0.499562149830823

                        \\b17-27878\\processor(2)\\% processor time :
                        0.499562149830823

                        \\b17-27878\\processor(3)\\% processor time :
                        0.499562149830823

                        \\b17-27878\\processor(_total)\\% processor time :
                        1.08584526309411

            """
        )
        host.stats._connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=output, stderr=""
        )
        host.stats.get_performance_collection(
            r"\Processor(*)\Interrupts/sec",
            r"\Processor(*)\% Processor Time",
            interval=1,
            samples=2,
        )
        host.stats._connection.execute_powershell.assert_has_calls(
            [
                call(
                    r"""Get-counter -Counter '\Processor(*)\Interrupts/sec', '\Processor(*)\% Processor Time' -MaxSamples 2 -SampleInterval 1  | Format-List""",  # noqa
                    expected_return_codes={0},
                ),
            ]
        )

    def test_get_dpc_rate(self, host, mocker):
        expected_out = {
            "0_dpc rate": 0.0,
            "1_dpc rate": 0.0,
            "2_dpc rate": 0.0,
            "3_dpc rate": 0.0,
            "4_dpc rate": 0.0,
            "5_dpc rate": 0.0,
            "6_dpc rate": 0.0,
            "7_dpc rate": 0.0,
            "8_dpc rate": 0.0,
            "9_dpc rate": 0.5,
            "_total_dpc rate": 1.0,
        }
        mocker.patch(
            "mfd_host.feature.stats.windows.WindowsStats.get_performance_collection",
            mocker.create_autospec(
                WindowsStats.get_performance_collection, return_value=self.performance_collection_out
            ),
        )
        assert host.stats.get_dpc_rate(interval=1, samples=2) == expected_out

    def test_parse_performance_collection(self, host, mocker):
        expected_out = {
            "0_dpc rate": 0.0,
            "1_dpc rate": 0.0,
            "2_dpc rate": 0.0,
            "3_dpc rate": 0.0,
            "4_dpc rate": 0.0,
            "5_dpc rate": 0.0,
            "6_dpc rate": 0.0,
            "7_dpc rate": 0.0,
            "8_dpc rate": 0.0,
            "9_dpc rate": 0.5,
            "_total_dpc rate": 1.0,
        }
        assert host.stats.parse_performance_collection(raw_perf_data=self.performance_collection_out) == expected_out

    def test__mean_data(self, host, mocker):
        time_data_dict = {"11/28/2023 3:37:38 PM": "1", "11/28/2023 3:37:39 PM": "0"}
        assert host.stats._mean_data(time_data_dict=time_data_dict) == 0.5
