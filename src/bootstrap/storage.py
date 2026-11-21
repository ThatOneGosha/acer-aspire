"""
def partition_bios_gpt(disk: Path) -> None:
    args = (
        ("mklabel", "gpt")
        + ("mkpart", "bios", "1MiB", "2MiB")
        + ("set", "1", "bios_grub", "on")
        + ("mkpart", "root", "btrfs", "2MiB", "100%")
    )
    cmd.parted("-s", disk, *args)
"""


def setup_storage(cfg: dict, yes: bool = False) -> None:
    print("Hello from setup_storage")
