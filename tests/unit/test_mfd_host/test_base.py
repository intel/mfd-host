# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Tests for `mfd_host` package."""

import sys

import pytest
from mfd_common_libs.exceptions import UnexpectedOSException
from mfd_connect import RPyCConnection
from mfd_network_adapter import NetworkInterface
from mfd_typing import OSName, PCIAddress
from mfd_typing.network_interface import LinuxInterfaceInfo, InterfaceType

from mfd_model.config import HostModel, NetworkInterfaceModelBase as NetworkInterfaceModel


from mfd_host import Host
from mfd_host.esxi import ESXiHost
from mfd_host.exceptions import HostConnectedOSNotSupported
from mfd_host.freebsd import FreeBSDHost
from mfd_host.linux import LinuxHost
from mfd_host.windows import WindowsHost


class TestHostCreation:
    @pytest.fixture
    def host(self, mocker):
        _connection = mocker.create_autospec(RPyCConnection)
        _connection.get_os_name.return_value = OSName.LINUX

        model = HostModel(role="sut")

        yield Host(connection=_connection, topology=model)
        mocker.stopall()

    def test_linux_host_created(self, mocker):
        conn = mocker.create_autospec(RPyCConnection)
        conn.get_os_name.return_value = OSName.LINUX

        assert isinstance(Host(connection=conn), LinuxHost)

    def test_windows_host_created(self, mocker):
        conn = mocker.create_autospec(RPyCConnection)
        conn.get_os_name.return_value = OSName.WINDOWS

        assert isinstance(Host(connection=conn), WindowsHost)

    def test_freebsd_owner_created(self, mocker):
        conn = mocker.create_autospec(RPyCConnection)
        conn.get_os_name.return_value = OSName.FREEBSD

        assert isinstance(Host(connection=conn), FreeBSDHost)

    def test_esxi_owner_created(self, mocker):
        conn = mocker.create_autospec(RPyCConnection)
        conn.get_os_name.return_value = OSName.ESXI

        assert isinstance(Host(connection=conn), ESXiHost)

    def test_unsupported_os(self, mocker):
        conn = mocker.create_autospec(RPyCConnection)
        conn.get_os_name.return_value = OSName.EFISHELL

        with pytest.raises(HostConnectedOSNotSupported):
            Host(connection=conn)

    def test_ordinary_constructor_os_supported_ok(self, mocker):
        conn = mocker.create_autospec(RPyCConnection)
        conn.get_os_name.return_value = OSName.LINUX

        assert isinstance(LinuxHost(connection=conn), LinuxHost)

    def test_ordinary_constructor_os_supported_fail(self, mocker):
        conn = mocker.create_autospec(RPyCConnection)
        conn.get_os_name.return_value = OSName.WINDOWS
        with pytest.raises(UnexpectedOSException):
            LinuxHost(connection=conn)

    def test_refresh_interfaces_ignore_instantiate_flag(self, host, mocker):
        interfaces_info = [
            LinuxInterfaceInfo(name="eth0"),
            LinuxInterfaceInfo(name="eth1"),
            LinuxInterfaceInfo(name="eth2"),
        ]
        mocker.patch(
            "mfd_network_adapter.network_adapter_owner.linux.LinuxNetworkAdapterOwner._get_all_interfaces_info",
            return_value=interfaces_info,
        )

        host.topology.network_interfaces = [NetworkInterfaceModel(interface_name="eth0", instantiate=False)]
        host.refresh_network_interfaces(ignore_instantiate=False)
        assert len(host.network_interfaces) == 0

        host.refresh_network_interfaces(ignore_instantiate=True)
        assert len(host.network_interfaces) == 1
        assert host.network_interfaces[0].name == "eth0"

        host.topology.network_interfaces = [NetworkInterfaceModel(interface_name="eth0", instantiate=True)]
        host.refresh_network_interfaces(ignore_instantiate=False)
        assert len(host.network_interfaces) == 1
        assert host.network_interfaces[0].name == "eth0"

        host.refresh_network_interfaces(ignore_instantiate=True)
        assert len(host.network_interfaces) == 1
        assert host.network_interfaces[0].name == "eth0"

    def test_refresh_interfaces_without_topology(self, host, mocker):
        interfaces_info = [
            LinuxInterfaceInfo(name="eth0"),
            LinuxInterfaceInfo(name="eth1"),
            LinuxInterfaceInfo(name="eth2"),
        ]
        mocker.patch(
            "mfd_network_adapter.network_adapter_owner.linux.LinuxNetworkAdapterOwner._get_all_interfaces_info",
            return_value=interfaces_info,
        )
        host.refresh_network_interfaces()
        assert len(host.network_interfaces) == 3

    def test_refresh_interfaces_with_topology_with_interfaces(self, host, mocker):
        interfaces_info = [
            LinuxInterfaceInfo(name="eth0"),
            LinuxInterfaceInfo(name="eth1"),
            LinuxInterfaceInfo(name="eth2"),
        ]
        mocker.patch(
            "mfd_network_adapter.network_adapter_owner.linux.LinuxNetworkAdapterOwner._get_all_interfaces_info",
            return_value=interfaces_info,
        )
        host.topology.network_interfaces = [NetworkInterfaceModel(interface_name="eth0", instantiate=False)]
        host.refresh_network_interfaces(ignore_instantiate=False)
        assert len(host.network_interfaces) == 0

        host.refresh_network_interfaces(ignore_instantiate=True)
        assert len(host.network_interfaces) == 1
        assert host.network_interfaces[0].name == "eth0"

        host.topology.network_interfaces = [NetworkInterfaceModel(interface_name="eth0", instantiate=True)]
        host.refresh_network_interfaces(ignore_instantiate=False)
        assert len(host.network_interfaces) == 1
        assert host.network_interfaces[0].name == "eth0"
        assert host.network_interfaces[0].topology is not None

        host.refresh_network_interfaces(ignore_instantiate=True)
        assert len(host.network_interfaces) == 1
        assert host.network_interfaces[0].name == "eth0"
        assert host.network_interfaces[0].topology is not None

    def test_refresh_interfaces_with_topology_without_interfaces(self, host, mocker):
        interfaces_info = [
            LinuxInterfaceInfo(name="eth0"),
            LinuxInterfaceInfo(name="eth1"),
            LinuxInterfaceInfo(name="eth2"),
        ]
        mocker.patch(
            "mfd_network_adapter.network_adapter_owner.linux.LinuxNetworkAdapterOwner._get_all_interfaces_info",
            return_value=interfaces_info,
        )
        host.topology.network_interfaces = []
        host.refresh_network_interfaces(ignore_instantiate=False)
        assert len(host.network_interfaces) == 3

        host.refresh_network_interfaces(ignore_instantiate=True)
        assert len(host.network_interfaces) == 3
        assert host.network_interfaces[0].name == "eth0"

    def test_refresh_interfaces_multiple(self, host, mocker):
        interfaces_info = [
            LinuxInterfaceInfo(name="eth0"),
            LinuxInterfaceInfo(name="eth1"),
            LinuxInterfaceInfo(name="eth2"),
        ]
        mocker.patch(
            "mfd_network_adapter.network_adapter_owner.linux.LinuxNetworkAdapterOwner._get_all_interfaces_info",
            return_value=interfaces_info,
        )
        host.topology.network_interfaces = [NetworkInterfaceModel(interface_name="eth0", instantiate=False)]
        host.refresh_network_interfaces(ignore_instantiate=False)
        host.refresh_network_interfaces(ignore_instantiate=True)
        host.refresh_network_interfaces(ignore_instantiate=False)
        host.refresh_network_interfaces(ignore_instantiate=True)
        host.refresh_network_interfaces(ignore_instantiate=True)
        host.refresh_network_interfaces(ignore_instantiate=True)
        host.refresh_network_interfaces(ignore_instantiate=True)
        assert len(host.network_interfaces) == 1
        assert host.network_interfaces[0].name == "eth0"

    def test_refresh_interfaces_multiple_interfaces_in_model(self, host, mocker):
        interfaces_info = [
            LinuxInterfaceInfo(name="eth0"),
            LinuxInterfaceInfo(name="eth1"),
            LinuxInterfaceInfo(name="eth2"),
        ]
        mocker.patch(
            "mfd_network_adapter.network_adapter_owner.linux.LinuxNetworkAdapterOwner._get_all_interfaces_info",
            return_value=interfaces_info,
        )
        host.topology.network_interfaces = [
            NetworkInterfaceModel(interface_name="eth0", instantiate=True),
            NetworkInterfaceModel(interface_name="eth1", instantiate=True),
        ]
        host.refresh_network_interfaces()
        assert len(host.network_interfaces) == 2
        assert host.network_interfaces[0].name == "eth0"
        assert host.network_interfaces[1].name == "eth1"

    def test_refresh_interfaces_extend(self, host, mocker):
        interfaces_info = [
            LinuxInterfaceInfo(name="eth0"),
            LinuxInterfaceInfo(name="eth1"),
            LinuxInterfaceInfo(name="eth2"),
            LinuxInterfaceInfo(name="vf_1", interface_type=InterfaceType.VF),
            LinuxInterfaceInfo(name="vf_2", interface_type=InterfaceType.VF),
            LinuxInterfaceInfo(name="vf_3", interface_type=InterfaceType.VF),
        ]
        mocker.patch(
            "mfd_network_adapter.network_adapter_owner.linux.LinuxNetworkAdapterOwner._get_all_interfaces_info",
            return_value=interfaces_info,
        )
        host.topology.network_interfaces = [NetworkInterfaceModel(interface_name="eth0", instantiate=False)]
        host.refresh_network_interfaces(ignore_instantiate=True)
        assert len(host.network_interfaces) == 1
        assert host.network_interfaces[0].name == "eth0"
        first_interface_id = id(host.network_interfaces[0])

        host.topology.network_interfaces = [NetworkInterfaceModel(interface_name="eth0", instantiate=True)]
        host.refresh_network_interfaces(ignore_instantiate=False, extended=[InterfaceType.VF])
        first_interface_id_after_refresh = id(host.network_interfaces[0])

        assert len(host.network_interfaces) == 4
        assert first_interface_id == first_interface_id_after_refresh
        assert host.network_interfaces[0].name == "eth0"
        assert host.network_interfaces[1].name == "vf_1"
        assert host.network_interfaces[2].name == "vf_2"
        assert host.network_interfaces[3].name == "vf_3"
        last_interface_id = id(host.network_interfaces[3])
        host.refresh_network_interfaces(ignore_instantiate=False, extended=[InterfaceType.VF])
        last_interface_id_after_refresh = id(host.network_interfaces[3])
        assert last_interface_id == last_interface_id_after_refresh
        assert len(host.network_interfaces) == 4

    def test__get_filtered_interface_info_by_topology(self, host):
        model = NetworkInterfaceModel(interface_name="eth0", instantiate=True)
        host.topology.network_interfaces = [model]
        interfaces_info = [
            LinuxInterfaceInfo(name="eth0"),
            LinuxInterfaceInfo(name="eth1"),
            LinuxInterfaceInfo(name="eth2"),
        ]
        filtered_info = [(LinuxInterfaceInfo(name="eth0"), model)]
        assert (
            host._get_filtered_interface_info_by_topology(interfaces_info=interfaces_info, ignore_instantiate=False)
            == filtered_info
        )

    def test__update_interfaces(self, host):
        interface_info = LinuxInterfaceInfo(name="eth0", namespace="foo")
        updated_namespace = "bar"
        updated_interface_info = LinuxInterfaceInfo(name="eth0", namespace=updated_namespace)
        interfaces_info = [updated_interface_info, LinuxInterfaceInfo(name="eth1"), LinuxInterfaceInfo(name="eth2")]
        interfaces_info = [(x, None) for x in interfaces_info]

        interface = NetworkInterface(connection=host.connection, interface_info=interface_info, topology=None)
        interfaces = [interface]

        host._update_interfaces(interfaces=interfaces, interfaces_info=interfaces_info)
        assert interface.namespace == updated_namespace
        assert interface.visited
        assert updated_interface_info.visited
        assert not getattr(interfaces_info[1], "visited", False)
        assert not getattr(interfaces_info[2], "visited", False)

    def test__add_interfaces_empty_list(self, host):
        interfaces_info = [
            LinuxInterfaceInfo(name="eth0"),
            LinuxInterfaceInfo(name="eth1"),
            LinuxInterfaceInfo(name="eth2"),
        ]
        interfaces = []

        host._add_interfaces(interfaces=interfaces, interfaces_info=[(x, None) for x in interfaces_info])
        assert len(interfaces) == 3
        assert all(isinstance(x, NetworkInterface) for x in interfaces)  # ensure all objects are NetworkIntefaces
        assert all(x._connection == host.connection for x in interfaces)  # ensure all objects share same connection

    def test__add_interfaces_non_empty_list(self, host):
        interfaces_info = [LinuxInterfaceInfo(name="eth1"), LinuxInterfaceInfo(name="eth2")]
        interfaces = [
            NetworkInterface(connection=host.connection, interface_info=LinuxInterfaceInfo(name="eth0"), topology=None)
        ]
        host._add_interfaces(interfaces=interfaces, interfaces_info=[(x, None) for x in interfaces_info])
        assert len(interfaces) == 3
        assert all(isinstance(x, NetworkInterface) for x in interfaces)  # ensure all objects are NetworkIntefaces
        assert all(x._connection == host.connection for x in interfaces)  # ensure all objects share same connection

    def test__remove_unvisited_interfaces_and_cleanup(self, host):
        nic_1 = NetworkInterface(connection=host.connection, interface_info=LinuxInterfaceInfo(name="eth0"))
        nic_2 = NetworkInterface(connection=host.connection, interface_info=LinuxInterfaceInfo(name="eth1"))
        nic_3 = NetworkInterface(connection=host.connection, interface_info=LinuxInterfaceInfo(name="eth2"))

        nic_1.visited = True
        nic_2.visited = False
        nic_3.visited = False
        interfaces = [nic_1, nic_2, nic_3]
        host._remove_unvisited_interfaces_and_cleanup(interfaces=interfaces)
        assert len(interfaces) == 1
        assert not getattr(nic_1, "visited", False)

    def test__add_visited_flag_to_objects(self, host):
        class A: ...

        objects = [A(), A(), A()]

        host._add_visited_flag_to_objects(objects=objects)
        assert all(not x.visited for x in objects)  # ensure 'visited' is added and set to False

    def test__create_virtualization_object_not_supported_os(self, host):
        host.connection.get_os_name.return_value = OSName.MELLANOX
        with pytest.raises(HostConnectedOSNotSupported):
            host._create_virtualization_object()

    def test__create_virtualization_object_esxi_os(self, host, mocker):
        host.connection.get_os_name.return_value = OSName.ESXI
        mocked_esxi = mocker.MagicMock()
        sys.modules["mfd_esxi.host"] = mocked_esxi
        host._create_virtualization_object()
        mocked_esxi.ESXiHypervisor.assert_called_once_with(connection=host.connection)

    def test__are_interfaces_same(self, host):
        pci_address_0 = PCIAddress(data="0000:5e:00.1")
        interface = NetworkInterface(
            connection=host.connection, interface_info=LinuxInterfaceInfo(name="eth0", pci_address=pci_address_0)
        )
        interface_info_1 = LinuxInterfaceInfo(name="eth1", pci_address=pci_address_0)
        interface_info_0 = LinuxInterfaceInfo(name="eth0", pci_address=pci_address_0)
        assert Host._are_interfaces_same(interface, interface_info_0)
        assert not Host._are_interfaces_same(interface, interface_info_1)
