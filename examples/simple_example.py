# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT

# Put here only the dependencies required to run the module.
# Development and test requirements should go to the corresponding files.
"""Simple example of usage."""

import logging

from mfd_connect import RPyCConnection

from mfd_host.linux import LinuxHost
from mfd_host.windows import WindowsHost
from mfd_host.freebsd import FreeBSDHost

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def linux_vlan_example():
    connection = RPyCConnection(ip="10.10.10.10")
    host = LinuxHost(connection=connection)
    priority_map = "0:0 1:1 2:2 3:3 4:4 5:5 6:6 7:7"
    host.network.vlan.set_ingress_egress_map(interface_name="eth1", priority_map=priority_map, direction="both")


def windows_vlan_example():
    connection = RPyCConnection(ip="20.20.20.20")
    host = WindowsHost(connection=connection)
    host.network.vlan.create_vlan(interface_name="Ethernet 1", vlan_id=4, method="proset")


def freebsd_driver_example():
    connection = RPyCConnection(ip="20.20.20.20")
    host = FreeBSDHost(connection=connection)
    host.driver.load_module(module_path="test/test")
