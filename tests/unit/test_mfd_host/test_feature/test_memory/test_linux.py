# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module to Test Linux Memory."""

import pytest

from mfd_host import Host

from mfd_model.config import HostModel
from mfd_connect import RPyCConnection
from mfd_connect.base import ConnectionCompletedProcess

from mfd_host.feature.memory.exceptions import InsufficientMemoryError, MountDiskDirectoryError, MatchNotFound

from mfd_typing.os_values import OSName


class TestLinuxMemory:
    @pytest.fixture
    def host(self, mocker):
        _connection = mocker.create_autospec(RPyCConnection)
        _connection.get_os_name.return_value = OSName.LINUX
        model = HostModel(role="sut")
        yield Host(connection=_connection, topology=model)
        mocker.stopall()

    def test_create_ram_disk(self, host, mocker):
        mount_disk = "/tmp/ramdisk"
        memory_out = "90595588"
        one_GB = 1024 * 1024
        host.memory._connection.execute_command.return_value.stdout = memory_out
        mocker.patch.object(host.memory, "_mount", autospec=True)
        host.memory._mount.is_mounted.side_effect = [False, True]
        host.memory.create_ram_disk(mount_disk=mount_disk, ram_disk_size=one_GB)
        host.memory._connection.path.assert_called_with(mount_disk)
        host.memory._connection.path.return_value.mkdir.assert_called_once_with(mode=0o777)
        host.memory._mount.mount_tmpfs.assert_called_once_with(
            mount_point="/mnt/tmpfs/", share_path=mount_disk, params=f"-o size={one_GB}"
        )

    def test_create_ram_disk_insufficent_memory(self, host):
        mount_disk = "/tmp/ramdisk"
        one_GB = 1024 * 1024
        host.memory._connection.execute_command.return_value.stdout = str(512 * 1024)
        with pytest.raises(InsufficientMemoryError):
            host.memory.create_ram_disk(mount_disk, one_GB)

    def test_create_ram_disk_mount_unsuccessful(self, host, mocker):
        mount_disk = "/tmp/ramdisk"
        one_GB = 1024 * 1024
        memory_out = "90595588"
        host.memory._connection.execute_command.return_value.stdout = memory_out
        mocker.patch.object(host.memory, "_mount", autospec=True)
        host.memory._mount.is_mounted.return_value = False
        with pytest.raises(MountDiskDirectoryError):
            host.memory.create_ram_disk(mount_disk, one_GB)

    def test_delete_ram_disk(self, host, mocker):
        path = "/mnt/ramdisk"
        mocker.patch.object(host.memory, "_mount", autospec=True)
        host.memory._mount.umount.return_value = True
        host.memory._mount.umount(mount_point=path)
        host.memory._mount.umount.assert_called_once_with(mount_point=path)

    def test_delete_ram_disk_unsuccessful(self, host, mocker):
        path = "/mnt/ramdisk"
        mocker.patch.object(host.memory, "_mount", autospec=True)
        host.memory._mount.umount.return_value = False
        with pytest.raises(MountDiskDirectoryError, match="Cannot Unmount RAM disk directory!"):
            host.memory.delete_ram_disk(path=path)

    def test_set_huge_pages(self, host, mocker):
        command = "echo 2048 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages"
        host.memory._connection.execute_command.return_value = None
        mocker.patch.object(host.memory, "_mount", autospec=True)
        host.memory.set_huge_pages(page_size_in_memory=2048)
        host.memory._connection.execute_command.assert_called_with(command=command, shell=True)
        host.memory._mount.is_mounted.assert_called_with(mount_point="/dev/hugepages")

    def test_set_huge_pages_mount_unsuccessful(self, host, mocker):
        mocker.patch.object(host.memory, "_mount", autospec=True)
        host.memory._mount.is_mounted.return_value = False
        with pytest.raises(MountDiskDirectoryError):
            host.memory.set_huge_pages(page_size_in_memory=2048)

    def test_set_huge_pages_with_numa(self, host, mocker):
        mocker.patch.object(host.memory, "_mount", autospec=True)
        host.memory._connection.execute_command.return_value = None
        host.memory.set_huge_pages(page_size_in_memory=2048, page_size_per_numa_node=(2048, 2))
        assert host.memory._connection.execute_command.call_count == 3
        host.memory._mount.is_mounted.assert_called_with(mount_point="/dev/hugepages")

    def test_get_memory_channels(self, host):
        output = "dmidecode -t memory |grep 'Number Of Devices'"
        expected_out = "Number Of Devices: 32"
        host.memory._connection.execute_command.return_value = ConnectionCompletedProcess(
            args=output, stdout=expected_out, return_code=0
        )
        assert host.memory.get_memory_channels() == 32

    def test_get_memory_channels_not_found(self, host):
        output = "dmidecode -t memory |grep 'Number Of Devices'"
        expected_out = ""
        host.memory._connection.execute_command.return_value = ConnectionCompletedProcess(
            args=output, stdout=expected_out, return_code=0
        )
        with pytest.raises(MatchNotFound, match="Unable to find 'Number of Devices'"):
            host.memory.get_memory_channels()
