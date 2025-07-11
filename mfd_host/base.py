# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for Host."""

import logging
import typing
from abc import ABC
from typing import Optional, Union, List

from mfd_common_libs import add_logging_level, log_levels
from mfd_typing import OSName, PCIAddress, PCIDevice
from mfd_typing.network_interface import InterfaceType, InterfaceInfo

from .exceptions import HostConnectedOSNotSupported, NetworkInterfaceRefreshException, HostConnectionTypeNotSupported
from .feature.stats import BaseFeatureStats, StatsFeatureType

if typing.TYPE_CHECKING:
    from mfd_connect import (
        Connection,
    )
    from mfd_network_adapter.network_interface.esxi import ESXiNetworkInterface
    from mfd_network_adapter.network_interface.freebsd import FreeBSDNetworkInterface
    from mfd_network_adapter.network_interface.linux import LinuxNetworkInterface
    from mfd_network_adapter.network_interface.windows import WindowsNetworkInterface
    from mfd_network_adapter.network_adapter_owner.esxi import ESXiNetworkAdapterOwner
    from mfd_network_adapter.network_adapter_owner.freebsd import FreeBSDNetworkAdapterOwner
    from mfd_network_adapter.network_adapter_owner.linux import LinuxNetworkAdapterOwner
    from mfd_network_adapter.network_adapter_owner.linux_ipu import IPULinuxNetworkAdapterOwner
    from mfd_network_adapter.network_adapter_owner.windows import WindowsNetworkAdapterOwner
    from mfd_package_manager import (
        PackageManager,
        LinuxPackageManager,
        WindowsPackageManager,
        ESXiPackageManager,
        BSDPackageManager,
    )
    from mfd_esxi.host import ESXiHypervisor
    from mfd_hyperv.hypervisor import HypervHypervisor
    from mfd_kvm.hypervisor import KVMHypervisor
    from mfd_cli_client import CliClient
    from mfd_powermanagement.base import PowerManagement
    from mfd_network_adapter import NetworkAdapterOwner, NetworkInterface
    from mfd_network_adapter.network_adapter_owner.base import InterfaceInfoType

    from mfd_model.config import HostModel, NetworkInterfaceModelBase as NetworkInterfaceModel
    from mfd_connect.util.connection_utils import Connections
    from mfd_dmesg import Dmesg
    from mfd_event_log import EventLog

    from .feature.utils import UtilsFeatureType
    from .feature.memory import MemoryFeatureType
    from .feature.cpu import CPUFeatureType
    from .feature.service import ServiceFeatureType
    from .feature.device import DeviceFeatureType

logger = logging.getLogger(__name__)
add_logging_level(level_name="MODULE_DEBUG", level_value=log_levels.MODULE_DEBUG)


class Host(ABC):
    """Abstract class for host."""

    def __new__(cls, connection: "Connection", *args, **kwargs):
        """
        Choose Host subclass based on provided connection object.

        :param connection:
        :return: instance of Host subclass.
        """
        if cls != Host:
            return super().__new__(cls)

        from .linux import LinuxHost
        from .windows import WindowsHost
        from .esxi import ESXiHost
        from .freebsd import FreeBSDHost

        os_name = connection.get_os_name()
        os_name_to_class = {
            OSName.LINUX: LinuxHost,
            OSName.WINDOWS: WindowsHost,
            OSName.ESXI: ESXiHost,
            OSName.FREEBSD: FreeBSDHost,
        }

        if os_name not in os_name_to_class.keys():
            raise HostConnectedOSNotSupported(f"Unsupported OS for Host: {os_name}")

        owner_class = os_name_to_class.get(os_name)
        return super().__new__(owner_class)

    def __init__(self, *, connection: "Connection", **kwargs):
        """
        Initialize Host.

        :param connection: Instance of mfd-connect connection.
        """
        self.connection = connection
        self.name: str = kwargs.get("name")
        self.network_interfaces: list[
            Union[
                "NetworkInterface",
                "FreeBSDNetworkInterface",
                "ESXiNetworkInterface",
                "LinuxNetworkInterface",
                "WindowsNetworkInterface",
            ]
        ] = []
        self.cli_client: Optional["CliClient"] = kwargs.get("cli_client")
        self.connections: Optional["Connections"] = kwargs.get("connections")
        self.power_mng: Optional[list["PowerManagement"]] = kwargs.get("power_mng")
        self.topology: Optional["HostModel"] = kwargs.get("topology")

        # Feature lazy initialization in properties
        self._network: Optional[
            Union[
                "NetworkAdapterOwner",
                "ESXiNetworkAdapterOwner",
                "FreeBSDNetworkAdapterOwner",
                "LinuxNetworkAdapterOwner",
                "IPULinuxNetworkAdapterOwner",
                "WindowsNetworkAdapterOwner",
            ]
        ] = None
        self._driver: Optional[
            Union[
                "PackageManager",
                "LinuxPackageManager",
                "WindowsPackageManager",
                "ESXiPackageManager",
                "BSDPackageManager",
            ]
        ] = None

        self._event: EventLog | Dmesg | None = None
        self._virtualization: Optional[Union["HypervHypervisor", "KVMHypervisor", "ESXiHypervisor"]] = None
        self._utils: Optional[UtilsFeatureType] = None
        self._memory: Optional[MemoryFeatureType] = None
        self._stats: Optional[StatsFeatureType] = None
        self._cpu: Optional[CPUFeatureType] = None
        self._service: ServiceFeatureType | None = None
        self._device: DeviceFeatureType | None = None

    @property
    def network(
        self,
    ) -> Union[
        "NetworkAdapterOwner",
        "ESXiNetworkAdapterOwner",
        "FreeBSDNetworkAdapterOwner",
        "LinuxNetworkAdapterOwner",
        "IPULinuxNetworkAdapterOwner",
        "WindowsNetworkAdapterOwner",
    ]:
        """Network feature."""
        if self._network is None:
            from mfd_network_adapter import NetworkAdapterOwner

            self._network = NetworkAdapterOwner(connection=self.connection, cli_client=self.cli_client)

        return self._network

    @property
    def driver(
        self,
    ) -> Union[
        "PackageManager", "LinuxPackageManager", "WindowsPackageManager", "ESXiPackageManager", "BSDPackageManager"
    ]:
        """Driver feature."""
        if self._driver is None:
            from mfd_package_manager import PackageManager

            self._driver = PackageManager(connection=self.connection)

        return self._driver

    @property
    def event(self) -> "EventLog | Dmesg":
        """Event feature."""
        if self._event is None:
            from mfd_dmesg import Dmesg
            from mfd_event_log import EventLog
            from mfd_connect import RPyCConnection
            from .esxi import ESXiHost
            from .linux import LinuxHost
            from .freebsd import FreeBSDHost
            from .windows import WindowsHost

            if self.__class__ in [ESXiHost, FreeBSDHost, LinuxHost]:
                self._event = Dmesg(connection=self.connection)
            elif self.__class__ in [WindowsHost] and type(self.connection) in [RPyCConnection]:
                self._event = EventLog(connection=self.connection)
            else:
                raise HostConnectionTypeNotSupported(
                    f"Unsupported connection type: {type(self.connection)} for event feature."
                )

        return self._event

    @property
    def virtualization(self) -> Union["HypervHypervisor", "KVMHypervisor", "ESXiHypervisor"]:
        """Virtualization feature."""
        if self._virtualization is None:
            self._create_virtualization_object()

        return self._virtualization

    @property
    def utils(self) -> "UtilsFeatureType":
        """Utils feature."""
        if self._utils is None:
            from .feature.utils import BaseFeatureUtils

            self._utils = BaseFeatureUtils(connection=self.connection, host=self)

        return self._utils

    @property
    def memory(self) -> "MemoryFeatureType":
        """Memory feature."""
        if self._memory is None:
            from .feature.memory import BaseFeatureMemory

            self._memory = BaseFeatureMemory(connection=self.connection, host=self)
        return self._memory

    @property
    def stats(self) -> StatsFeatureType:
        """Stats feature."""
        if self._stats is None:
            self._stats = BaseFeatureStats(connection=self.connection, host=self)
        return self._stats

    @property
    def cpu(self) -> "CPUFeatureType":
        """CPU feature."""
        if self._cpu is None:
            from .feature.cpu import BaseFeatureCPU

            self._cpu = BaseFeatureCPU(connection=self.connection, host=self)
        return self._cpu

    @property
    def service(self) -> "ServiceFeatureType":
        """Service feature."""
        if self._service is None:
            from .feature.service import BaseFeatureService

            self._service = BaseFeatureService(connection=self.connection, host=self)
        return self._service

    @property
    def device(self) -> "DeviceFeatureType":
        """Device feature."""
        if self._device is None:
            from .feature.device import BaseFeatureDevice

            self._device = BaseFeatureDevice(connection=self.connection, host=self)
        return self._device

    def _create_virtualization_object(self) -> None:
        """Decide which object should be created and initialize it."""
        from mfd_hyperv.hypervisor import HypervHypervisor
        from mfd_kvm.hypervisor import KVMHypervisor

        os_name = self.connection.get_os_name()
        os_name_to_class = {
            OSName.LINUX: KVMHypervisor,
            OSName.FREEBSD: KVMHypervisor,
            OSName.WINDOWS: HypervHypervisor,
        }

        if os_name not in os_name_to_class and os_name is not OSName.ESXI:
            raise HostConnectedOSNotSupported(f"Unsupported OS for virtualization feature: {os_name}.")

        # ESXI requires additional module (vsphere-automation-sdk) to be installed manually
        # that's why it is required to be handled separately
        if os_name is OSName.ESXI:
            from mfd_esxi.host import ESXiHypervisor

            self._virtualization = ESXiHypervisor(connection=self.connection)
        else:
            self._virtualization = os_name_to_class.get(os_name)(connection=self.connection)

    @staticmethod
    def _are_interfaces_same(interface: "InterfaceInfo", compared_to: "InterfaceInfo") -> bool:
        """Determine whether both interfaces are same."""
        if interface.interface_type != compared_to.interface_type:
            return False
        return interface.name == compared_to.name and interface.pci_address == compared_to.pci_address

    @staticmethod
    def _add_visited_flag_to_objects(objects: List[object]) -> None:
        """Upodate in-place objects from the list."""
        for item in objects:
            setattr(item, "visited", False)

    @staticmethod
    def _remove_unvisited_interfaces_and_cleanup(interfaces: List["NetworkInterface"]) -> None:
        """Remove unvisited interfaces from the list and remove 'visited' attribute from all interfaces."""
        to_be_removed = []
        for interface in interfaces:
            if not interface.visited:
                to_be_removed.append(interface)

        for interface in to_be_removed:
            interfaces.remove(interface)

        # remove 'visited' tag
        for iface in interfaces:
            if getattr(iface, "visited", False):
                delattr(iface, "visited")

    def _add_interfaces(
        self,
        interfaces: list["NetworkInterface"],
        interfaces_info: list[tuple["InterfaceInfoType", "NetworkInterfaceModel | None"]],
    ) -> None:
        """Add new NetworkInterface objects to provided list."""
        from mfd_network_adapter.network_interface import NetworkInterface

        for info, model in interfaces_info:
            interfaces.append(NetworkInterface(connection=self.connection, interface_info=info, topology=model))

    @staticmethod
    def _update_interfaces(
        interfaces: list["NetworkInterface"],
        interfaces_info: list[tuple["InterfaceInfoType", "NetworkInterfaceModel | None"]],
    ) -> None:
        """Update interfaces with interface info data."""
        for interface in interfaces:
            for compared_to, _ in interfaces_info:
                if Host._are_interfaces_same(interface._interface_info, compared_to):
                    interface.visited = True
                    compared_to.visited = True
                    interface._interface_info = compared_to  # updating only interface info

    def _get_filtered_interface_info_by_topology(
        self, interfaces_info: list["InterfaceInfoType"], ignore_instantiate: bool
    ) -> list[tuple["InterfaceInfoType", "NetworkInterfaceModel"]]:
        """Get InterfaceInfo objects from topology models."""
        from mfd_network_adapter.network_adapter_owner.exceptions import NetworkAdapterIncorrectData

        models_to_instantiate = [
            interface for interface in self.topology.network_interfaces if interface.instantiate or ignore_instantiate
        ]
        filtered_info = []

        for interface_model in models_to_instantiate:
            try:
                if interface_model.interface_index is not None:
                    interface_indexes = [int(interface_model.interface_index)]
                else:
                    interface_indexes = getattr(interface_model, "interface_indexes", None)
                info = self.network._filter_interfaces_info(
                    all_interfaces_info=interfaces_info,
                    pci_address=None
                    if interface_model.pci_address is None
                    else PCIAddress(data=interface_model.pci_address),
                    pci_device=None
                    if interface_model.pci_device is None
                    else PCIDevice(data=interface_model.pci_device),
                    family=interface_model.family,
                    speed=interface_model.speed,
                    interface_indexes=interface_indexes,
                    interface_names=[interface_model.interface_name] if interface_model.interface_name else None,
                    random_interface=None
                    if interface_model.random_interface is None
                    else interface_model.random_interface,
                    all_interfaces=None if interface_model.all_interfaces is None else interface_model.all_interfaces,
                )
                if info:
                    filtered_info.extend([(x, interface_model) for x in info])
                else:
                    raise NetworkAdapterIncorrectData(f"No interfaces found for given data: {interface_model}")

            except Exception as e:
                raise ValueError(
                    f"Error while looking for NetworkInterface with given data: {interface_model}, "
                    f"system: {self.connection.ip}, error: {e}."
                )

        return filtered_info

    def refresh_network_interfaces(
        self, ignore_instantiate: bool = False, extended: Optional[List["InterfaceType"]] = None
    ) -> None:
        """Refresh NetworkInteface objects.

        - Addition:
        For the first time objects are added to the list
        (In case fresh `interface_info` data does not match any of objects of the current `network_interfaces` list).

        - Update:
        In case objects are already added to the list they are updated with the fresh `interface_info` data.
        Check logic of `self._are_interfaces_same()` method used for comparing interfaces.

        - Deletion:
        In case objects from current list do not much any of fresh `interface_info` data they will be deleted
        (meaning they are missing from the system under test).

        Logic in details, there are 2 main cases we should consider:
        1) host model containing network interfaces passed as an argument to Host constructor
          a) ignore_instantiate == False (default):
          - Interfaces that have flag 'instantiate' set in topology will be refreshed
          b) ignore_instantiate == True:
          - All interfaces mentioned in topology model (regardless of 'instantiate' flag value) will be refreshed
          c) extended param in use - List of InterfaceType objects that should be also refreshed
        2) host model without network interfaces passed to Host constructor


        For case 1c) if user expect new interfaces to appear, e.g. VFs,
        then they should call the method with following params:
            `host.refresh_network_interfaces(extended=[InterfaceType.VF])`
            so that will return list of topology interfaces + all VFs captured on the system

        :param ignore_instantiate: flag to determine whether 'instantiate' from interface model is checked or ignored
        :param extended: List of interface types to be included in result, e.g. [InterfaceType.VF]
        :raises NetworkAdapterIncorrectData: in case topology data doesn't much any of the interfaces from the system
        :raises ValueError: if there is problem while creating network interfaces
        """
        logger.log(level=log_levels.MODULE_DEBUG, msg="Preparing NetworkInterfaces.")

        if (self.topology and extended and not self.topology.network_interfaces) or (not self.topology and extended):
            raise NetworkInterfaceRefreshException(
                "Wrong usage of extended parameter - "
                "if there is no topology interfaces then all interfaces "
                "are always collected."
            )
        # gather fresh info about interfaces
        all_interfaces_info = self.network._get_all_interfaces_info()

        # visited flag is used temporarily, it should be deleted from obejcts by the end of method call
        self._add_visited_flag_to_objects(objects=self.network_interfaces + all_interfaces_info)

        # case 2)
        if not self.topology or not self.topology.network_interfaces:
            self._update_interfaces(
                interfaces=self.network_interfaces, interfaces_info=[(x, None) for x in all_interfaces_info]
            )
            self._remove_unvisited_interfaces_and_cleanup(self.network_interfaces)
            self._add_interfaces(
                interfaces=self.network_interfaces,
                interfaces_info=[(info, None) for info in all_interfaces_info if not info.visited],
            )
            return

        # case 1a) & 1b) & 1c)
        filtered_info = self._get_filtered_interface_info_by_topology(
            interfaces_info=all_interfaces_info, ignore_instantiate=ignore_instantiate
        )  # it's a list of tuples of InterfaceInfo and NetworkInterfaceModel objects
        if extended:
            # case 1c)
            extended_info = [(x, None) for x in all_interfaces_info if x.interface_type in extended]
            filtered_info.extend(extended_info)

        self._update_interfaces(interfaces=self.network_interfaces, interfaces_info=filtered_info)
        self._remove_unvisited_interfaces_and_cleanup(self.network_interfaces)
        self._add_interfaces(
            interfaces=self.network_interfaces,
            interfaces_info=[(info, model) for (info, model) in filtered_info if not info.visited],
        )
