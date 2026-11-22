from pathlib import Path

import click
from plumbum import cmd


def partition_disk(disk: Path) -> None:
    layout = """
    label: gpt
    name=bios, size=1MiB, type=bios
    name=root, type=linux
    """
    cmd.sfdisk["-w", "always", "-W", "always", str(disk)].run(stdin=layout)


def setup_storage(storage: dict, yes: bool = False) -> None:
    disk = Path("/dev/disk/by-id") / storage["id"]

    if not yes:
        click.confirm(f"Partition disk {disk}? All data will be lost.", abort=True)

    click.echo(f"Partitioning storage {disk}...")
    partition_disk(disk)
