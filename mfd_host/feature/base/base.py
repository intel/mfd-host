# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for BaseFeature."""

import typing
import logging
import weakref
from functools import lru_cache
from typing import Any, Dict, Set

from mfd_common_libs import add_logging_level, log_levels
from mfd_typing import OSName

if typing.TYPE_CHECKING:
    from mfd_connect import Connection
    from mfd_host import Host

logger = logging.getLogger(__name__)
add_logging_level(level_name="MODULE_DEBUG", level_value=log_levels.MODULE_DEBUG)


class BaseFeature:
    """Class for BaseFeature."""

    def __new__(cls, *args, **kwargs):
        """Create new feature object."""
        os_name = kwargs["connection"].get_os_name()
        os_name = "esxi" if os_name == OSName.ESXI else os_name.value.lower()

        all_subclasses = _get_all_subclasses(cls)
        requested_class = all_subclasses.get(os_name)

        if requested_class is None:
            return super().__new__(cls)
        return super().__new__(requested_class)

    def __init__(self, connection: "Connection", host: "Host"):
        """
        Initialize BaseFeature.

        :param connection: Object of mfd-connect
        :param host: Host object, parent of feature
        """
        self._connection = connection
        self._host = weakref.ref(host)


@lru_cache()
def _get_all_subclasses(cls: Any) -> Dict[str, Any]:
    os_class_dict = {}
    cls_subclasses = _subclasses(cls)
    for subcls in cls_subclasses:
        module_details = subcls.__module__.split(".")
        if module_details[-1] != "base":
            os_class_dict[module_details[-1]] = subcls
    return os_class_dict


@lru_cache()
def _subclasses(cls: Any) -> Set[Any]:
    return set(c for subcls in cls.__subclasses__() for c in _subclasses(subcls)).union(cls.__subclasses__())
