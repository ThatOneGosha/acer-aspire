sudo := if `id -u` == "0" { "" } else { "sudo" }

deps := \
    "age sops just uv git " + \
    "parted btrfs-progs eudev util-linux"

default:
    @just --list

setup: install-deps enable-hooks
    uv sync
    @echo "Project setup complete!"

install-deps:
    {{sudo}} xbps-install -Sy {{deps}}

enable-hooks:
    git config core.hooksPath .githooks
    @echo "Git hooks enabled from .githooks/"

import-keys device:
    mkdir -p ~/.config/sops/age
    {{sudo}} mkdir -p /mnt/ventoy_storage
    {{sudo}} mount {{device}} /mnt/ventoy_storage
    cp /mnt/ventoy_storage/sops-acer-aspire/age/keys.txt ~/.config/sops/age/keys.txt
    chmod 600 ~/.config/sops/age/keys.txt
    {{sudo}} umount /mnt/ventoy_storage
    @echo "Age keys imported from {{device}}"

# Decrypt, overwrite, encrypt (e.g., just edit secrets/network.yaml)
edit file:
    sops {{file}}
