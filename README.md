> [!IMPORTANT] 
> This project is under development. All source code and features on the main branch are for the purpose of testing or evaluation and not production ready.

# MFD Host

MFD Host provides a unified Python interface for managing and interacting with Systems Under Tests (SUTs) AKA Hosts and their capabilities across multiple operating systems.
It consists of multiple features like `network`, `driver`, `cpu`, `memory`, etc.

```mermaid
classDiagram
class Host{
    +str: name
    +Connection: connection
    +List[NetworkInterface]: network_interfaces
    +CliClient: cli_client
    +Connections: connections
    +PowerManagement: power_mng
    +TopologyModel: topology
    --- Features ---
    +NetworkAdapterOwner: network
    +PackageManager: driver
    +refresh_network_interfaces()
}

Host *-- NetworkAdapterOwner
Host *-- PackageManager
```

> [!IMPORTANT]
> ESXi Users ONLY\
> This module requires `vsphere-automation-sdk` to work.\
> Please add `vsphere-automation-sdk` to your requirements file or install it manually:
> ```bash
> pip install vsphere-automation-sdk @ git+https://github.com/vmware/vsphere-automation-sdk-python@v8.0.3.0
> ```
> For currently supported version of `vsphere-automation-sdk` please refer to [mfd-esxi/README](https://github.com/intel/mfd-esxi).

## Usage

### How to instantiate Host? 

```python
from mfd_connect.util.connection_utils import Connections
from pytest_mfd_config.fixtures import create_host_connections_from_model, create_power_mng_from_model

_connections = create_host_connections_from_model(host_model)
connections = Connections(_connections)

power_mng = create_power_mng_from_model(host_model.power_mng) if host_model.power_mng else None
host = Host(
    connection=_connections[0],
    name=host_model.name,
    cli_client=cli_client,
    connections=connections,
    power_mng=power_mng,
    topology=host_model,
)
```
### How to use host object? 

```python
from mfd_typing.network_interface import InterfaceType
(...)
host.refresh_network_interfaces()  # to refresh host interfaces
(...)
host.refresh_network_interfaces(ignore_instantiate=True)  # to refresh all interfaces (including ones with 'instantiate' set to False)
(...)
host.network.vlan.create_vlan(vlan_id=100, interface_name="foo", vlan_name="foo_100") # to create VLAN interface
host.refresh_network_interfaces(extended=[InterfaceType.VLAN])  # to append foo_100 interface to list of network_interfaces
```

### Host Methods (API):

- `refresh_network_interfaces(ignore_instantiate: bool = False, extend: List[InterfaceType]] = None) -> None` : Update list of `NetworkInterface` objects stored in `self.network_interfaces` attribute. Method's behavior varies based on used flags or passed topology data:

>:information_source: Once interfaces are added to the list they will be always updated, not being recreated, e.g. `id(interface_1)` shall point to same address in memory before and after method call.

Logic in details, there are 2 main cases we should consider:
1) host model containing network interfaces passed as an argument to Host constructor
    * a) ignore_instantiate == False (default): Interfaces that have flag 'instantiate' set in topology will be refreshed
    * b) ignore_instantiate == True: All interfaces mentioned in topology model (regardless of 'instantiate' flag value) will be refreshed
    * c) extended param in use: List of InterfaceType objects that should be also refreshed
2) host model without network interfaces passed to Host constructor
 
>For case 1c) if user expect new interfaces to appear, e.g. VFs, then they should call the method with following params:
`host.refresh_network_interfaces(extended=[InterfaceType.VF])`
so that will return list of topology interfaces + all VFs captured on the system

For more examples please check [interface_refresh_examples.py](/examples/interface_refresh_examples.py)

## Available features

### - Network

It's a pass-through to the `mfd-network-adapter`'s owner object, which let you use its methods and features by `network` attribute.

[Available API](https://github.com/intel/mfd-network-adapter)

Example:
```python
host.network.get_interfaces(all_interfaces=True)
host.network.vxlan.delete_vxlan(vxlan_name="vxlan")
host.network.vlan.remove_all_vlans()
```

### - Driver

It's a pass-through to the `mfd-package-manager`'s object, which let you use its methods and features by `driver` attribute.

[Available API](https://github.com/intel/mfd-package-manager)

Example:
```python
host.driver.uninstall_module(module_name="module_name")
```

### - Event
For FreeBSD, Linux and ESXi hosts it's a pass-through to the `mfd-dmesg`'s object.

For Windows host it's a pass-through to the `mfd-event-log`'s object. 
> [!CAUTION]
> Event feature for Windows supports only RPyCConnection

Methods and features are accessible by `event` attribute.

### - Virtualization

It's a pass-through to the one of [`HypervHypervisor` (`mfd-hyperv`), `KVMHypervisor` (`mfd-kvm`), `ESXiHypervisor` (`mfd-esxi`)] objects, which let you use its methods and features by `virtualization` attribute.

Auto-selection is based on OS:
```python
os_name_to_class = {
    OSName.LINUX: KVMHypervisor,
    OSName.FREEBSD: KVMHypervisor,
    OSName.WINDOWS: HypervHypervisor,
    OSName.ESXI: ESXiHypervisor,
}
```

[KVM Available API](https://github.com/intel/mfd-kvm)

[ESXI Available API](https://github.com/intel/mfd-esxi)

[HyperV Available API](https://github.com/intel/mfd-hyperv)

Example:
```python
# HyperV
host.virtualization.create_vm(...)

# ESXI
host.virtualization.add_vswitch(...)

# KVM
host.virtualization.attach_vm(...)
```

### Utils:

All OSes:
* get_interface_by_ip(ip: IPv4Address | IPv6Address, check_all_interfaces: bool = False) -> "ESXiNetworkInterface | FreeBSDNetworkInterface | LinuxNetworkInterface | WindowsNetworkInterface" - Get interface with matching IP address.
* get_hostname() -> str - Get hostname.

Linux:
* remove_ssh_known_host(host_ip: Union["IPv4Interface", "IPv6Interface"], ssh_client_config_dir: str) - Removes specific host IP from known host configuration
* start_kedr(driver_name: str) -> None - attach KEDR module to the driver 
* stop_kedr() -> None - stop KEDR process
* create_unprivileged_user(username: str, password: str) -> None - create unprivileged user
* delete_unprivileged_user(username: str) -> None - delete unprivileged user
* set_icmp_echo(*, ignore_all: bool = False, ignore_broadcasts: bool = True) -> None - Set ICMP broadcast.

FreeBSD:
* set_icmp_echo(*, ignore_broadcasts: bool = True, **kwargs) -> None - Set ICMP broadcast.

### Memory:

Linux:
* create_ram_disk(mount_disk: Union[Path, str], ram_disk_size: int) - Create a RAM disk.
* delete_ram_disk(path: str) - Delete RAM disk.
* set_huge_pages(page_size_in_memory: int,page_size_per_numa_node: Optional[Tuple[int, int]] = None, page_size_in_kernel: int = 2048) - Set Hugepages in Memory and on Numa Node
* get_memory_channels() - Gets the number of memory channels on system.

### Stats:

Linux:

* get_meminfo() -> Dict[str, str] - Get information about memory in system.
* get_cpu_utilization() -> Dict[str, Dict[str, str]] - Get sar CPU utilization values for all cores. Output data is in percentages which sums up to 1 for each core.
* get_slabinfo() -> Dict[str, str] - Capture slabinfo results.
* get_mem_used() -> int: - Get total memory used.
* get_top_stats(
        self,
        separate_cpu: Optional[bool] = True,
        memory_scaling: Optional[str] = "",
        options: Optional[str] = "",
        friendly_labels: Optional[bool] = True,
        filter_proc: Optional[List[str]] = [],
    ) -> StatsOutput - Get the top values and build a text output from the values themselves.

FreeBSD:
* get_free_memory() -> int - Get free memory (in MBytes).
* get_wired_memory() -> int - Get wired (non-pageable) memory (in MBytes).
* get_cpu_utilization() -> Dict[str, Dict[str, str]] - Get CPU utilization. Utilization calucated based on the time spent by the cores in different states since the last function call.

Windows:
* get_meminfo() -> Dict[str, int] - Get information about memory in system.
* get_cpu_utilization() -> float - Get the CPU utilization value.
* get_dpc_rate(interval: int, samples: int) -> Dict[str, int] - Get DPC Rate values from performance monitor.

ESXi:
* get_meminfo() -> Dict[str, int] - Get information about memory in system.

Example
```python
from mfd_host.base import Host
from mfd_host import Host
from mfd_connect import RPyCConnection
host = Host(connection=RPyCConnection)

path = "/tmp/ramdisk"
size = 1024 * 1024 # 1 gigabyte
hp_numa = (2048, 2)
host.memory.create_ram_disk(mount_disk=path, ram_disk_size=size)
host.memory.delete_ram_disk(path=path)
host.memory.set_huge_pages(page_size_in_memory=2048, page_size_per_numa_node=hp_numa)
host.memory.get_memory_channels()
```

ESXi:
* ram() - Returns total bytes of RAM on system.

Example
```python
from mfd_host import Host
from mfd_connect import RPyCConnection
host = Host(connection=RPyCConnection)

esxi_host = Host(connection=RPyCConnection)

esxi_host.memory.ram
```

### CPU:

Windows:
* get_core_info(self) -> List[Dict[str, str]] - Get device id, number of cores and number of logical processors.
* get_hyperthreading_state(self) -> State - Check if hyperthreading enabled.
* get_phy_cpu_no(self) -> int - Get the number of physical cpus.
* get_numa_node_count(self) -> int - Get NUMA node count.
* get_log_cpu_no(self) -> int - Get the number of logical CPUs.
* set_groupsize(self, maxsize: int) -> None - Set maximum processor group size.

ESXi:
* packages(self) -> int - To fetch the number of numa nodes.
* cores(self) -> int - To fetch the number of cores.
* threads(self) -> int - To fetch the number of threads.
* set_numa_affinity(self, numa_state: State) -> None - Set the advanced OS setting LocalityWeightActionAffinity.

FreeBSD:
* get_log_cpu_no(self) -> int - Get the number of logical CPUs.

Linux:
* display_cpu_stats_only(self) -> str - Display the cpu stats only.
* get_cpu_stats(self) -> Dict[str, Dict[str, str]] - Get CPU stats.
* get_log_cpu_no(self) -> int - Get the number of logical CPUs.
* affinitize_queues_to_cpus(self, adapter: str, scriptdir: str) -> None - Execute set_irq_affinity script on given adapter.

### Service:
Feature for handling system service operations.

Linux:
* restart_service(name: str): Restart a system service by name.
* restart_libvirtd(): Restart the libvirtd service specifically.
* stop_irqbalance(): Stop/kill the irqbalance service if running.
* start_irqbalance(): Start the irqbalance service.
* is_service_running(name: str): Check if a service is running and active. Returns boolean.
* is_network_manager_running(): Check status of NetworkManager service specifically.
* set_network_manager(*, enable: bool): Enable or disable NetworkManager service.

ESXi:
* restart_service(name: str): Restart a system service by name.

### Device:

Windows:
* find_devices(device_id: str, pattern: str): Find devices that are currently attached to the computer.
* uninstall_devices(device_id: str, pattern: str, reboot: bool): Remove the device from the device tree and deletes the device stack for the device.
* get_description_for_code(error_code: int): Fetch error description for a particular error code.
* restart_devices(device_id: str, pattern: str, reboot: bool): Stop and restart the specified devices.
* get_device_status(device_index: int): Get device status using the device index.
* get_resources(device_id: str, pattern: str, resource_filter: str): Get the resources allocated to the specified devices.
* verify_device_state(device: "WindowsNetworkInterface", state: State): Check if a device is in specified state and if resources are available as expected.
* enable_devices(device_id: str, pattern: str, reboot: bool): Enable devices on the computer.
* disable_devices(device_id: str, pattern: str, reboot: bool): Disable devices on the computer.
* set_state_for_multiple_devices(device_list: list["WindowsNetworkInterface"], state: State): Enable/Disable multiple devices specified through a list of dictionaries.

## OS supported:

Here is a place to write what OSes support your MFD module:
* LNX
* WINDOWS
* FREEBSD
* ESXI

## Issue reporting

If you encounter any bugs or have suggestions for improvements, you're welcome to contribute directly or open an issue [here](https://github.com/intel/mfd-host/issues).
