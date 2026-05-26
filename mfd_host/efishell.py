# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for Host for UEFI Shell OS."""

import logging

from mfd_common_libs import add_logging_level, log_levels, os_supported
from mfd_typing import OSName

from .base import Host

logger = logging.getLogger(__name__)
add_logging_level(level_name="MODULE_DEBUG", level_value=log_levels.MODULE_DEBUG)


class EFIShellHost(Host):
    """Class for EFI Shell host."""

    __init__ = os_supported(OSName.EFISHELL)(Host.__init__)
