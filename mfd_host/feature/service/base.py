# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for base service."""

import logging
from abc import ABC

from mfd_common_libs import add_logging_level, log_levels

from mfd_host.feature.base import BaseFeature

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class BaseFeatureService(BaseFeature, ABC):
    """Base class for Service feature."""
