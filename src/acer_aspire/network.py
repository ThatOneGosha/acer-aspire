from loguru import logger
from acer_aspire import State
import click

@click.group()
def network() -> None:
    pass

@network.command()
@click.pass_obj
def check(state: State) -> None:
    logger.success(42)
