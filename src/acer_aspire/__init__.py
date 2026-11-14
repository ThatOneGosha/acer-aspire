from dataclasses import dataclass
from plumbum.cmd import sops
from loguru import logger
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

cli.add_command(storage)

def main() -> None:
    cli()
