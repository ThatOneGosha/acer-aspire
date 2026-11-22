from collections.abc import Sequence
from pathlib import Path

import click
from plumbum import cmd


def partition_disk(disk: Path) -> None:
    layout = """
    label: gpt
    name=bios, size=1MiB, type=bios
    name=root, type=linux
    """
    (cmd.sfdisk["-w", "always", "-W", "always", str(disk)] << layout).run()
    cmd.partprobe(str(disk))
    cmd.udevadm("settle")


# Disk mount required!
def create_subvolumes(mount: Path, subvols: Sequence[str]) -> None:
    cmd.btrfs("subvolume", "create", *[str(mount / subvol) for subvol in subvols])

# Disk mount required!
def create_mountpoints(mount: Path, mountpoints: Sequence[str]) -> None:
    for mountpoint in mountpoints:
        (mount / mountpoint).mkdir(parents=True, exist_ok=True)


def setup_storage(storage: dict, yes: bool = False) -> None:
    disk = Path("/dev/disk/by-id") / storage["id"]

    if not yes:
        prompt = f"Partition disk {disk}? All data will be lost."
        click.confirm(prompt, abort=True)

    click.echo(f"Partitioning storage {disk}...")
    partition_disk(disk)
