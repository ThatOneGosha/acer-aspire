from pathlib import Path

import click
import pexpect
from loguru import logger
from plumbum import cmd

from stages import State

MNT = Path("/mnt")
VOID_REPO = "https://repo-default.voidlinux.org/current"
BTRFS_OPTS = "defaults,noatime,compress=zstd"
SUBVOL_MOUNTS = (
    ("@home", "home"),
    ("@projects", "projects"),
    ("@snapshots", ".snapshots"),
)
BASE_PACKAGES = (
    "base-system",
    "btrfs-progs",
    "grub",
    "os-prober",
    "grub-btrfs",
    "python3",
)


@click.group()
def system() -> None:
    pass


def mount_filesystems(part: Path, mnt: Path) -> None:
    cmd.mount("-o", f"{BTRFS_OPTS},subvol=@root", part, mnt)
    logger.info("Mounting remaining Btrfs subvolumes...")
    for subvol, target in SUBVOL_MOUNTS:
        cmd.mount("-o", f"{BTRFS_OPTS},subvol={subvol}", part, mnt / target)


def install_base(mnt: Path) -> None:
    logger.info("Installing base packages...")
    cmd.xbps_install("-S", "-y", "-R", VOID_REPO, "-r", mnt, *BASE_PACKAGES)


def configure_system(mnt: Path) -> None:
    logger.info("Generating /etc/fstab...")
    fstab: str = cmd.xgenfstab("-U", mnt)
    (mnt / "etc/fstab").write_text(fstab)

    logger.info("Configuring system...")
    (mnt / "etc/hostname").write_text("home-pc\n")
    (mnt / "etc/locale.conf").write_text("LANG=en_US.UTF-8\n")
    (mnt / "etc/default/libc-locales").write_text("en_US.UTF-8 UTF-8\n")
    cmd.xchroot(mnt, "ln", "-sf", "/usr/share/zoneinfo/Europe/Moscow",
                "/etc/localtime")


def set_root_password(mnt: Path, password: str) -> None:
    logger.info("Setting root password...")
    child = pexpect.spawn(f"chroot {mnt} passwd root")
    child.expect("New password:")
    child.sendline(password)
    child.expect("Retype new password:")
    child.sendline(password)
    child.expect(pexpect.EOF)


def install_grub(mnt: Path, disk: Path) -> None:
    logger.info("Installing Legacy BIOS GRUB to {}...", disk.resolve())
    cmd.xchroot(mnt, "xbps-install", "-Sy")
    cmd.xchroot(mnt, "xbps-install", "-uy", "xbps")

    # For Legacy BIOS + GPT, point grub-install to the whole disk.
    # GRUB automatically detects partition 1 (bios_grub) and embeds core.img there.
    cmd.xchroot(
        mnt,
        "grub-install",
        "--target=i386-pc",
        "--recheck",
        disk.resolve(),
    )

    grub_default = mnt / "etc/default/grub"
    with grub_default.open("a") as f:
        f.write("GRUB_DISABLE_OS_PROBER=false\n")

    cmd.xchroot(mnt, "grub-mkconfig", "-o", "/boot/grub/grub.cfg")
    cmd.xchroot(mnt, "xbps-reconfigure", "-fa")


@system.command()
@click.pass_obj
def setup(state: State) -> None:
    disk_id: str = state.storage["main_disk"]["id"]
    root_password: str = state.users["passwords"]["root"]

    by_id = Path("/dev/disk/by-id")
    disk = by_id / disk_id
    part2 = by_id / f"{disk_id}-part2"

    if not disk.exists() or not part2.exists():
        logger.error("Target disk or Btrfs partition not found: '{}'.", disk)
        raise SystemExit(1)

    mount_filesystems(part2, MNT)
    install_base(MNT)
    configure_system(MNT)
    set_root_password(MNT, root_password)
    install_grub(MNT, disk)

    logger.success("System bootstrap done!")
