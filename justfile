deps := \
    "age sops just uv git " + \
    "parted btrfs-progs eudev util-linux"

default:
    @just --list

auth:
    @[ "$(id -u)" -eq 0 ] || (echo "Root privileges required." && exit 1)

setup: auth install-deps hooks uv-sync
    @echo "Project setup complete!"

install-deps: auth
    xbps-install -Sy {{deps}}

hooks:
    git config core.hooksPath .githooks
    @echo "Git hooks enabled from .githooks/"

uv-sync:
    uv sync

import-keys device: auth
    mkdir -p ~/.config/sops/age /mnt/ventoy_storage
    mount {{device}} /mnt/ventoy_storage
    cp /mnt/ventoy_storage/sops-acer-aspire/age/keys.txt ~/.config/sops/age/keys.txt
    chmod 600 ~/.config/sops/age/keys.txt
    umount /mnt/ventoy_storage
    @echo "Age keys imported from {{device}}"


# Decrypt, overwrite, encrypt (e.g., just edit secrets/network.yaml)
edit file:
    sops {{file}}
