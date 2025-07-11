# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
from textwrap import dedent

import pytest
from mfd_connect import RPyCConnection
from mfd_connect.base import ConnectionCompletedProcess
from mfd_typing import OSName
from mfd_model.config import HostModel

from mfd_host import Host
from mfd_host.feature.stats.data_structures import StatsOutput
from mfd_host.exceptions import StatisticNotFoundException


class TestLinuxUtils:
    top_output = dedent(
        """\
        top - 19:43:02 up 111 days, 22:16,  0 users,  load average: 0.46, 0.31, 0.22
        Tasks: 186 total,   1 running, 185 sleeping,   0 stopped,   0 zombie
        %Cpu0  :  0.0 us,  0.0 sy,  0.0 ni,100.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
        %Cpu1  :  0.0 us,  0.0 sy,  0.0 ni,100.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
        %Cpu2  :  0.0 us,  0.0 sy,  0.0 ni,100.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
        %Cpu3  :  0.0 us,  6.2 sy,  0.0 ni, 93.8 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
        MiB Mem :  78924.9 total,  60415.4 free,   3092.8 used,  15416.8 buff/cache
        MiB Swap:   8192.0 total,   8129.9 free,     62.1 used.  74997.8 avail Mem
            PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
        163819 root      20   0 1504896  15072   7284 S   6.2   0.0   1071:07 contain+
            1 root      20   0  169712  10520   6392 S   0.0   0.0   3:17.91 systemd
            2 root      20   0       0      0      0 S   0.0   0.0   0:05.28 kthreadd
            3 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 rcu_gp
            4 root       0 -20       0      0      0 I   0.0   0.0   0:00.00 rcu_par+
        523849 root      20   0    8260   4584   4220 S   0.0   0.0   0:00.03 bluetoo+
        661787 root       0 -20       0      0      0 S   0.0   0.0   0:00.03 loop9
        661849 root      20   0 1468012  32876  20388 S   0.0   0.0   2:16.40 snapd
        879700 root       0 -20       0      0      0 S   0.0   0.0   0:00.00 loop1
        916605 rohit-d+  20   0   19160   9732   8092 S   0.0   0.0   0:00.09 systemd
        916611 rohit-d+  20   0  170852   4432      0 S   0.0   0.0   0:00.00 (sd-pam)
        916619 rohit-d+  20   0  277760  14380  12532 S   0.0   0.0   0:00.12 pulseau+
        916637 rohit-d+  20   0    7108   3860   3508 S   0.0   0.0   0:00.00 dbus-da+
        916782 rohit-d+  20   0    2608    532    464 S   0.0   0.0   0:00.00 sh
        916792 rohit-d+  20   0  993208 157808  43068 S   0.0   0.2   2:13.57 node
        916881 rohit-d+  20   0  905040  73296  39544 S   0.0   0.1   1:16.04 node
        940971 rohit-d+  20   0    9248   3508   3052 R   0.0   0.0   0:00.00 top
        """
    )

    cpu_stat = {
        0: {
            "user": 0.0,
            "sys": 0.0,
            "nice": 0.0,
            "idle": 100.0,
            "IO-wait": 0.0,
            "HW-int": 0.0,
            "SOFT-int": 0.0,
            "stolen": 0.0,
            "total": 0.0,
        },
        1: {
            "user": 0.0,
            "sys": 0.0,
            "nice": 0.0,
            "idle": 100.0,
            "IO-wait": 0.0,
            "HW-int": 0.0,
            "SOFT-int": 0.0,
            "stolen": 0.0,
            "total": 0.0,
        },
        2: {
            "user": 0.0,
            "sys": 0.0,
            "nice": 0.0,
            "idle": 100.0,
            "IO-wait": 0.0,
            "HW-int": 0.0,
            "SOFT-int": 0.0,
            "stolen": 0.0,
            "total": 0.0,
        },
        3: {
            "user": 0.0,
            "sys": 6.2,
            "nice": 0.0,
            "idle": 93.8,
            "IO-wait": 0.0,
            "HW-int": 0.0,
            "SOFT-int": 0.0,
            "stolen": 0.0,
            "total": 6.2,
        },
        999: {
            "user": 0.0,
            "sys": 6.2,
            "nice": 0.0,
            "idle": 393.8,
            "IO-wait": 0.0,
            "HW-int": 0.0,
            "SOFT-int": 0.0,
            "stolen": 0.0,
            "total": 6.2,
        },
    }
    memory_stat = {
        "Mem": {"total": 78924.9, "free": 60415.4, "used": 3092.8, "buff/cache": 15416.8},
        "Scale": "MiB ",
        "Swap": {"total": 8192.0, "free": 8129.9, "used": 62.1, "avail": 74997.8},
    }
    process_stat = {
        "PID": [
            163819,
            1,
            2,
            3,
            4,
            523849,
            661787,
            661849,
            879700,
            916605,
            916611,
            916619,
            916637,
            916782,
            916792,
            916881,
            940971,
        ],
        "USER": [
            "root",
            "root",
            "root",
            "root",
            "root",
            "root",
            "root",
            "root",
            "root",
            "rohit-d+",
            "rohit-d+",
            "rohit-d+",
            "rohit-d+",
            "rohit-d+",
            "rohit-d+",
            "rohit-d+",
            "rohit-d+",
        ],
        "PR": [20, 20, 20, 0, 0, 20, 0, 20, 0, 20, 20, 20, 20, 20, 20, 20, 20],
        "NI": [0, 0, 0, -20, -20, 0, -20, 0, -20, 0, 0, 0, 0, 0, 0, 0, 0],
        "VIRT": [
            1504896,
            169712,
            0,
            0,
            0,
            8260,
            0,
            1468012,
            0,
            19160,
            170852,
            277760,
            7108,
            2608,
            993208,
            905040,
            9248,
        ],
        "RES": [15072, 10520, 0, 0, 0, 4584, 0, 32876, 0, 9732, 4432, 14380, 3860, 532, 157808, 73296, 3508],
        "SHR": [7284, 6392, 0, 0, 0, 4220, 0, 20388, 0, 8092, 0, 12532, 3508, 464, 43068, 39544, 3052],
        "S": ["S", "S", "S", "I", "I", "S", "S", "S", "S", "S", "S", "S", "S", "S", "S", "S", "R"],
        "%CPU": [6.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "%MEM": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.1, 0.0],
        "TIME+": [
            "1071:07",
            "3:17.91",
            "0:05.28",
            "0:00.00",
            "0:00.00",
            "0:00.03",
            "0:00.03",
            "2:16.40",
            "0:00.00",
            "0:00.09",
            "0:00.00",
            "0:00.12",
            "0:00.00",
            "0:00.00",
            "2:13.57",
            "1:16.04",
            "0:00.00",
        ],
        "COMMAND": [
            "contain+",
            "systemd",
            "kthreadd",
            "rcu_gp",
            "rcu_par+",
            "bluetoo+",
            "loop9",
            "snapd",
            "loop1",
            "systemd",
            "(sd-pam)",
            "pulseau+",
            "dbus-da+",
            "sh",
            "node",
            "node",
            "top",
        ],
    }

    @pytest.fixture
    def host(self, mocker):
        _connection = mocker.create_autospec(RPyCConnection)
        _connection.get_os_name.return_value = OSName.LINUX

        model = HostModel(role="sut")

        yield Host(connection=_connection, topology=model)
        mocker.stopall()

    def test_get_meminfo(self, host):
        cmd_out = dedent(
            """\
            MemTotal:       80819108 kB
            MemFree:        61896272 kB
            MemAvailable:   77005920 kB
            Buffers:         1177256 kB
            Cached:         12937004 kB
            SwapCached:        17396 kB
            Active:          8508868 kB
            Inactive:        8279792 kB
            Active(anon):    2663960 kB
            Inactive(anon):    19620 kB
            Active(file):    5844908 kB
            Inactive(file):  8260172 kB
            Unevictable:       18536 kB
            Mlocked:           18536 kB
            SwapTotal:       8388604 kB
            SwapFree:        8324992 kB
            Dirty:               480 kB
            Writeback:             0 kB
            AnonPages:       2690632 kB
            Mapped:           160112 kB
            Shmem:               976 kB
            KReclaimable:    1849684 kB
            Slab:            1988052 kB
            SReclaimable:    1849684 kB
            SUnreclaim:       138368 kB
            KernelStack:        6000 kB
            PageTables:        34992 kB
            NFS_Unstable:          0 kB
            Bounce:                0 kB
            WritebackTmp:          0 kB
            CommitLimit:    48798156 kB
            Committed_AS:    2598744 kB
            VmallocTotal:   34359738367 kB
            VmallocUsed:       27944 kB
            VmallocChunk:          0 kB
            Percpu:             5184 kB
            HardwareCorrupted:     0 kB
            AnonHugePages:         0 kB
            ShmemHugePages:        0 kB
            ShmemPmdMapped:        0 kB
            FileHugePages:         0 kB
            FilePmdMapped:         0 kB
            CmaTotal:              0 kB
            CmaFree:               0 kB
            HugePages_Total:       0
            HugePages_Free:        0
            HugePages_Rsvd:        0
            HugePages_Surp:        0
            Hugepagesize:       2048 kB
            Hugetlb:               0 kB
            DirectMap4k:      487276 kB
            DirectMap2M:    81825792 kB
        """
        )
        expected_out = {
            "MemTotal": "80819108",
            "MemFree": "61896272",
            "MemAvailable": "77005920",
            "Buffers": "1177256",
            "Cached": "12937004",
            "SwapCached": "17396",
            "Active": "8508868",
            "Inactive": "8279792",
            "Active(anon)": "2663960",
            "Inactive(anon)": "19620",
            "Active(file)": "5844908",
            "Inactive(file)": "8260172",
            "Unevictable": "18536",
            "Mlocked": "18536",
            "SwapTotal": "8388604",
            "SwapFree": "8324992",
            "Dirty": "480",
            "Writeback": "0",
            "AnonPages": "2690632",
            "Mapped": "160112",
            "Shmem": "976",
            "KReclaimable": "1849684",
            "Slab": "1988052",
            "SReclaimable": "1849684",
            "SUnreclaim": "138368",
            "KernelStack": "6000",
            "PageTables": "34992",
            "NFS_Unstable": "0",
            "Bounce": "0",
            "WritebackTmp": "0",
            "CommitLimit": "48798156",
            "Committed_AS": "2598744",
            "VmallocTotal": "34359738367",
            "VmallocUsed": "27944",
            "VmallocChunk": "0",
            "Percpu": "5184",
            "HardwareCorrupted": "0",
            "AnonHugePages": "0",
            "ShmemHugePages": "0",
            "ShmemPmdMapped": "0",
            "FileHugePages": "0",
            "FilePmdMapped": "0",
            "CmaTotal": "0",
            "CmaFree": "0",
            "HugePages_Total": "0",
            "HugePages_Free": "0",
            "HugePages_Rsvd": "0",
            "HugePages_Surp": "0",
            "Hugepagesize": "2048",
            "Hugetlb": "0",
            "DirectMap4k": "487276",
            "DirectMap2M": "81825792",
        }
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=cmd_out, stderr=""
        )
        out = host.stats.get_meminfo()
        assert out == expected_out
        host.connection.execute_command.assert_called_once_with("cat /proc/meminfo", shell=True)

    def test_get_cpu_utilization(self, host):
        cmd_out = dedent(
            """\
            Linux 5.4.0-153-generic (rohit-dev)     11/06/2023      _x86_64_        (4 CPU)

            06:46:38 AM     CPU     %user     %nice   %system   %iowait    %steal     %idle
            07:55:01 AM     all      3.81      0.00      1.10      0.01      0.00     95.08
            07:55:01 AM       0      3.58      0.00      1.07      0.00      0.00     95.35
            07:55:01 AM       1      4.12      0.00      1.15      0.00      0.00     94.73
            07:55:01 AM       2      4.12      0.00      1.24      0.00      0.00     94.63
            07:55:01 AM       3      3.43      0.00      0.95      0.02      0.00     95.59
            Average:        all      3.25      0.00      1.00      0.01      0.00     95.74
            Average:          0      3.07      0.00      1.05      0.00      0.00     95.88
            Average:          1      3.34      0.00      1.03      0.00      0.00     95.62
            Average:          2      3.53      0.00      1.08      0.00      0.00     95.39
            Average:          3      3.05      0.00      0.85      0.02      0.00     96.07"""
        )
        expected_out = {
            "all": {
                "cpu_number": "all",
                "user": "3.25",
                "nice": "0.00",
                "system": "1.00",
                "iowait": "0.01",
                "steal": "0.00",
                "idle": "95.74",
            },
            "0": {
                "cpu_number": "0",
                "user": "3.07",
                "nice": "0.00",
                "system": "1.05",
                "iowait": "0.00",
                "steal": "0.00",
                "idle": "95.88",
            },
            "1": {
                "cpu_number": "1",
                "user": "3.34",
                "nice": "0.00",
                "system": "1.03",
                "iowait": "0.00",
                "steal": "0.00",
                "idle": "95.62",
            },
            "2": {
                "cpu_number": "2",
                "user": "3.53",
                "nice": "0.00",
                "system": "1.08",
                "iowait": "0.00",
                "steal": "0.00",
                "idle": "95.39",
            },
            "3": {
                "cpu_number": "3",
                "user": "3.05",
                "nice": "0.00",
                "system": "0.85",
                "iowait": "0.02",
                "steal": "0.00",
                "idle": "96.07",
            },
        }
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=cmd_out, stderr=""
        )
        out = host.stats.get_cpu_utilization()
        assert out == expected_out
        host.connection.execute_command.assert_called_once_with("sar -P ALL", shell=True)

    def test_get_slabinfo(self, host):
        cmd_out = dedent(
            """\
            slabinfo - version: 2.1
            # name            <active_objs> <num_objs> <objsize> <objperslab> <pagesperslab> : tunables <limit> <batchcount> <sharedfactor> : slabdata <active_slabs> <num_slabs> <sharedavail>
            ufs_inode_cache        0      0    808   20    4 : tunables    0    0    0 : slabdata      0      0      0
            mm_struct           2370   2370   1088   30    8 : tunables    0    0    0 : slabdata     79     79      0
            files_cache         1748   1748    704   23    4 : tunables    0    0    0 : slabdata     76     76      0
            signal_cache        2464   2464   1152   28    8 : tunables    0    0    0 : slabdata     88     88      0
            sighand_cache       1530   1530   2112   15    8 : tunables    0    0    0 : slabdata    102    102      0
            task_struct         1074   1170   5696    5    8 : tunables    0    0    0 : slabdata    234    234      0
            cred_jar            6092   6132    192   21    1 : tunables    0    0    0 : slabdata    292    292      0
            anon_vma_chain     55610  59520     64   64    1 : tunables    0    0    0 : slabdata    930    930      0
            anon_vma           28521  31083    104   39    1 : tunables    0    0    0 : slabdata    797    797      0
            vmap_area         269734 270080     64   64    1 : tunables    0    0    0 : slabdata   4220   4220      0
            dma-kmalloc-8k         0      0   8192    4    8 : tunables    0    0    0 : slabdata      0      0      0
            dma-kmalloc-4k         0      0   4096    8    8 : tunables    0    0    0 : slabdata      0      0      0
            dma-kmalloc-2k         0      0   2048   16    8 : tunables    0    0    0 : slabdata      0      0      0
            dma-kmalloc-1k         0      0   1024   16    4 : tunables    0    0    0 : slabdata      0      0      0
            dma-kmalloc-512        0      0    512   16    2 : tunables    0    0    0 : slabdata      0      0      0
            dma-kmalloc-256        0      0    256   16    1 : tunables    0    0    0 : slabdata      0      0      0
            dma-kmalloc-128        0      0    128   32    1 : tunables    0    0    0 : slabdata      0      0      0
            dma-kmalloc-64         0      0     64   64    1 : tunables    0    0    0 : slabdata      0      0      0
            dma-kmalloc-32         0      0     32  128    1 : tunables    0    0    0 : slabdata      0      0      0
            dma-kmalloc-16         0      0     16  256    1 : tunables    0    0    0 : slabdata      0      0      0
            dma-kmalloc-8          0      0      8  512    1 : tunables    0    0    0 : slabdata      0      0      0
            dma-kmalloc-192        0      0    192   21    1 : tunables    0    0    0 : slabdata      0      0      0
            dma-kmalloc-96         0      0     96   42    1 : tunables    0    0    0 : slabdata      0      0      0
            kmalloc-rcl-8k         0      0   8192    4    8 : tunables    0    0    0 : slabdata      0      0      0
            kmalloc-rcl-4k         0      0   4096    8    8 : tunables    0    0    0 : slabdata      0      0      0
            kmalloc-rcl-2k        48     48   2048   16    8 : tunables    0    0    0 : slabdata      3      3      0
            kmalloc-rcl-1k       128    128   1024   16    4 : tunables    0    0    0 : slabdata      8      8      0
            kmalloc-rcl-512      125    384    512   16    2 : tunables    0    0    0 : slabdata     24     24      0
            kmalloc-rcl-256      289    864    256   16    1 : tunables    0    0    0 : slabdata     54     54      0
            kmalloc-rcl-192      733   2415    192   21    1 : tunables    0    0    0 : slabdata    115    115      0
            kmalloc-rcl-128     1509   4128    128   32    1 : tunables    0    0    0 : slabdata    129    129      0
            kmalloc-rcl-96     26368  31794     96   42    1 : tunables    0    0    0 : slabdata    757    757      0
            kmalloc-rcl-64    144459 156224     64   64    1 : tunables    0    0    0 : slabdata   2441   2441      0
            kmalloc-rcl-32         0      0     32  128    1 : tunables    0    0    0 : slabdata      0      0      0
            kmalloc-rcl-16         0      0     16  256    1 : tunables    0    0    0 : slabdata      0      0      0
            kmalloc-rcl-8          0      0      8  512    1 : tunables    0    0    0 : slabdata      0      0      0
            kmalloc-8k           160    160   8192    4    8 : tunables    0    0    0 : slabdata     40     40      0
            kmalloc-4k          3008   3008   4096    8    8 : tunables    0    0    0 : slabdata    376    376      0
            kmalloc-2k          1995   2032   2048   16    8 : tunables    0    0    0 : slabdata    127    127      0
            kmalloc-1k          4012   4176   1024   16    4 : tunables    0    0    0 : slabdata    261    261      0
            kmalloc-512         5468   5520    512   16    2 : tunables    0    0    0 : slabdata    345    345      0
            kmalloc-256         1616   1616    256   16    1 : tunables    0    0    0 : slabdata    101    101      0
            kmalloc-192         2888   3087    192   21    1 : tunables    0    0    0 : slabdata    147    147      0
            kmalloc-128         2619   3008    128   32    1 : tunables    0    0    0 : slabdata     94     94      0
            kmalloc-96          5443   6006     96   42    1 : tunables    0    0    0 : slabdata    143    143      0
            kmalloc-64         59418  59904     64   64    1 : tunables    0    0    0 : slabdata    936    936      0
            kmalloc-32         57216  57216     32  128    1 : tunables    0    0    0 : slabdata    447    447      0
            kmalloc-16         15616  15616     16  256    1 : tunables    0    0    0 : slabdata     61     61      0
            kmalloc-8          16384  16384      8  512    1 : tunables    0    0    0 : slabdata     32     32      0
            kmem_cache_node     3648   3648     64   64    1 : tunables    0    0    0 : slabdata     57     57      0
            kmem_cache          3068   3096    448   18    2 : tunables    0    0    0 : slabdata    172    172      0
        """  # noqa
        )
        expected_out = {
            "dma-kmalloc-8k": "0",
            "dma-kmalloc-4k": "0",
            "dma-kmalloc-2k": "0",
            "dma-kmalloc-1k": "0",
            "dma-kmalloc-512": "0",
            "dma-kmalloc-256": "0",
            "dma-kmalloc-128": "0",
            "dma-kmalloc-64": "0",
            "dma-kmalloc-32": "0",
            "dma-kmalloc-16": "0",
            "dma-kmalloc-8": "0",
            "dma-kmalloc-192": "0",
            "dma-kmalloc-96": "0",
            "kmalloc-rcl-8k": "0",
            "kmalloc-rcl-4k": "0",
            "kmalloc-rcl-2k": "48",
            "kmalloc-rcl-1k": "128",
            "kmalloc-rcl-512": "125",
            "kmalloc-rcl-256": "289",
            "kmalloc-rcl-192": "733",
            "kmalloc-rcl-128": "1509",
            "kmalloc-rcl-96": "26368",
            "kmalloc-rcl-64": "144459",
            "kmalloc-rcl-32": "0",
            "kmalloc-rcl-16": "0",
            "kmalloc-rcl-8": "0",
            "kmalloc-8k": "160",
            "kmalloc-4k": "3008",
            "kmalloc-2k": "1995",
            "kmalloc-1k": "4012",
            "kmalloc-512": "5468",
            "kmalloc-256": "1616",
            "kmalloc-192": "2888",
            "kmalloc-128": "2619",
            "kmalloc-96": "5443",
            "kmalloc-64": "59418",
            "kmalloc-32": "57216",
            "kmalloc-16": "15616",
            "kmalloc-8": "16384",
        }
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=cmd_out, stderr=""
        )
        out = host.stats.get_slabinfo()
        assert out == expected_out
        host.connection.execute_command.assert_called_once_with("cat /proc/slabinfo", shell=True)

    def test_get_mem_used(self, host):
        cmd_out = dedent(
            """\
            MemTotal:       80819108 kB
            MemFree:        61896572 kB
            MemAvailable:   77006220 kB
            Buffers:         1177256 kB
            Cached:         12937004 kB
            """
        )
        expected_out = 18922536
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=cmd_out, stderr=""
        )
        out = host.stats.get_mem_used()
        assert out == expected_out
        host.connection.execute_command.assert_called_once_with("cat /proc/meminfo", shell=True)

    def test_get_mem_used_error(self, host):
        cmd_out = dedent(
            """\
            MemTotal:       80819108 kB
            """
        )
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=cmd_out, stderr=""
        )
        with pytest.raises(StatisticNotFoundException, match=f"Unable to find memory usage: {cmd_out}"):
            host.stats.get_mem_used()

    def test__get_top_values(self, host):
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=self.top_output, stderr=""
        )
        out_obj = host.stats._get_top_values(memory_scaling="g")
        assert isinstance(out_obj, StatsOutput)
        host.connection.execute_command.assert_called_once_with("top -b -n1 -1 -E g", shell=True)

    def test__get_top_values_error(self, host):
        error = "error while fetching stats"
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=1, args="", stdout="", stderr=error
        )
        with pytest.raises(StatisticNotFoundException, match=f"gathering stats failed with error: {error}"):
            host.stats._get_top_values()

    def test_linux_top_stats(self, host):
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=self.top_output, stderr=""
        )
        out_obj = host.stats.get_top_stats()
        assert out_obj.cpu_stat == self.cpu_stat
        assert out_obj.memory_stat == self.memory_stat
        assert out_obj.process_stat == self.process_stat

    def test__handle_separate_cpu_warning(self, host):
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=self.top_output, stderr=""
        )
        host.stats._handle_separate_cpu_warning(memory_scaling="k", options="")
        host.connection.execute_command.assert_called_once_with("top -b -n1 -E k", shell=True)

    def test__execute_top_command(self, host):
        host.connection.execute_command.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=self.top_output, stderr=""
        )
        output_obj = host.stats._execute_top_command(separate_cpu=True, memory_scaling="k", options="")
        host.connection.execute_command.assert_called_once_with("top -b -n1 -1 -E k", shell=True)
        assert isinstance(output_obj, ConnectionCompletedProcess)
        assert output_obj.stdout == self.top_output

    def test__build_cpu_raw_output(self, host):
        cpu_stats = {
            0: {
                "user": 0.0,
                "sys": 0.0,
                "nice": 0.0,
                "idle": 100.0,
                "IO-wait": 0.0,
                "HW-int": 0.0,
                "SOFT-int": 0.0,
                "stolen": 0.0,
                "total": 0.0,
            },
            1: {
                "user": 0.0,
                "sys": 0.0,
                "nice": 0.0,
                "idle": 100.0,
                "IO-wait": 0.0,
                "HW-int": 0.0,
                "SOFT-int": 0.0,
                "stolen": 0.0,
                "total": 0.0,
            },
        }
        expected_out = dedent(
            """\
            %CPU0  :   0.0 user,    0.0 sys,    0.0 nice,  100.0 idle,    0.0 IO-wait,    0.0 HW-int,    0.0 SOFT-int,    0.0 stolen,    0.0 total
            %CPU1  :   0.0 user,    0.0 sys,    0.0 nice,  100.0 idle,    0.0 IO-wait,    0.0 HW-int,    0.0 SOFT-int,    0.0 stolen,    0.0 total"""  # noqa
        )
        assert host.stats._build_cpu_raw_output(cpu_stats=cpu_stats) == expected_out

    def test__build_memory_raw_output(self, host):
        mem_stats = {
            "Mem": {"total": 78924.9, "free": 60415.4, "used": 3092.8, "buff/cache": 15416.8},
            "Scale": "MiB ",
            "Swap": {"total": 8192.0, "free": 8129.9, "used": 62.1, "avail": 74997.8},
        }
        expected_out = dedent(
            """\
        MiB Mem :
         78924.9 total,  60415.4 free,   3092.8 used,  15416.8 buff/cache
        MiB Swap:
          8192.0 total,   8129.9 free,     62.1 used,  74997.8 avail"""
        )
        assert host.stats._build_memory_raw_output(mem_stats=mem_stats) == expected_out

    def test__build_process_raw_output(self, host):
        out = """     PID USER         PR    NI      VIRT      RES     SHR S    %CPU  %MEM TIME+     COMMAND    
  163819 root         20     0   1504896    15072    7284 S     6.2   0.0 1071:07   contain+  
       1 root         20     0    169712    10520    6392 S     0.0   0.0 3:17.91   systemd   
       2 root         20     0         0        0       0 S     0.0   0.0 0:05.28   kthreadd  
       3 root          0   -20         0        0       0 I     0.0   0.0 0:00.00   rcu_gp    
       4 root          0   -20         0        0       0 I     0.0   0.0 0:00.00   rcu_par+  
  523849 root         20     0      8260     4584    4220 S     0.0   0.0 0:00.03   bluetoo+  
  661787 root          0   -20         0        0       0 S     0.0   0.0 0:00.03   loop9     
  661849 root         20     0   1468012    32876   20388 S     0.0   0.0 2:16.40   snapd     
  879700 root          0   -20         0        0       0 S     0.0   0.0 0:00.00   loop1     
  916605 rohit-d+     20     0     19160     9732    8092 S     0.0   0.0 0:00.09   systemd   
  916611 rohit-d+     20     0    170852     4432       0 S     0.0   0.0 0:00.00   (sd-pam)  
  916619 rohit-d+     20     0    277760    14380   12532 S     0.0   0.0 0:00.12   pulseau+  
  916637 rohit-d+     20     0      7108     3860    3508 S     0.0   0.0 0:00.00   dbus-da+  
  916782 rohit-d+     20     0      2608      532     464 S     0.0   0.0 0:00.00   sh        
  916792 rohit-d+     20     0    993208   157808   43068 S     0.0   0.2 2:13.57   node      
  916881 rohit-d+     20     0    905040    73296   39544 S     0.0   0.1 1:16.04   node      
  940971 rohit-d+     20     0      9248     3508    3052 R     0.0   0.0 0:00.00   top       """  # noqa
        assert host.stats._build_process_raw_output(proc_stats=self.process_stat) == out

    def test__get_cpu_from_top_output(self, host):
        assert host.stats._get_cpu_from_top_output(output=self.top_output, friendly_labels=True) == self.cpu_stat

    def test__get_mem_from_top_output(self, host):
        assert host.stats._get_mem_from_top_output(output=self.top_output) == self.memory_stat

    def test__get_proc_from_top_output(self, host):
        assert host.stats._get_proc_from_top_output(output=self.top_output, filter_proc=[]) == self.process_stat

    def test__update_porc_stats(self, host):
        proc_labels = ["PID", "USER", "PR", "NI", "VIRT", "RES", "SHR", "S", "%CPU", "%MEM", "TIME+", "COMMAND"]
        values = ["1", "root", "20", "0", "169712", "10520", "6392", "S", "0.0", "0.0", "3:17.91", "systemd"]
        proc_stats = {
            "PID": [163819],
            "USER": ["root"],
            "PR": [20],
            "NI": [0],
            "VIRT": [1504896],
            "RES": [15072],
            "SHR": [7284],
            "S": ["S"],
            "%CPU": [6.2],
            "%MEM": [0.0],
            "TIME+": ["1071:07"],
            "COMMAND": ["contain+"],
        }
        output = {
            "PID": [163819, 1],
            "USER": ["root", "root"],
            "PR": [20, 20],
            "NI": [0, 0],
            "VIRT": [1504896, 169712],
            "RES": [15072, 10520],
            "SHR": [7284, 6392],
            "S": ["S", "S"],
            "%CPU": [6.2, 0.0],
            "%MEM": [0.0, 0.0],
            "TIME+": ["1071:07", "3:17.91"],
            "COMMAND": ["contain+", "systemd"],
        }
        assert host.stats._update_proc_stats(proc_labels, values, proc_stats) == output
