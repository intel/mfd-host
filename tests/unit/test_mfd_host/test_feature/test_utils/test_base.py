# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
from ipaddress import IPv4Interface, IPv6Interface, IPv4Address, IPv6Address

import pytest
from mfd_connect import RPyCConnection
from mfd_network_adapter.network_interface.feature.ip.data_structures import IPs
from mfd_typing import OSName
from mfd_network_adapter.network_interface.linux import LinuxNetworkInterface
from mfd_model.config import HostModel

from mfd_host import Host
from mfd_host.exceptions import UtilsFeatureException


class TestBaseUtils:
    @pytest.fixture
    def host(self, mocker):
        connection = mocker.create_autospec(RPyCConnection)
        connection.get_os_name.return_value = OSName.LINUX

        model = HostModel(role="sut")

        yield Host(connection=connection, topology=model)

        mocker.stopall()

    def test_get_interface_by_ip(self, host, mocker):
        interface_v4 = mocker.create_autospec(LinuxNetworkInterface)
        interface_v4.ip.get_ips.return_value = IPs(v4=[IPv4Interface("127.0.0.1/10")])

        interface_v6 = mocker.create_autospec(LinuxNetworkInterface)
        interface_v6.ip.get_ips.return_value = IPs(v6=[IPv6Interface("fe80::3efd:feff:fecf:8b72/64")])

        host.network_interfaces = [interface_v4, interface_v6]

        assert host.utils.get_interface_by_ip(IPv4Address("127.0.0.1")) is interface_v4
        assert host.utils.get_interface_by_ip(IPv6Address("fe80::3efd:feff:fecf:8b72")) is interface_v6

        with pytest.raises(UtilsFeatureException):
            host.utils.get_interface_by_ip(IPv4Interface("1.2.3.4"))

        host.network.get_interfaces = mocker.Mock(return_value=[interface_v4, interface_v6])

        assert host.utils.get_interface_by_ip(IPv4Address("127.0.0.1"), check_all_interfaces=True) is interface_v4
        assert (
            host.utils.get_interface_by_ip(IPv6Address("fe80::3efd:feff:fecf:8b72"), check_all_interfaces=True)
            is interface_v6
        )

        with pytest.raises(UtilsFeatureException):
            host.utils.get_interface_by_ip(IPv4Interface("1.2.3.4"), check_all_interfaces=True)
