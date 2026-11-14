from loguru import logger
from acer_aspire import State

from pathlib import Path

import click

from plumbum import FG
from plumbum.cmd import lsblk


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
        alert = f"All data on {disk_id} will be removed. Continue?"
        click.confirm(alert, default=False, abort=True)
    
    if not disk.exists():
        logger.error("Disk not found: {}", disk.resolve())
        raise SystemExit(1)

    logger.success("Resolved disk: {}", disk.resolve())
    lsblk["-o", "NAME,MODEL,SIZE,TYPE,FSTYPE", str(disk)] & FG
