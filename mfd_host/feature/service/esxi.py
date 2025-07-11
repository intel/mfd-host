# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for ESXi service."""

import logging

from mfd_common_libs import add_logging_level, log_levels

from mfd_host.feature.service.base import BaseFeatureService

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class ESXiService(BaseFeatureService):
    """ESXi class for Service feature."""

    def restart_service(self, name: str) -> None:
        """
        Restart started service.

        :param name: name of service to restart
        """
        cmd = f"/etc/init.d/{name} restart"
        self._connection.execute_command(cmd, expected_return_codes={0})
