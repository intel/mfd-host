# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
from ipaddress import IPv4Address

from mfd_connect import RPyCConnection

from mfd_host.linux import LinuxHost


def linux_utils_ssh():
    connection = RPyCConnection(ip="20.20.20.20")
    host = LinuxHost(connection=connection)
    host.utils.remove_ssh_known_host(IPv4Address("10.0.0.1"), ssh_client_config_dir="~/.ssh")


def create_user():
    connection = RPyCConnection(ip="20.20.20.20")
    host = LinuxHost(connection=connection)
    host.utils.create_unprivileged_user("test_user", "test_password")


def remove_user():
    connection = RPyCConnection(ip="20.20.20.20")
    host = LinuxHost(connection=connection)
    host.utils.delete_unprivileged_user("test_user")
