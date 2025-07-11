# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for base memory."""

import logging
from abc import ABC
from mfd_common_libs import add_logging_level, log_levels
from mfd_host.feature.base import BaseFeature
from typing import TYPE_CHECKING
from mfd_mount import Mount

if TYPE_CHECKING:
    from mfd_connect import Connection
    from mfd_host import Host

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class BaseFeatureMemory(BaseFeature, ABC):
    """Base class for Memory feature."""

    def __init__(self, connection: "Connection", host: "Host"):
        """Initialize Base Memory Feature."""
        self._connection = connection
        self._mount = Mount(connection=connection)
