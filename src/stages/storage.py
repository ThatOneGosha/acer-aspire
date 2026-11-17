from pathlib import Path

import click
from loguru import logger
from plumbum import cmd

from stages import State

SUBVOLUMES = ("@root", "@home", "@projects", "@snapshots")
MOUNTPOINTS = ("home", "projects", ".snapshots")
MNT = Path("/mnt")


@click.group()
def storage() -> None:
    pass


def confirm_wipe(disk: str) -> None:
    prompt = f"All data on {disk} will be removed. Continue?"
    click.confirm(prompt, default=False, abort=True)


def wipefs(disk: Path) -> None:
    cmd.wipefs("-a", "-f", disk)


def partition_bios_gpt(disk: Path) -> None:
    # yapf: disable
    cmd.parted(
        "-s", disk,
        "mklabel", "gpt",
        "mkpart", "primary", "1MiB", "2MiB",
        "set", "1", "bios_grub", "on",
        "mkpart", "primary", "btrfs", "2MiB", "100%",
    )
    # yapf: enable


def sync_partitions(disk: Path) -> None:
    cmd.partprobe(disk)
    cmd.udevadm("settle")


def create_subvolumes(part: Path, mnt: Path) -> None:
    cmd.mount(part, mnt)
    try:
        for subvol in SUBVOLUMES:
            logger.info("Creating subvolume {}...", subvol)
            cmd.btrfs("subvolume", "create", mnt / subvol)
    finally:
        cmd.umount(mnt)


def bootstrap_root(part: Path, mnt: Path) -> None:
    cmd.mount("-o", "defaults,subvol=@root", part, mnt)
    try:
        logger.info("Creating mountpoints...")
        for name in MOUNTPOINTS:
            (mnt / name).mkdir(parents=True, exist_ok=True)

        logger.info("Synchronizing xbps keys...")
        xbps_db = mnt / "var/db/xbps"
        xbps_db.mkdir(parents=True, exist_ok=True)
        cmd.cp("-R", "/var/db/xbps/keys", xbps_db)
    finally:
        cmd.umount(mnt)


@storage.command()
@click.option("--yes", is_flag=True)
@click.pass_obj
def setup(state: State, yes: bool) -> None:
    disk_id: str = state.storage["main_disk"]["id"]
    by_id = Path("/dev/disk/by-id")
    disk = by_id / disk_id
    part2 = by_id / f"{disk_id}-part2"

    if not disk.exists():
        logger.error("Disk not found: '{}'.", disk)
        raise SystemExit(1)

    logger.success("Resolved disk: '{}'.", disk.resolve())

    if not yes:
        confirm_wipe(disk_id)

    wipefs(disk)

    logger.info("Creating GPT partition table...")
    partition_bios_gpt(disk)
    sync_partitions(disk)

    logger.info("Formatting {} as Btrfs...", part2.name)
    cmd.mkfs_btrfs("-f", part2)

    create_subvolumes(part2, MNT)
    bootstrap_root(part2, MNT)

    logger.success("Storage partitioned, formatted, and subvolumes created.")
