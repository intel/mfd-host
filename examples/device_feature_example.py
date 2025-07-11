# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Example of Device Feature usage."""

import logging
from mfd_connect import RPyCConnection
from mfd_host import Host
from mfd_network_adapter.data_structures import State
from mfd_network_adapter.network_interface.windows import WindowsNetworkInterface
from mfd_typing.network_interface import WindowsInterfaceInfo
from mfd_typing import MACAddress


conn = RPyCConnection(ip="10.0.0.10")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

host_obj = Host(connection=conn)
interface_info = WindowsInterfaceInfo(
        pci_address=None,
        pci_device=None,
        name="Ethernet 2",
        mac_address=MACAddress("aa:bb:cc:dd:ee:ff"),
        installed=True,
        branding_string="Intel(R) Ethernet Controller X550",
        vlan_info=None,
        index="2",
        manufacturer="Intel Corporation",
        net_connection_status="7",
        pnp_device_id="PCI\\VEN_8086&DEV_1563&SUBSYS_35D48086&REV_01\\0000C9FFFF00000001",
        product_name="Intel(R) Ethernet Controller X550",
        service_name="ixgbi",
        guid="{F9E5C035-3B25-4CCF-8308-780F3623F0C6}",
        speed="9223372036854775807",
        cluster_info=None,
    )
interface = WindowsNetworkInterface(connection=conn, interface_info=interface_info)
host_obj.device.find_devices(pattern="=PrintQueue")
host_obj.device.find_devices(device_id="USB\\ROOT_HUB30\\5&20BE2FCD&0&0")
host_obj.device.uninstall_devices(device_id="SWD\\PRINTENUM\\{BAF9C437-DA87-4CDC-95E4-B8AB0B316969}")
host_obj.device.restart_devices(device_id=r"SWD\PRINTENUM\PRINTQUEUES")
host_obj.device.restart_devices(pattern="=PrintQueue")
host_obj.device.get_description_for_code(error_code=12)
host_obj.device.get_device_status(device_index=500)
host_obj.device.get_resources(device_id="PCI\\VEN_8086&DEV_1592&SUBSYS_00028086&REV_01\\4&273B1A92&0&0710")
host_obj.device.verify_device_state(
    device=interface,
    state=State.ENABLED,
)
host_obj.device.set_state_for_multiple_devices(
    device_dict_list=[
        interface
    ],
    state=State.ENABLED,
)
