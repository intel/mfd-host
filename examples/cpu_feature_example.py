# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Example of CPU Feature usage."""

from mfd_connect import RPyCConnection, SSHConnection
from mfd_host import Host
from mfd_network_adapter.data_structures import State


def cpu_windows():
    """Usage example of Windows CPU Feature."""
    connection = RPyCConnection(ip="20.20.20.20")
    host = Host(connection=connection)
    host.cpu.get_core_info()
    host.cpu.get_hyperthreading_state()
    host.cpu.get_phy_cpu_no()
    host.cpu.get_numa_node_count()
    host.cpu.get_log_cpu_no()
    host.cpu.set_groupsize(maxsize=32)


def cpu_esxi():
    """Usage example of ESXi CPU Feature."""
    connection = SSHConnection(ip="20.20.20.20", username="root", password="")
    host = Host(connection=connection)
    host.cpu.packages()
    host.cpu.threads()
    host.cpu.cores()
    host.cpu.set_numa_affinity(State.ENABLED)
    host.cpu.set_numa_affinity(State.DISABLED)


def cpu_freebsd():
    """Usage example of FreeBSD CPU Feature."""
    connection = SSHConnection(ip="20.20.20.20", username="root", password="")
    host = Host(connection=connection)
    host.cpu.get_log_cpu_no()


def cpu_linux():
    """Usage example of Linux CPU Feature."""
    connection = SSHConnection(ip="20.20.20.20", username="root", password="")
    host = Host(connection=connection)
    host.cpu.display_cpu_stats_only()
    host.cpu.get_cpu_stats()
    host.cpu.get_log_cpu_no()
    host.cpu.affinitize_queues_to_cpus("ens5f1", "/root/ice-1.7.0_rc75/scripts")
