from pathlib import Path

import click
import pexpect
from loguru import logger
from plumbum import cmd

from stages import State


@click.group()
def system() -> None:
    pass


@system.command()
@click.pass_obj
def setup(state: State) -> None:
    mnt = Path("/mnt")
    disk_id = state.storage["storage"]["disk_id"]
    disk = Path(f"/dev/disk/by-id/{disk_id}")
    part2 = Path(f"/dev/disk/by-id/{disk_id}-part2")

    # Adjust key path if root_password lives elsewhere in State
    root_password = '123'

    if not disk.exists() or not part2.exists():
        logger.error("Target disk or Btrfs partition not found: '{}'.", disk)
        raise SystemExit(1)

    logger.info("Mounting remaining Btrfs subvolumes...")
    btrfs_opts = "defaults,noatime,compress=zstd"
    for subvol, target in [
        ("@home", mnt / "home"),
        ("@projects", mnt / "projects"),
        ("@snapshots", mnt / ".snapshots"),
    ]:
        cmd.mount("-o", f"{btrfs_opts},subvol={subvol}", str(part2),
                  str(target))

    logger.info("Installing base packages...")
    repo = "https://repo-default.voidlinux.org/current"
    packages = [
        "base-system",
        "btrfs-progs",
        "grub",
        "os-prober",
        "grub-btrfs",
        "python3",
    ]
    cmd.xbps_install("-S", "-y", "-R", repo, "-r", str(mnt), *packages)

    logger.info("Generating /etc/fstab...")
    fstab = cmd.xgenfstab("-U", str(mnt))
    (mnt / "etc/fstab").write_text(fstab)

    logger.info("Configuring system...")
    (mnt / "etc/hostname").write_text("home-pc\n")
    (mnt / "etc/locale.conf").write_text("LANG=en_US.UTF-8\n")
    (mnt / "etc/default/libc-locales").write_text("en_US.UTF-8 UTF-8\n")
    cmd.xchroot(str(mnt), "ln", "-sf", "/usr/share/zoneinfo/Europe/Moscow",
                "/etc/localtime")

    logger.info("Setting root password...")
    child = pexpect.spawn(f"chroot {mnt} passwd root")
    child.expect("New password:")
    child.sendline(root_password)
    child.expect("Retype new password:")
    child.sendline(root_password)
    child.expect(pexpect.EOF)

    logger.info("Installing Legacy BIOS GRUB to {}...", disk.resolve())
    cmd.xchroot(str(mnt), "xbps-install", "-Sy")
    cmd.xchroot(str(mnt), "xbps-install", "-uy", "xbps")

    # For Legacy BIOS + GPT, point grub-install to the whole disk.
    # GRUB automatically detects partition 1 (bios_grub) and embeds core.img there.
    cmd.xchroot(
        str(mnt),
        "grub-install",
        "--target=i386-pc",
        "--recheck",
        str(disk.resolve()),
    )

    grub_default = mnt / "etc/default/grub"
    with grub_default.open("a") as f:
        f.write("GRUB_DISABLE_OS_PROBER=false\n")

    cmd.xchroot(str(mnt), "grub-mkconfig", "-o", "/boot/grub/grub.cfg")
    cmd.xchroot(str(mnt), "xbps-reconfigure", "-fa")

    logger.success("System bootstrap done!")
