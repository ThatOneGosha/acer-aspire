from loguru import logger
from dataclasses import dataclass
from plumbum.cmd import sops
import click
import json

@dataclass(frozen=True)
class State:
    storage: dict
    network: dict

@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    storage = sops["-d", "--output-type", "json", "secrets/storage.yaml"]()
    network = sops["-d", "--output-type", "json", "secrets/network.yaml"]()
    ctx.obj = State(
        storage=json.loads(storage),
        network=json.loads(network)
    )

from acer_aspire.storage import storage
from acer_aspire.network import network

cli.add_command(storage)
cli.add_command(network)

def main() -> None:
    cli()
