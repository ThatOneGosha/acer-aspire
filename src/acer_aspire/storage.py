from acer_aspire import State
from loguru import logger
import click

@click.group()
def storage() -> None:
    pass

@storage.command()
@click.pass_obj
def check(state: State) -> None:
    print(state.storage)
