# Copyright 2024-2024 Intel Corporation.
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed
# by the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.
"""Module for Windows Device."""

import logging
import re
import typing

from mfd_common_libs import add_logging_level, log_levels
from mfd_devcon import Devcon
from mfd_host.exceptions import DeviceFeatureException
from mfd_host.feature.device.base import BaseFeatureDevice
from mfd_network_adapter.data_structures import State
from .device_const import DEVICE_STATUS_DESCRIPTION_MAP

if typing.TYPE_CHECKING:
    from mfd_connect import Connection
    from mfd_devcon import DevconDevices
    from mfd_devcon import DevconResources
    from mfd_host import Host
    from mfd_network_adapter.network_interface.windows import WindowsNetworkInterface

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class WindowsDevice(BaseFeatureDevice):
    """Windows class for Device feature."""

    def __init__(self, *, connection: "Connection", host: "Host") -> None:
        """
        Initialize the Windows Device feature.

        :param connection: Object of mfd-connect
        :param host: Object of mfd-host
        """
        super().__init__(connection=connection, host=host)
        self._connection = connection
        self._devcon = Devcon(connection=self._connection)

    def find_devices(self, device_id: str = "", pattern: str = "") -> list["DevconDevices"]:
        """
        Find devices that are currently attached to the computer.

        :param device_id: hardware ID, compatible ID, or device instance ID of a device
        :param pattern: devices to look for specified by ID, class, or all devices (*)
        :return: parsed devcon output
        """
        return self._devcon.find_devices(device_id=device_id, pattern=pattern)

    def uninstall_devices(self, device_id: str = "", pattern: str = "", reboot: bool = False) -> str:
        """
        Remove the device from the device tree and deletes the device stack for the device.

        :param device_id: hardware ID, compatible ID, or device instance ID of a device
        :param pattern: devices to get hwids for specified by ID, class, or all devices (*)
        :param reboot: Set to True if conditional reboot needs to be enabled, else False
        :return: output of executed devcon command
        """
        return self._devcon.remove_devices(device_id=device_id, pattern=pattern, reboot=reboot)

    def get_description_for_code(self, error_code: int) -> str:
        """
        Fetch error description for a particular error code.

        :param error_code: config manager error code
        :return: error description for the error code
        """
        description = DEVICE_STATUS_DESCRIPTION_MAP.get(error_code, "Unknown error code")
        if description == "Unknown error code":
            logger.log(level=log_levels.MODULE_DEBUG, msg=f"Unknown error code: {error_code}")
        return description

    def restart_devices(self, device_id: str = "", pattern: str = "", reboot: bool = False) -> str:
        """
        Stop and restart the specified devices.

        :param device_id: hardware ID, compatible ID, or device instance ID of a device
        :param pattern: devices to get hwids for specified by ID, class, or all devices (*)
        :param reboot: Set to True if conditional reboot needs to be enabled, else False
        :return: output of executed devcon command
        """
        return self._devcon.restart_devices(device_id=device_id, pattern=pattern, reboot=reboot)

    def get_device_status(self, device_index: int) -> dict[str, dict[int, str]]:
        """
        Get device status using the device index.

        :param device_index: Index number of the requested network adapter
        return: dictionary containing error code and description
        :raises DeviceFeatureException: if Unable to get ConfigManagerErrorCode
        """
        cmd = rf'gwmi win32_networkadapter -Filter "Index={device_index}" -Property ConfigManagerErrorCode'
        output = self._connection.execute_powershell(cmd)
        match = re.search(r"ConfigManagerErrorCode(\s+):(\s+)(?P<ErrorCode>\d+)", output.stdout)
        if match:
            error_code = int(match.group("ErrorCode"))
            description = DEVICE_STATUS_DESCRIPTION_MAP.get(error_code, "Unknown error code")
            if description == "Unknown error code":
                logger.log(level=log_levels.MODULE_DEBUG, msg=f"Unknown error code: {error_code}")
            return {"Error_code": error_code, "Error_Description": description}
        else:
            raise DeviceFeatureException("Unable to get ConfigManagerErrorCode")

    def get_resources(
        self, device_id: str = "", pattern: str = "", resource_filter: str = "all"
    ) -> list["DevconResources"]:
        """
        Get the resources allocated to the specified devices.

        :param device_id: hardware ID, compatible ID, or device instance ID of a device
        :param pattern: devices to get resources for specified by ID, class, or all devices (*)
        :param resource_filter: specify resources to be fetched for a given device.
                                return only specified resources if any
        :return: parsed devcon output
        :raises DevconExecutionError: if devcon command execution fails
        :raises DevconException: if devcon command output consists of known errors
        """
        return self._devcon.get_resources(device_id=device_id, pattern=pattern, resource_filter=resource_filter)

    def _verify_device_state(self, device_index: int, state: State) -> None:
        """
        Verify if the device is in the desired state.

        :param device_id: Index number of the requested network adapter
        :param state: expected State (enable/disable) of the device
        :raises DeviceFeatureException: if Unable to verify the device status
        """
        error_code = self.get_device_status(device_index).get("Error_code")
        error_desc = DEVICE_STATUS_DESCRIPTION_MAP.get(error_code, "")
        if (state is State.ENABLED and ("Code 0:" not in error_desc)) or (
            state is State.DISABLED and ("Code 22:" not in error_desc)
        ):
            raise DeviceFeatureException(f"get_device_status returned error: {error_code}")

    def _verify_resource_state(self, device_id: str, state: State) -> None:
        """
        Verify if the device's resources are available as expected based on the device's state.

        :param device_id: hardware ID, compatible ID, or device instance ID of a device
        :param state: expected state (enable/disable) of the device
        :raises DeviceFeatureException: if Unable to verify the resource state
        """
        out = self.get_resources(device_id=device_id)
        for device in out:
            if (state is State.ENABLED and not device.resources) or (state is State.DISABLED and device.resources):
                raise DeviceFeatureException(f"Devcon get resources error: {out}")

    def verify_device_state(self, device: "WindowsNetworkInterface", state: State) -> None:
        """
        Check if a device is in a specified state and if its resources are available as expected.

        :param device: dictionary entry that provides device pnp ID and device interface index
        :param state: expected state (enable/disable) of the device
        """
        self._verify_device_state(device_index=device.index, state=state)
        self._verify_resource_state(device_id=device.pnp_device_id, state=state)

    def enable_devices(self, device_id: str = "", pattern: str = "", reboot: bool = False) -> str:
        """
        Enable devices on the computer.

        :param device_id: hardware ID, compatible ID, or device instance ID of a device
        :param pattern: devices to be enabled specified by ID, class, or all devices (*)
        :param reboot: Set to True if conditional reboot needs to be enabled, else False
        :return: output of executed devcon command
        :raises DevconExecutionError: if devcon command execution fails
        :raises DevconException: if devcon command output consists of known errors
        """
        return self._devcon.enable_devices(device_id=device_id, pattern=pattern, reboot=reboot)

    def disable_devices(self, device_id: str = "", pattern: str = "", reboot: bool = False) -> str:
        """
        Disable devices on the computer.

        :param device_id: hardware ID, compatible ID, or device instance ID of a device
        :param pattern: devices to be disabled specified by ID, class, or all devices (*)
        :param reboot: Set to True if conditional reboot needs to be enabled, else False
        :return: output of executed devcon command
        :raises DevconExecutionError: if devcon command execution fails
        :raises DevconException: if devcon command output consists of known errors
        """
        return self._devcon.disable_devices(device_id=device_id, pattern=pattern, reboot=reboot)

    def set_state_for_multiple_devices(self, device_list: list["WindowsNetworkInterface"], state: State) -> None:
        """
        Enable/Disable multiple devices specified through a list of dictionaries.

        :param device_dict_list: list of dictionaries with device_id
        :param state: required state (enable/disable) of the devices
        :raises DeviceFeatureException: if state set for any device failed
        """
        for device in device_list:
            if state is State.DISABLED:
                out = self.disable_devices(device.pnp_device_id)
                if "1 device(s) disabled" not in out:
                    raise DeviceFeatureException(f"Devcon disable error: {out}")
            elif state is State.ENABLED:
                out = self.enable_devices(device.pnp_device_id)
                if "1 device(s) are enabled" not in out:
                    raise DeviceFeatureException(f"Devcon disable error: {out}")
            self.verify_device_state(device, state)
