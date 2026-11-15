import json
from dataclasses import dataclass

import click
from plumbum import cmd


@dataclass(frozen=True)
class State:
    storage: dict
    network: dict


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    storage = cmd.sops("-d", "--output-type", "json", "secrets/storage.yaml")
    network = cmd.sops("-d", "--output-type", "json", "secrets/network.yaml")
    ctx.obj = State(storage=json.loads(storage), network=json.loads(network))


from acer_aspire.network import network
from acer_aspire.storage import storage

cli.add_command(storage)
cli.add_command(network)


def main() -> None:
    cli()
