import click
from loguru import logger

from stages import State


@click.group()
def system() -> None:
    pass


@system.command()
@click.pass_obj
def check(state: State) -> None:
    logger.success(42)
