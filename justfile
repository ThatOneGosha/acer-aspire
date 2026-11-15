deps := \
    "age sops just uv git " + \
    "parted btrfs-progs eudev util-linux"

default:
    @just --list

setup: auth install-deps hooks uv-sync
    @echo "Project setup complete!"

auth:
    @[ "$(id -u)" -eq 0 ] || (echo "Root privileges required." && exit 1)

install-deps: auth
    xbps-install -Sy {{deps}}

hooks:
    git config core.hooksPath .githooks
    @echo "Git hooks enabled from .githooks/"

uv-sync:
    uv sync

# Decrypt, overwrite, encrypt (e.g., just edit secrets/network.yaml)
edit file:
    sops {{file}}
