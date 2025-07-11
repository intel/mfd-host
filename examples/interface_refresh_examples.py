# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Host Network Interface Refresh Examples."""
import logging
from ipaddress import IPv4Interface

from mfd_typing.network_interface import InterfaceType

from mfd_host import Host
from mfd_connect import RPyCConnection


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


HOST_IP = "<<PUT_YOUR_HOST_IP_HERE>>"
NAMESPACE_NAME = "foo"
SECOND_NAMESPACE_NAME = "bar"
connection = RPyCConnection(HOST_IP)
host = Host(connection=connection)


# Refresh interfaces
host.refresh_network_interfaces()

# Pick first PF interface with name starting with 'eth' from Host list
first_pf = [
    iface
    for iface in host.network_interfaces
    if iface.interface_type == InterfaceType.PF and iface.name.startswith("eth")
][0]
logger.info("Picked first interface")

firs_pf_id = id(first_pf)  # get memory address

# Make sure it is not assigned to Namespace
assert first_pf.namespace is None, f"Selected interface '{first_pf.name}' has already assigned namespace!"
logger.info(f"Ensured tested interface - {first_pf.name} is not assigned to any namespaces")

# Make sure namespace doesn't exist
assert (
    NAMESPACE_NAME
    not in host.network._get_network_namespaces()
), f"Namespace {NAMESPACE_NAME} already exists on host {HOST_IP}"
logger.info(f"Ensured that namespace '{NAMESPACE_NAME}' does not exist.")

logger.info(f"Creating namespace '{NAMESPACE_NAME}")
# Create Namespace
host.network.ip.create_namespace(namespace_name=NAMESPACE_NAME)


logger.info(f"Moving interface '{first_pf.name}' to namespace '{NAMESPACE_NAME}")

# Move Interface X into namespace A (requires refreshing)
host.network.ip.add_to_namespace(namespace_name=NAMESPACE_NAME, interface_name=first_pf.name)


logger.info(f"Refreshing interfaces ..")

# Refresh after moving to namespace
host.refresh_network_interfaces()

first_pf_id_after_refresh = id(first_pf)  # get memory address after refresh

# Make sure object has not changed
assert firs_pf_id == first_pf_id_after_refresh, "First PF object has changed after refresh!"
logger.info(f"Ensured {first_pf} object reference hasn't changed after refresh")

# Make sure it is now assigned to namespace
assert first_pf.namespace == NAMESPACE_NAME
logger.info(f"Ensured {first_pf.name} is assigned to namespace '{NAMESPACE_NAME}'")

# Assign IP to the interface within namespace

ip_address = IPv4Interface("1.2.1.2")
logger.info(f"Adding {ip_address} ip address to {first_pf.name}")

first_pf.ip.add_ip(ip=ip_address)


# Make sure address is added
assert ip_address in first_pf.ip.get_ips().v4  # get_ips() returns IPs object, v4 attribute is a list of IPv4 addresses
logger.info(f"Ensured {first_pf.name} has properly added ip {ip_address}")


# Move interface from namespace A into namespace B
logger.info(f"Moving {first_pf.name} from namespace {NAMESPACE_NAME} to {SECOND_NAMESPACE_NAME}")
host.network.ip.create_namespace(namespace_name=SECOND_NAMESPACE_NAME)
host.network.ip.add_to_namespace(
    namespace_name=SECOND_NAMESPACE_NAME, interface_name=first_pf.name, namespace=NAMESPACE_NAME
)

# Refresh after moving to namespace
host.refresh_network_interfaces()
logger.info(f"Refreshing interfaces ..")

first_pf_id_after_2nd_refresh = id(first_pf)  # get memory address after refresh

# Make sure object has not changed
assert firs_pf_id == first_pf_id_after_2nd_refresh, "First PF object has changed after refresh!"
logger.info(f"Ensured {first_pf} object reference hasn't changed after refresh")

# Make sure it is now assigned to SECOND_NAMESPACE
assert first_pf.namespace == SECOND_NAMESPACE_NAME
logger.info(f"Ensured {first_pf.name} is assigned to namespace '{SECOND_NAMESPACE_NAME}'")
