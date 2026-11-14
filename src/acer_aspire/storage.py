from acer_aspire import State
from loguru import logger
import click

@click.group()
def storage() -> None:
    pass

@storage.command()
@click.pass_obj
def check(state: State) -> None:
    disk_id = state.storage["storage"]["disk_id"]
    disk = Path(f"/dev/disk/by-id/{disk_id}")

    if not disk.exists():
        logger.error("Disk not found: {}", disk)
        raise SystemExit(1)

    logger.success("Resolved {} -> {}", disk_id, disk.resolve())
    lsblk["-o", "NAME,MODEL,SIZE,TYPE,FSTYPE", str(disk)] & FG
