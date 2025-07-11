# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT

from mfd_connect import RPyCConnection
from mfd_host.linux import LinuxHost
from mfd_host.freebsd import FreeBSDHost


def linux_host_stats():
    connection = RPyCConnection(ip="20.20.20.20")
    host = LinuxHost(connection=connection)
    print(host.stats.get_meminfo())
    # {
    #         "MemTotal": "80819108",
    #         "MemFree": "61896272",
    #         "AnonHugePages": "0",
    #         "ShmemHugePages": "0",
    #         "HugePages_Free": "0",
    #         "HugePages_Rsvd": "0",
    #         "HugePages_Surp": "0",
    #         "Hugepagesize": "2048",
    #         "Hugetlb": "0",
    #         "DirectMap4k": "487276",
    #         "DirectMap2M": "81825792",
    #     }
    print(host.stats.get_cpu_utilization())
    # {
    #         "all": {
    #             "cpu_number": "all",
    #             "user": "3.25",
    #             "nice": "0.00",
    #             "system": "1.00",
    #             "iowait": "0.01",
    #             "steal": "0.00",
    #             "idle": "95.74",
    #         },
    #         "0": {
    #             "cpu_number": "0",
    #             "user": "3.07",
    #             "nice": "0.00",
    #             "system": "1.05",
    #             "iowait": "0.00",
    #             "steal": "0.00",
    #             "idle": "95.88",
    #         },
    #         "1": {
    #             "cpu_number": "1",
    #             "user": "3.34",
    #             "nice": "0.00",
    #             "system": "1.03",
    #             "iowait": "0.00",
    #             "steal": "0.00",
    #             "idle": "95.62",
    #         },
    #     }
    print(host.stats.get_slabinfo())
    # {
    #         "kmalloc-512": "5468",
    #         "kmalloc-256": "1616",
    #         "kmalloc-192": "2888",
    #         "kmalloc-128": "2619",
    #         "kmalloc-96": "5443",
    #         "kmalloc-64": "59418",
    #         "kmalloc-32": "57216",
    #         "kmalloc-16": "15616",
    #         "kmalloc-8": "16384",
    #     }
    print(host.stats.get_mem_used())
    # 18922536
    out_obj = host.stats.get_top_stats()
    print(out_obj.cpu_stat)
    # {
    #     0: {
    #         "user": 0.0,
    #         "sys": 0.0,
    #         "nice": 0.0,
    #         "idle": 100.0,
    #         "IO-wait": 0.0,
    #         "HW-int": 0.0,
    #         "SOFT-int": 0.0,
    #         "stolen": 0.0,
    #         "total": 0.0,
    #     },
    #     1: {
    #         "user": 0.0,
    #         "sys": 0.0,
    #         "nice": 0.0,
    #         "idle": 100.0,
    #         "IO-wait": 0.0,
    #         "HW-int": 0.0,
    #         "SOFT-int": 0.0,
    #         "stolen": 0.0,
    #         "total": 0.0,
    #     },
    #     999: {
    #         "user": 0.0,
    #         "sys": 6.2,
    #         "nice": 0.0,
    #         "idle": 393.8,
    #         "IO-wait": 0.0,
    #         "HW-int": 0.0,
    #         "SOFT-int": 0.0,
    #         "stolen": 0.0,
    #         "total": 6.2,
    #     },
    # }
    print(out_obj.memory_stat)
    # {
    #     "Mem": {"total": 78924.9, "free": 60415.4, "used": 3092.8, "buff/cache": 15416.8},
    #     "Scale": "MiB ",
    #     "Swap": {"total": 8192.0, "free": 8129.9, "used": 62.1, "avail": 74997.8},
    # }
    print(out_obj.process_stat)
    # {
    #     "PID": [
    #         163819,
    #         1,
    #         2,
    #         3,
    #         4,
    #     ],
    #     "USER": [
    #         "root",
    #         "root",
    #         "root",
    #         "root",
    #         "root",
    #     ],
    #     "PR": [20, 20, 20, 0, 0],
    #     "NI": [0, 0, 0, -20, -20],
    #     "VIRT": [
    #         1504896,
    #         169712,
    #         0,
    #         0,
    #         0,
    #     ],
    #     "RES": [15072, 10520, 0, 0, 0],
    #     "SHR": [7284, 6392, 0, 0, 0],
    #     "S": ["S", "S", "S", "I", "I"],
    #     "%CPU": [6.2, 0.0, 0.0, 0.0, 0.0],
    #     "%MEM": [0.0, 0.0, 0.0, 0.0, 0.0],
    #     "TIME+": [
    #         "1071:07",
    #         "3:17.91",
    #         "0:05.28",
    #         "0:00.00",
    #         "0:00.00",
    #     ],
    #     "COMMAND": [
    #         "contain+",
    #         "systemd",
    #         "kthreadd",
    #         "rcu_gp",
    #         "rcu_par+",
    #     ],
    # }

def freebsd_host_stats():
    connection = RPyCConnection(ip="20.20.20.20")
    host = FreeBSDHost(connection=connection)

    allowed_memory_leak = 1024  # 1 GB
    free_memory_at_startup = host.stats.get_free_memory()
    print(free_memory_at_startup)
    # 4096
    # allocate 512 MB of memory
    free_memory = host.stats.get_free_memory()
    print(free_memory)
    # 3584
    assert free_memory >= free_memory_at_startup - allowed_memory_leak

    wired_memory_at_startup = host.stats.get_wired_memory()
    print(wired_memory_at_startup)
    # 2102
    # load the driver (allocate 10-20MB of non-pageable memory)
    print(host.stats.get_wired_memory())
    # 2122
    # unload the driver
    wired_memory = host.stats.get_wired_memory()
    print(wired_memory)
    # 2105
    assert wired_memory <= wired_memory_at_startup + allowed_memory_leak

    host.stats.get_cpu_utilization()
    # do some CPU-intensive actions
    print(host.stats.get_cpu_utilization())
    # {
    #         "all": {
    #             "user": 4.29,
    #             "nice": 0.00,
    #             "system": 83.36,
    #             "interrupt": 0.04,
    #             "idle": 12.31,
    #         },
    #         "0": {
    #             "user": "4.29",
    #             "nice": "0.00",
    #             "system": "83.36",
    #             "interrupt": "0.04",
    #             "idle": "12.31",
    #         },
    #         "1": {
    #             "user": "0.00",
    #             "nice": "0.00",
    #             "system": "0.00",
    #             "interrupt": "0.00",
    #             "idle": "100.00",
    #         },
    #  }
