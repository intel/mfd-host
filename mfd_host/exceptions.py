# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for MFD Host related exceptions."""

import subprocess


class HostModuleException(Exception):
    """Handle module exception."""


class HostConnectedOSNotSupported(HostModuleException):
    """Handle unsupported OS."""


class HostConnectionTypeNotSupported(HostModuleException):
    """Handle unsupported connection type."""


class VLANFeatureException(HostModuleException):
    """Handle VLAN feature exceptions."""


class VxLANFeatureException(HostModuleException):
    """Handle VxLAN feature exceptions."""


class NetworkInterfaceRefreshException(HostModuleException):
    """Handle NetworkInterface refresh action errors."""


class StatisticNotFoundException(HostModuleException):
    """Handle not found statistic."""


class CPUFeatureExecutionError(HostModuleException, subprocess.CalledProcessError):
    """Handle CPU Feature Execution Errors."""


class CPUFeatureException(HostModuleException):
    """Handle CPU Feature exceptions."""


class ServiceFeatureException(HostModuleException):
    """Handle service feature exceptions."""


class DeviceFeatureException(HostModuleException):
    """Handle Device feature exceptions."""


class UtilsFeatureException(HostModuleException):
    """Handle Utils feature exceptions."""


class UtilsFeatureExecutionError(HostModuleException, subprocess.CalledProcessError):
    """Handle Utils feature Execution errors."""
