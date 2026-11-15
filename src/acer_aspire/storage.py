from loguru import logger
from acer_aspire import State
from plumbum import cmd
from pathlib import Path

import click

@click.group()
def storage() -> None:
    pass

@storage.command()
@click.option("--yes", is_flag=True)
@click.pass_obj
def setup(state: State, yes: bool) -> None:
    disk_id = state.storage["storage"]["disk_id"]
    disk = Path(f"/dev/disk/by-id/{disk_id}")
    
    if not disk.exists():
        logger.error("Disk not found: {}", disk.resolve())
        raise SystemExit(1)
    
    logger.success("Resolved disk: {}", disk.resolve())

    if not yes:
        prompt = f"All data on {disk_id} will be removed. Continue?"
        click.confirm(prompt, default=False, abort=True)
        
    logger.info("Wiping existing signatures on {}...", disk_id)
    cmd.wipefs["-a", "-f", str(disk)]()

    logger.info("Creating GPT partition table...")
    cmd.parted[
        "-s", str(disk),
        "mklabel", "gpt",
        "mkpart", "primary", "1MiB", "2MiB",
        "set", "1", "bios_grub", "on",
        "mkpart", "primary", "btrfs", "2MiB", "100%",
    ]()

    cmd.partprobe[str(disk)]()
    cmd.udevadm["settle"]()

    part2 = Path(f"/dev/disk/by-id/{disk_id}-part2")
    logger.info("Formatting {} as Btrfs...", part2.name)
    cmd.mkfs_btrfs["-f", str(part2)]()
    
    cmd.mount[str(part2), "/mnt"]()
    try:
        for subvol in ["@root", "@home", "@projects", "@snapshots"]:
            logger.info("Creating subvolume {}...", subvol)
            cmd.btrfs["subvolume", "create", f"/mnt/{subvol}"]()
    finally:
        cmd.umount["/mnt"]()

    logger.success("Storage partitioned, formatted, and subvolumes created")
