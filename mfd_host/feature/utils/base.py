# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for base utils."""

import logging
from abc import ABC, abstractmethod
from ipaddress import IPv4Address, IPv6Address
from typing import overload, TYPE_CHECKING

from mfd_common_libs import add_logging_level, log_levels
from mfd_connect.util.rpc_copy_utils import _get_hostname

from mfd_host.exceptions import UtilsFeatureException
from mfd_host.feature.base import BaseFeature

if TYPE_CHECKING:
    from mfd_network_adapter.network_interface.esxi import ESXiNetworkInterface
    from mfd_network_adapter.network_interface.freebsd import FreeBSDNetworkInterface
    from mfd_network_adapter.network_interface.linux import LinuxNetworkInterface
    from mfd_network_adapter.network_interface.windows import WindowsNetworkInterface

logger = logging.getLogger(__name__)
add_logging_level("MODULE_DEBUG", log_levels.MODULE_DEBUG)


class BaseFeatureUtils(BaseFeature, ABC):
    """Base class for Utils feature."""

    def get_interface_by_ip(
        self, ip: IPv4Address | IPv6Address, check_all_interfaces: bool = False
    ) -> "ESXiNetworkInterface | FreeBSDNetworkInterface | LinuxNetworkInterface | WindowsNetworkInterface":
        """
        Get interface with matching IP address.

        :param ip: IP address
        :param check_all_interfaces: True - gather all interfaces and check,
                                     False - check interfaces saved in network_interfaces attribute
        :return: Matching interface
        """
        interfaces_to_check = (
            self._host().network.get_interfaces() if check_all_interfaces else self._host().network_interfaces
        )
        ip_version = "v4" if isinstance(ip, IPv4Address) else "v6"
        for interface in interfaces_to_check:
            for addr in getattr(interface.ip.get_ips(), ip_version):
                if ip == addr.ip:
                    return interface

        raise UtilsFeatureException(f"Interface with ip {ip} not found.")

    def get_hostname(self) -> str:
        """Get hostname."""
        return _get_hostname(self._connection)

    @overload
    def set_icmp_echo(self, *, ignore_all: bool = False, ignore_broadcasts: bool = True, **kwargs) -> None: ...

    @overload
    def set_icmp_echo(self, *, ignore_broadcasts: bool = True, **kwargs) -> None: ...

    @abstractmethod
    def set_icmp_echo(self, *, ignore_broadcasts: bool = True, **kwargs) -> None:
        """
        Set ICMP broadcast.

        :param ignore_broadcasts: ICMP echo ignore broadcasts.
        """
