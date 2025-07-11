# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module to Test Windows Device."""

import pytest

from dataclasses import make_dataclass
from textwrap import dedent
from unittest.mock import patch

from mfd_common_libs import log_levels
from mfd_connect import RPyCConnection
from mfd_connect.base import ConnectionCompletedProcess
from mfd_connect.util import rpc_copy_utils
from mfd_devcon import Devcon
from mfd_host import Host
from mfd_host.exceptions import DeviceFeatureException
from mfd_network_adapter.data_structures import State
from mfd_network_adapter.network_interface.windows import WindowsNetworkInterface
from mfd_typing.network_interface import WindowsInterfaceInfo
from mfd_typing import MACAddress, OSName


class TestWindowsDevice:
    devcon_device_list_dataclass = make_dataclass(
        "DevconDevices",
        [
            ("device_instance_id", ""),
            ("device_desc", ""),
        ],
    )

    devcon_resource_list_dataclass = make_dataclass(
        "DevconResources",
        [("device_pnp", ""), ("name", ""), ("resources", [])],
    )
    device_dict = {
        "name": "Ethernet0",
        "pnp": "PCI\\VEN_8086&DEV_1592&SUBSYS_00028086&REV_01\\4&273B1A92&0&0710",
        "eth": "12",
        "mac": "AA:BB:CC:DD:EE:FF",
    }
    device = WindowsInterfaceInfo(
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

    @pytest.fixture
    def host(self, mocker):
        mocker.patch(
            "mfd_connect.util.rpc_copy_utils.copy",
            mocker.create_autospec(rpc_copy_utils.copy),
        )
        mocker.patch("mfd_devcon.Devcon.check_if_available", mocker.create_autospec(Devcon.check_if_available))
        mocker.patch("mfd_devcon.Devcon.get_version", mocker.create_autospec(Devcon.get_version, return_value="1.2"))
        mocker.patch(
            "mfd_devcon.Devcon._get_tool_exec_factory",
            mocker.create_autospec(Devcon._get_tool_exec_factory, return_value="devcon"),
        )
        _connection = mocker.create_autospec(RPyCConnection)
        _connection.get_os_name.return_value = OSName.WINDOWS
        yield Host(connection=_connection)
        mocker.stopall()

    def test_restart_devices(self, mocker, host):
        output = dedent(
            """
            {EDCF0178-D7AC-4A94-B7EF-2D17A1517D02}        : Restarted
            1 device(s) restarted.
            """
        )
        devcon_patch = mocker.patch(
            "mfd_devcon.Devcon.restart_devices",
            mocker.create_autospec(Devcon.remove_devices, return_value=output),
        )
        assert host.device.restart_devices(device_id="{EDCF0178-D7AC-4A94-B7EF-2D17A1517D02}") == output
        devcon_patch.assert_called_once()

    def test_find_devices(self, mocker, host):
        devcon_device_list_dataclass = [
            self.devcon_device_list_dataclass(
                device_instance_id="USB\\VID_413C&PID_A001\\0123456789", device_desc="Generic USB Hub"
            ),
            self.devcon_device_list_dataclass(
                device_instance_id="PCI\\VEN_8086&DEV_8D26&SUBSYS_06001028&REV_05\\3&3259BAD1&0&E8",
                device_desc="Standard Enhanced PCI to USB Host Controller",
            ),
        ]
        devcon_patch = mocker.patch(
            "mfd_devcon.Devcon.find_devices",
            mocker.create_autospec(Devcon.find_devices, return_value=devcon_device_list_dataclass),
        )
        assert (
            host.device.find_devices(device_id="{EDCF0178-D7AC-4A94-B7EF-2D17A1517D02}") == devcon_device_list_dataclass
        )
        devcon_patch.assert_called_once()

    def test_uninstall_devices(self, mocker, host):
        output = dedent(
            """
            PCI\\VEN_8086&DEV_8D2D&SUBSYS_06001028&REV_05\\3&3259BAD1&0&D0: Removed
            1 device(s) were removed.
            """
        )
        devcon_patch = mocker.patch(
            "mfd_devcon.Devcon.remove_devices",
            mocker.create_autospec(Devcon.remove_devices, return_value=output),
        )
        assert (
            host.device.uninstall_devices(device_id="PCI\\VEN_8086&DEV_8D2D&SUBSYS_06001028&REV_05\\3&3259BAD1&0&D0")
            == output
        )
        devcon_patch.assert_called_once()

    def test_get_description_for_code(self, mocker, host):
        output = "Code 14: This device cannot work properly until you restart your computer."
        assert host.device.get_description_for_code(error_code=14) == output

    def test_get_description_for_code_unknown(self, mocker, host):
        mocker_log = mocker.patch("mfd_host.feature.device.windows.logger.log")
        output = "Unknown error code"
        assert host.device.get_description_for_code(error_code=1400) == output
        mocker_log.assert_has_calls(
            [
                mocker.call(
                    level=log_levels.MODULE_DEBUG,
                    msg="Unknown error code: 1400",
                )
            ]
        )

    def test_get_device_status(self, mocker, host):
        os_output = dedent(
            """
            __GENUS                : 2
            __CLASS                : Win32_NetworkAdapter
            __SUPERCLASS           :
            __DYNASTY              :
            __RELPATH              :
            __PROPERTY_COUNT       : 1
            __DERIVATION           : {}
            __SERVER               :
            __NAMESPACE            :
            __PATH                 :
            ConfigManagerErrorCode : 45
            PSComputerName         :
            """
        )
        output = {
            "Error_code": 45,
            "Error_Description": "Code 45: Currently, this hardware device is not connected to the computer.",
        }
        host.connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=os_output, stderr=""
        )
        assert host.device.get_device_status(device_index=14) == output

    def test_get_device_status_error(self, mocker, host):
        os_output = dedent(
            """
            __GENUS                : 2
            __CLASS                : Win32_NetworkAdapter
            __SUPERCLASS           :
            __DYNASTY              :
            __RELPATH              :
            __PROPERTY_COUNT       : 1
            __DERIVATION           : {}
            __SERVER               :
            __NAMESPACE            :
            __PATH                 :
            ConfigManagerErrorCode :
            PSComputerName         :
            """
        )
        host.connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=os_output, stderr=""
        )
        with pytest.raises(DeviceFeatureException):
            host.device.get_device_status(device_index=14)

    def verify_device_state_helper(self, os_output, host):
        host.connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=os_output, stderr=""
        )

    def test_verify_device_state_enabled(self, host, mocker):
        os_output = dedent(
            """
            __GENUS                : 2
            ConfigManagerErrorCode : 0
            PSComputerName         :
            """
        )
        self.verify_device_state_helper(os_output=os_output, host=host)
        host.device._verify_device_state(device_index=2, state=State.ENABLED)

    def test_verify_device_state_disabled(self, host, mocker):
        os_output = dedent(
            """
            __GENUS                : 2
            ConfigManagerErrorCode : 22
            PSComputerName         :
            """
        )
        self.verify_device_state_helper(os_output=os_output, host=host)
        host.device._verify_device_state(device_index=2, state=State.DISABLED)

    def test_verify_device_state_disabled_fail(self, host, mocker):
        os_output = dedent(
            """
            __GENUS                : 2
            ConfigManagerErrorCode : 220
            PSComputerName         :
            """
        )
        self.verify_device_state_helper(os_output=os_output, host=host)
        with pytest.raises(DeviceFeatureException):
            host.device._verify_device_state(device_index=2, state=State.DISABLED)

    def test__verify_device_state_enabled_fail(self, host, mocker):
        os_output = dedent(
            """
            __GENUS                : 2
            ConfigManagerErrorCode : 220
            PSComputerName         :
            """
        )
        self.verify_device_state_helper(os_output=os_output, host=host)
        with pytest.raises(DeviceFeatureException):
            host.device._verify_device_state(device_index=2, state=State.ENABLED)

    def _get_resources_helper(self, resources, host):
        devcon_resource_list_dataclass = [
            self.devcon_resource_list_dataclass(
                device_pnp="PCI\\VEN_8086&DEV_1592&SUBSYS_00028086&REV_01\\4&273B1A92&0&0710",
                name="Intel(R) Ethernet Network Adapter E810-C-Q2 #8",
                resources=resources,
            )
        ]
        with patch.object(Devcon, "get_resources", return_value=devcon_resource_list_dataclass):
            return (
                host.device.get_resources(device_id="PCI\\VEN_8086&DEV_1592&SUBSYS_00028086&REV_01\\4&273B1A92&0&0710")
                == devcon_resource_list_dataclass
            )

    def test_get_resources(self, host):
        assert self._get_resources_helper(
            resources=["MEM : 37ff2000000-37ff3ffffff", "MEM : 37ffe000000-37ffe00ffff"], host=host
        )

    def __verify_resource_state_helper(self, resources, state, host):
        devcon_resource_list_dataclass = [
            self.devcon_resource_list_dataclass(
                device_pnp="PCI\\VEN_8086&DEV_1592&SUBSYS_00028086&REV_01\\4&273B1A92&0&0710",
                name="Intel(R) Ethernet Network Adapter E810-C-Q2 #8",
                resources=resources,
            )
        ]
        with patch.object(Devcon, "get_resources", return_value=devcon_resource_list_dataclass):
            return host.device._verify_resource_state(
                device_id="PCI\\VEN_8086&DEV_1592&SUBSYS_00028086&REV_01\\4&273B1A92&0&0710", state=state
            )

    def test__verify_resource_state_enabled(self, host, mocker):
        resources = ["MEM : 37ff2000000-37ff3ffffff", "MEM : 37ffe000000-37ffe00ffff"]
        self.__verify_resource_state_helper(resources=resources, state=State.ENABLED, host=host)

    def test__verify_resource_state_disabled(self, host, mocker):
        resources = []
        self.__verify_resource_state_helper(resources=resources, state=State.DISABLED, host=host)

    def test__verify_resource_state_enabled_fail(self, host, mocker):
        resources = []
        with pytest.raises(DeviceFeatureException):
            self.__verify_resource_state_helper(resources=resources, state=State.ENABLED, host=host)

    def test__verify_resource_state_disabled_fail(self, host, mocker):
        resources = ["MEM : 37ff2000000-37ff3ffffff"]
        with pytest.raises(DeviceFeatureException):
            self.__verify_resource_state_helper(resources=resources, state=State.DISABLED, host=host)

    def _verify_device_state_helper(self, os_output, resources, state, host):
        host.connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=os_output, stderr=""
        )
        devcon_resource_list_dataclass = [
            self.devcon_resource_list_dataclass(
                device_pnp="PCI\\VEN_8086&DEV",
                name="Intel(R) Ethernet",
                resources=resources,
            )
        ]
        interface = WindowsNetworkInterface(interface_info=self.device, connection=host.connection)
        with patch.object(
            Devcon,
            "get_resources",
            return_value=devcon_resource_list_dataclass,
        ):
            host.device.get_resources(device_id="PCI\\VEN_8086&DEV")
            host.device.verify_device_state(device=interface, state=State.ENABLED)

    def test_verify_device_state(self, host, mocker):
        os_output = dedent(
            """
            __GENUS                : 2
            ConfigManagerErrorCode : 0
            PSComputerName         :
            """
        )
        resources = ["MEM : 37ff2000000-37ff3ffffff"]
        self._verify_device_state_helper(os_output=os_output, resources=resources, state=State.ENABLED, host=host)

    def test_verify_device_state_fail(self, host, mocker):
        os_output = dedent(
            """
            __GENUS                : 2
            ConfigManagerErrorCode : 0
            PSComputerName         :
            """
        )
        interface = WindowsNetworkInterface(interface_info=self.device, connection=host.connection)
        self.verify_device_state_helper(os_output=os_output, host=host)
        with pytest.raises(DeviceFeatureException):
            host.device.verify_device_state(device=interface, state=State.DISABLED)

    def test_verify_device_state_resource_fail(self, host, mocker):
        os_output = dedent(
            """
            __GENUS                : 2
            ConfigManagerErrorCode : 22
            PSComputerName         :
            """
        )
        resources = ["MEM : 37ff2000000-37ff3ffffff"]
        with pytest.raises(DeviceFeatureException):
            self._verify_device_state_helper(os_output=os_output, resources=resources, state=State.DISABLED, host=host)

    def test_enable_device(self, host, mocker):
        enable_output = dedent(
            """
            PCI\\VEN_8086&DEV_1592&SUBSYS_00028086&REV_01\\4&273B1A92&0&0710: Enabled
            1 device(s) are enabled.
            """
        )
        devcon_patch = mocker.patch(
            "mfd_devcon.Devcon.enable_devices",
            mocker.create_autospec(Devcon.enable_devices, return_value=enable_output),
        )
        assert (
            host.device.enable_devices(device_id="PCI\\VEN_8086&DEV_1592&SUBSYS_00028086&REV_01\\4&273B1A92&0&0710")
            == enable_output
        )
        devcon_patch.assert_called_once()

    def test_disable_device(self, host, mocker):
        disable_output = dedent(
            """
            PCI\\VEN_8086&DEV_1592&SUBSYS_00028086&REV_01\\4&273B1A92&0&0710: Disabled
            1 device(s) are disabled.
            """
        )
        devcon_patch = mocker.patch(
            "mfd_devcon.Devcon.disable_devices",
            mocker.create_autospec(Devcon.disable_devices, return_value=disable_output),
        )
        assert (
            host.device.disable_devices(device_id="PCI\\VEN_8086&DEV_1592&SUBSYS_00028086&REV_01\\4&273B1A92&0&0710")
            == disable_output
        )
        devcon_patch.assert_called_once()

    def test_set_state_for_multiple_devices(self, host, mocker):
        enable_output = dedent(
            """
            PCI\\VEN_8086&DEV_1592&SUBSYS_00028086&REV_01\\4&273B1A92&0&0710: Enabled
            1 device(s) are enabled.
            """
        )
        enable_devices_patch = mocker.patch(
            "mfd_devcon.Devcon.enable_devices",
            mocker.create_autospec(Devcon.enable_devices, return_value=enable_output),
        )
        os_output = dedent(
            """
            __GENUS                : 2
            ConfigManagerErrorCode : 0
            PSComputerName         :
            """
        )
        interface = WindowsNetworkInterface(interface_info=self.device, connection=host.connection)
        host.connection.execute_powershell.return_value = ConnectionCompletedProcess(
            return_code=0, args="", stdout=os_output, stderr=""
        )
        devcon_resource_list_dataclass = [
            self.devcon_resource_list_dataclass(
                device_pnp="PCI\\VEN_8086&DEV_1592&SUBSYS_00028086&REV_01\\4&273B1A92&0&0710",
                name="Intel(R) Ethernet",
                resources=["MEM : 37ff2000000-37ff3ffffff"],
            )
        ]
        mocker.patch(
            "mfd_devcon.Devcon.get_resources",
            mocker.create_autospec(Devcon.get_resources, return_value=devcon_resource_list_dataclass),
        )
        host.device.set_state_for_multiple_devices(device_list=[interface], state=State.ENABLED)
        enable_devices_patch.assert_called_once()
