# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for FreeBSD service."""

import logging

from mfd_common_libs import add_logging_level, log_levels

from mfd_host.feature.service.base import BaseFeatureService

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class FreeBSDService(BaseFeatureService):
    """Class for FreeBSDService."""
