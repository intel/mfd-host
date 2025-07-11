# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for ESXI Memory."""

from .base import BaseFeatureMemory
from .exceptions import ServerMemoryNotFoundError
import re


class ESXiMemory(BaseFeatureMemory):
    """ESXi class for Memory feature."""

    @property
    def ram(self) -> int:
        """
        Return bytes of RAM.

        :return: RAM in bytes
        :rtype: int
        """
        ram_command = "esxcli hardware memory get"
        output = self._connection.execute_command(
            command=ram_command, expected_return_codes={0}, shell=True
        ).stdout.splitlines()
        if not output:
            raise ServerMemoryNotFoundError(
                'Server memory not found, unexpected result of "esxcli hardware memory get"'
            )
        ram = re.search(r"(\d+)", output[0])
        if ram:
            return int(ram.group())
        raise ServerMemoryNotFoundError('Server memory not found, unexpected result of "esxcli hardware memory get"')
