sudo := if `id -u` == "0" { "" } else { "sudo" }

default:
    @just --list

setup: install-deps hooks uv-sync
    @echo "Project setup complete!"

install-deps:
    {{sudo}} xbps-install -Sy age sops just uv git parted btrfs-progs eudev util-linux

hooks:
    git config core.hooksPath .githooks
    @echo "Git hooks enabled from .githooks/"

uv-sync:
    uv sync

# Decrypt, overwrite, encrypt (e.g., just edit secrets/network.yaml)
edit file:
    sops {{file}}
