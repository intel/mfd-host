# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for FreeBSD CPU."""

import logging

from mfd_common_libs import add_logging_level, log_levels
from mfd_host.feature.cpu.base import BaseFeatureCPU
from mfd_sysctl.freebsd import FreebsdSysctl

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class FreeBSDCPU(BaseFeatureCPU):
    """FreeBSD class for CPU feature."""

    def get_log_cpu_no(self) -> int:
        """Get the number of logical CPUs.

        :return: Number of logical cpus
        """
        self._sysctl_freebsd = FreebsdSysctl(connection=self._connection)
        return self._sysctl_freebsd.get_log_cpu_no()
