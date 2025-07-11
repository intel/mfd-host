# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for memory exception handling."""


class MemoryException(Exception):
    """Handle generic memory exception."""


class MountDiskDirectoryError(MemoryException):
    """Handle mount disk point errors."""


class ServerMemoryNotFoundError(MemoryException):
    """Exception to handle memory not found errors."""


class InsufficientMemoryError(MemoryException):
    """Exception to handle insufficient memory error."""


class MatchNotFound(MemoryException):
    """Exception to handle device match not found error."""
