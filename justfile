default:
    @just --list

setup: install-deps hooks sync
    @echo "Project setup complete!"

install-deps:
    xbps-install -Sy age sops just uv

hooks:
    git config core.hooksPath .githooks
    @echo "Git hooks enabled from .githooks/"

sync:
    uv sync

check-secrets:
    uvx --python 3.10 --from ensure-sops ensure_sops secrets/*

# Decrypt, overwrite, encrypt (e.g., just edit secrets/network.yaml)
edit file:
    sops {{file}}
