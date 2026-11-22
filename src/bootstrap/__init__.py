import json
from dataclasses import dataclass
from functools import cached_property

import click
from plumbum import cmd

from bootstrap.storage import setup_storage


class Vault:
    @staticmethod
    def _decrypt(name: str) -> dict:
        raw = cmd.sops("-d", "--output-type", "json", f"secrets/{name}")
        return json.loads(raw)

    @cached_property
    def storage(self) -> dict:
        return self._decrypt("storage.yaml")


@dataclass(frozen=True)
class AppState:
    vault: Vault
    yes: bool = False


@click.group(invoke_without_command=True)
@click.option("--yes", is_flag=True)
@click.pass_context
def cli(ctx: click.Context, yes: bool) -> None:
    ctx.obj = AppState(vault=Vault(), yes=yes)
    if ctx.invoked_subcommand is None:
        click.echo("Starting full bootstrap...")
        setup_storage(ctx.obj.vault.storage, yes=ctx.obj.yes)


@cli.command("setup-storage")
@click.pass_obj
def _setup_storage(state: AppState) -> None:
    setup_storage(state.vault.storage, yes=state.yes)
