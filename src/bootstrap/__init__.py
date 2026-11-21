import json
from dataclasses import dataclass
from functools import cached_property
import click
from plumbum import cmd
from bootstrap.storage import setup_storage


@dataclass(frozen=True)
class Vault:
    @staticmethod
    def _decrypt(name: str) -> dict:
        raw = cmd.sops("-d", "--output-type", "json", f"secrets/{name}")
        return json.loads(raw)

    @cached_property
    def storage(self) -> dict:
        return self._decrypt("storage.yaml")


@click.group(invoke_without_command=True)
@click.option("--yes", is_flag=True)
@click.pass_context
def cli(ctx: click.Context, yes: bool) -> None:
    ctx.obj = Vault()
    if ctx.invoked_subcommand is None:
        setup_storage(ctx.obj.storage, yes=yes)


@cli.command("setup-storage")
@click.option("--yes", is_flag=True)
@click.pass_obj
def cmd_setup_storage(vault: Vault, yes: bool) -> None:
    setup_storage(vault.storage, yes=yes)
