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
def cli(ctx: click.Context):
    storage = sops["-d", "--output-type", "json", "secrets/storage.yaml"]()
    network = sops["-d", "--output-type", "json", "secrets/network.yaml"]()
    ctx.obj = State(
        storage=json.loads(storage),
        network=json.loads(network)
    )

@cli.command()
@click.pass_obj
def test(state: State):
    logger.info("Network: {} | Storage: {}", state.network, state.storage)

def main() -> None:
    cli()
