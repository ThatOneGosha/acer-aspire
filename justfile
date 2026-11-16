sudo := if `id -u` == "0" { "" } else { "sudo" }

mountpoint := "/mnt/ventoy_storage"
default_keys := "sops-acer-aspire/age/keys.txt"

deps := \
    "age sops just uv git " + \
    "parted btrfs-progs eudev util-linux"

default:
    @just --list

init: install-deps enable-hooks
    uv sync
    @echo "Project init complete."

install-deps:
    {{sudo}} xbps-install -Sy {{deps}}
    @echo "Dependencies installed."

enable-hooks:
    git config core.hooksPath .githooks
    @echo "Git hooks enabled from '.githooks/'."

import-keys device keys=(mountpoint / default_keys):
    #!/usr/bin/env sh
    set -eu
    mkdir -p ~/.config/sops/age
    {{sudo}} mkdir -p "{{mountpoint}}"
    {{sudo}} mount "{{device}}" "{{mountpoint}}"
    trap '{{sudo}} umount "{{mountpoint}}"' EXIT
    cp "{{keys}}" ~/.config/sops/age/keys.txt
    chmod 600 ~/.config/sops/age/keys.txt
    echo "Age keys imported from '{{device}}'."
