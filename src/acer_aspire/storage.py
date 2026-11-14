from pathlib import Path
import re

import click
from loguru import logger
from plumbum import FG
from plumbum.cmd import lsblk

from acer_aspire import State


def mask_disk_id(disk_id: str) -> str:
    """Mask the hardware serial number in a /dev/disk/by-id/ identifier."""
    match = re.match(r"^(.+_)([^_]+?)(-part\d+)?$", disk_id)
    if not match:
        return disk_id

    prefix, serial, part = match.groups()
    return f"{prefix}{'*' * len(serial)}{part or ''}"


@click.group()
def storage() -> None:
    pass


@storage.command()
@click.pass_obj
def check(state: State) -> None:
    disk_id = state.storage["storage"]["disk_id"]
    masked_id = mask_disk_id(disk_id)
    disk = Path(f"/dev/disk/by-id/{disk_id}")

    if not disk.exists():
        logger.error("Disk not found: /dev/disk/by-id/{}", masked_id)
        raise SystemExit(1)

    logger.success("Resolved {} -> {}", masked_id, disk.resolve())
    lsblk["-o", "NAME,MODEL,SIZE,TYPE,FSTYPE", str(disk)] & FG
