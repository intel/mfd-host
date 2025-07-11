# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for Linux service."""

import logging

from mfd_common_libs import add_logging_level, log_levels
from mfd_connect.util.process_utils import stop_process_by_name

from mfd_host.exceptions import ServiceFeatureException
from mfd_host.feature.service.base import BaseFeatureService

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class LinuxService(BaseFeatureService):
    """Linux class for Service feature."""

    def restart_service(self, name: str) -> None:
        """
        Restart started service.

        :param name: name of service to restart
        """
        cmd = f"service {name} restart"
        result = self._connection.execute_command(cmd, expected_return_codes={0, 1, 127})
        if result.return_code != 0:
            cmd = f"systemctl restart {name}"
            self._connection.execute_command(cmd, expected_return_codes={0})

    def restart_libvirtd(self) -> None:
        """Restart libvirt daemon service."""
        self.restart_service("libvirtd")

    def stop_irqbalance(self) -> None:
        """
        Kill irqbalance, if it is running.

        :raises ServiceFeatureException: In case of failure
        """
        stop_process_by_name(self._connection, "irqbalance")

    def start_irqbalance(self) -> None:
        """Start irqbalance daemon."""
        self._connection.execute_command("irqbalance")

    def is_service_running(self, name: str) -> bool:
        """
        Check the service run status.

        :param name: Service to check
        :return: the activeness of the service
        """
        cmd = f'systemctl status {name} 2>&1 | grep -i "active" | grep "running" | wc -l'
        result = self._connection.execute_command(cmd, shell=True, expected_return_codes={0})
        if result.stdout.rstrip() != "0":
            logger.log(level=log_levels.MODULE_DEBUG, msg=f"{name} is present and running")
            return True

        logger.log(level=log_levels.MODULE_DEBUG, msg=f"{name} is not running or no service is present")
        return False

    def is_network_manager_running(self) -> bool:
        """
        Check the NetworkManager service run status.

        :return: the run status of the NetworkManager
        """
        return self.is_service_running("NetworkManager")

    def set_network_manager(self, *, enable: bool) -> None:
        """
        Enable/Disable Network Manager.

        :param enable: Flag for deciding whether to enable or disable
        :raises ServiceFeatureException: if you cannot change the state of the service
        """
        if enable:
            states = ("unmask", "start", "enable")
        else:
            states = ("stop", "disable", "mask")

        for command in states:
            result = self._connection.execute_command(
                f"systemctl {command} NetworkManager.service", expected_return_codes=None
            )
            if result.return_code != 0:
                if (
                    "Unit NetworkManager.service not loaded." in result.stdout
                    or "Unit file NetworkManager.service does not exist." in result.stdout
                    or "Unit NetworkManager.service does not exist" in result.stdout
                ):
                    logger.log(
                        level=log_levels.MODULE_DEBUG,
                        msg=f"NetworkManager {command} on {self._connection.ip} is already done.",
                    )
                else:
                    raise ServiceFeatureException(f"Unable to {command} on {self._connection.ip}")
            else:
                logger.log(level=log_levels.MODULE_DEBUG, msg=f"NetworkManager {command} on {self._connection.ip}")
