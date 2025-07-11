# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for Linux Memory."""

from .base import BaseFeatureMemory
from .exceptions import MountDiskDirectoryError, InsufficientMemoryError, MatchNotFound
import logging
from typing import Optional, Tuple, Union
from mfd_common_libs import log_levels, add_logging_level
from pathlib import Path
import re

add_logging_level("MODULE_DEBUG", level_value=log_levels.MODULE_DEBUG)

logger = logging.getLogger(__name__)


class LinuxMemory(BaseFeatureMemory):
    """Linux class for Memory feature."""

    def _mount_ram_disk(self, mount_disk: Union[Path, str], ram_disk_size: int) -> None:
        """Mount ram disk."""
        tmpfs_location = "/mnt/tmpfs/"
        self._connection.path(mount_disk).mkdir(mode=0o777)
        if not self._mount.is_mounted(mount_point=mount_disk):
            self._mount.mount_tmpfs(
                mount_point=tmpfs_location, share_path=mount_disk, params=f"-o size={ram_disk_size}"
            )
            if not self._mount.is_mounted(mount_point=mount_disk):
                raise MountDiskDirectoryError("Unable to mount RAM disk directory.")

    def _mount_hugetlbs(self, mount_point: Union[Path, str]) -> None:
        """Mount HUGETLBS file system."""
        if not self._connection.path(mount_point).exists():
            self._connection.path(mount_point).mkdir(mode=0o777)
        if not self._mount.is_mounted(mount_point=mount_point):
            self._mount.mount_hugetlbfs(mount_point=mount_point, share_path="nodev")
            if not self._mount.is_mounted(mount_point=mount_point):
                raise MountDiskDirectoryError("Unable to mount Hugetlbfs.")

    def create_ram_disk(self, mount_disk: Union[Path, str], ram_disk_size: int) -> None:
        """
        Create ram disk.

        :param mount_disk: Path / location to mount RAM disk.
        :param ram_disk_size: Size of RAM disk in kB.
        :return: None.
        """
        logger.debug("Checking if memory space is available to create RAM disk.")
        check_memory_command = "grep MemAvailable /proc/meminfo | awk '{print $2}'"

        out = self._connection.execute_command(command=check_memory_command, shell=True)
        memory_out = int(out.stdout)
        if memory_out < ram_disk_size:
            raise InsufficientMemoryError(f"Insufficient memory to create ram disk. {memory_out} < {ram_disk_size}")
        self._mount_ram_disk(mount_disk=mount_disk, ram_disk_size=ram_disk_size)

    def delete_ram_disk(self, path: str) -> None:
        """
        Delete ram disk.

        :param: path: A string to path of file.
        :return: None.
        """
        if not self._mount.umount(mount_point=path):
            raise MountDiskDirectoryError("Cannot Unmount RAM disk directory!")

    def set_huge_pages(
        self,
        page_size_in_memory: int,
        page_size_per_numa_node: Optional[Tuple[int, int]] = None,
        page_size_in_kernel: int = 2048,
    ) -> None:
        """
        Set huge_pages in memory and per numa node.

        :param page_size_in_memory: Size of huge-pages in memory in kB.
        :param page_size_per_numa_node: An optional tuple with huge-pages and numa nodes on system e.g. (2048,2)
        :param page_size_in_kernel: Size of huge-pages in kernel should be 2048kB or 1048576kB.
        :return: None
        """
        mount_point = "/dev/hugepages"
        self._mount_hugetlbs(mount_point=mount_point)
        command = (
            f"echo {page_size_in_memory} > " f"/sys/kernel/mm/hugepages/hugepages-{page_size_in_kernel}kB/nr_hugepages"
        )
        self._connection.execute_command(command=command, shell=True)
        if page_size_per_numa_node:
            for node in range(page_size_per_numa_node[1]):
                command1 = (
                    f"echo {page_size_per_numa_node[0]} >"
                    f" /sys/devices/system/node/node{node}"
                    f"/hugepages/hugepages-{page_size_in_kernel}kB/nr_hugepages"
                )
                self._connection.execute_command(command=command1, shell=True)

    def get_memory_channels(self) -> int:
        """
        Get memory channels from system.

        :returns: String of total memory channels on device.
        """
        mem_channels_cmd = "dmidecode -t memory |grep 'Number Of Devices'"
        output = self._connection.execute_command(mem_channels_cmd, shell=True).stdout
        devices_regex = r"Number\sOf\sDevices\:\s(?P<dev_no>\d+)"
        match = re.match(pattern=devices_regex, string=output)
        if match:
            return int(match.group("dev_no"))
        raise MatchNotFound("Unable to find 'Number of Devices'")
