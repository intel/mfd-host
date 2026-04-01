# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for Windows service."""

import logging

from mfd_common_libs import add_logging_level, log_levels

from mfd_host.feature.service.base import BaseFeatureService

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class WindowsService(BaseFeatureService):
    """Windows class for Service feature."""

    def restart_service(self, name: str) -> None:
        """
        Restart started service.

        :param name: name of service to restart
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg=f"Restarting service '{name}'")
        cmd = f'Restart-Service -Name "{name}" -Force'
        self._connection.execute_powershell(cmd, expected_return_codes={0})

    def get_service_status(self, name: str) -> str:
        """
        Get service status.

        :param name: name of service to get status of
        :return: service status string (e.g. "Running", "Stopped")
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg=f"Getting service '{name}'")
        cmd = f'(Get-Service -Name "{name}").Status'
        result = self._connection.execute_powershell(cmd, expected_return_codes={0})
        return result.stdout.strip()
