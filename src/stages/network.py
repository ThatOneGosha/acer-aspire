import click
from loguru import logger

from stages import State


@click.group()
def network() -> None:
    pass


@network.command()
@click.pass_obj
def check(state: State) -> None:
    logger.success(42)
