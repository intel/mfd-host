# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for linux utils."""

import logging
from typing import Union, TYPE_CHECKING

from mfd_common_libs import add_logging_level, log_levels
from mfd_base_tool.exceptions import ToolNotAvailable

from mfd_host.exceptions import HostModuleException, UtilsFeatureExecutionError
from mfd_host.feature.utils.base import BaseFeatureUtils

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)

if TYPE_CHECKING:
    from ipaddress import IPv6Address, IPv4Address


class LinuxUtils(BaseFeatureUtils):
    """Linux class for Utils feature."""

    def remove_ssh_known_host(self, host_ip: Union["IPv4Address", "IPv6Address"], ssh_client_config_dir: str) -> None:
        """
        Remove specific host_ip keys from known_host file.

        e.g. sed -i "/100.0.0.100/d" ~/.ssh/known_hosts

        :param host_ip: IP address
        :param ssh_client_config_dir: Path to known_hosts file as per user used for execution of script
        :raises HostModuleException: on failure.
        """
        cmd = f"sed -i '/{host_ip}/d' {ssh_client_config_dir}/known_hosts"
        try:
            self._connection.execute_command(cmd, shell=True)
        except Exception as err:
            raise HostModuleException(f"SSH keys removal failed with error :'{err}'")

    def _get_program_cmd(self, tool: str) -> str:
        """
        Get path to tool binary.

        :param tool: Name of tool
        :return: path to tool binary
        :raises ToolNotAvailable when tool cannot be found in $PATH
        """
        which_cmd = f"which {tool}"
        return self._connection.execute_command(command=which_cmd, custom_exception=ToolNotAvailable).stdout.strip()

    def start_kedr(self, driver_name: str) -> None:
        """
        Attach KEDR module to a driver.

        :param driver_name: Name of the driver to check for memory leaks (ixgbe, i40e, ice, etc)
        :raises ToolNotAvailable when tool cannot be found in $PATH
        """
        kedr_path = self._get_program_cmd("kedr")
        cmd = rf'"{kedr_path} start {driver_name}"'
        res = self._connection.execute_command(cmd, stderr_to_stdout=True, expected_return_codes=None)
        if res.return_code != 0:
            if res.stdout.find("Service is already running") >= 0:
                raise HostModuleException("Attempted to start KEDR when it is already running. Bad cleanup?")
            elif res.stdout.find("the target module is already loaded") >= 0:
                raise HostModuleException("You must unload the driver before starting KEDR")
            else:
                raise HostModuleException(f"Cannot execute command: {cmd}")

    def stop_kedr(self) -> None:
        """
        Stop the KEDR process.

        The driver must be unloaded for this to work.

        :raises ToolNotAvailable when tool cannot be found in $PATH
        """
        kedr_path = self._get_program_cmd("kedr")
        cmd = rf'"{kedr_path} stop"'
        res = self._connection.execute_command(cmd, stderr_to_stdout=True, expected_return_codes=None)
        if res.return_code != 0:
            if res.stdout.find("the target module is still loaded") >= 0:
                # Handle this error appropriately to clean up nicely
                raise HostModuleException("You must unload the driver before stopping KEDR")
            elif res.stdout.find("Service is not running.") >= 0:
                logger.log(level=log_levels.MODULE_DEBUG, msg="KEDR was not running, no stop needed")
            else:
                raise HostModuleException(f"Cannot execute command: {cmd}")

    def create_unprivileged_user(self, username: str, password: str) -> None:
        """
        Create unprivileged user.

        :param username: user's name
        :param password: password for user
        """
        cmd = f"adduser {username} && echo '{username}:{password}' | chpasswd"
        self._connection.execute_command(cmd, shell=True)

    def delete_unprivileged_user(self, username: str) -> None:
        """
        Delete unprivileged user.

        :param username: user's name
        """
        cmd = f"userdel -r {username}"
        self._connection.execute_command(cmd)

    def set_icmp_echo(self, *, ignore_all: bool = False, ignore_broadcasts: bool = True) -> None:
        """
        Set ICMP broadcast.

        :param ignore_all: ICMP echo ignore all.
        :param ignore_broadcasts: ICMP echo ignore broadcasts.
        """
        cmd = f"echo '{int(ignore_all)}' > /proc/sys/net/ipv4/icmp_echo_ignore_all"
        self._connection.execute_command(cmd, shell=True)

        cmd = f"echo '{int(ignore_broadcasts)}' > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts"
        self._connection.execute_command(cmd, shell=True)

    def get_pretty_name(self) -> str:
        """
        Get distro name from /etc/os-release.

        :raises: UtilsFeatureExecutionError raised if file is empty or does not exist
        :return: distro name.
        """
        cmd = "cat /etc/os-release | grep -i 'pretty_name'"
        res = self._connection.execute_command(cmd, custom_exception=UtilsFeatureExecutionError, shell=True)

        return res.stdout.split("=", 1)[1].rstrip().replace('"', "")
