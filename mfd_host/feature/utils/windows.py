# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for windows utils."""

from mfd_host.feature.utils import BaseFeatureUtils


class WindowsUtils(BaseFeatureUtils):
    """Windows class for Utils feature."""

    def set_icmp_echo(self, *, ignore_broadcasts: bool = True, **kwargs) -> None:
        """
        Set ICMP broadcast.

        :param ignore_broadcasts: ICMP echo ignore broadcasts.
        """
        raise NotImplementedError
