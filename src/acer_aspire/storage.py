from loguru import logger
from acer_aspire import State

from pathlib import Path

import click

from plumbum.cmd import mkfs_btrfs, parted, partprobe, udevadm, wipefs

@click.group()
def storage() -> None:
    pass

@storage.command()
@click.option("--yes", is_flag=True)
@click.pass_obj
def setup(state: State, yes: bool) -> None:
    disk_id = state.storage["storage"]["disk_id"]
    disk = Path(f"/dev/disk/by-id/{disk_id}")

    if not yes:
        prompt = f"All data on {disk_id} will be removed. Continue?"
        click.confirm(prompt, default=False, abort=True)
    
    if not disk.exists():
        logger.error("Disk not found: {}", disk.resolve())
        raise SystemExit(1)

    logger.success("Resolved disk: {}", disk.resolve())

    wipefs["-a", "-f", str(disk)]()

    parted[
        "-s", str(disk),
        "mklabel", "gpt",
        "mkpart", "primary", "1MiB", "2MiB",
        "set", "1", "bios_grub", "on",
        "mkpart", "primary", "btrfs", "2MiB", "100%",
    ]()

    partprobe[str(disk)]()
    udevadm["settle"]()

    part2 = Path(f"/dev/disk/by-id/{disk_id}-part2")
    mkfs_btrfs["-f", str(part2)]()
