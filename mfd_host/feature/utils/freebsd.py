# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for freebsd utils."""

from mfd_host.feature.utils import BaseFeatureUtils


class FreeBSDUtils(BaseFeatureUtils):
    """FreeBSD class for Utils feature."""

    def set_icmp_echo(self, *, ignore_broadcasts: bool = True, **kwargs) -> None:
        """
        Set icmp broadcast.

        kwargs to allow unified calls of this method, as on FreeBSD different params are supported than on Linux.

        :param ignore_broadcasts: ICMP echo ignore broadcasts.
        """
        cmd = f"sysctl net.inet.icmp.bmcastecho={int(ignore_broadcasts is False)}"
        self._connection.execute_command(cmd)
