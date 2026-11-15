import re
import sys
from pathlib import Path

import click
from loguru import logger
from plumbum import FG, ProcessExecutionError, cmd


def get_staged_files() -> list[str]:
    args = ("diff", "--cached", "--name-only", "--diff-filter=ACM")
    return cmd.git(*args).splitlines()


@click.group()
def main() -> None:
    pass


@main.command()
@click.option("--staged",
              is_flag=True,
              help="Format and re-stage only git staged files.")
def fmt(staged: bool) -> None:
    """Format Python files with isort and yapf."""
    if staged:
        targets = [p for p in get_staged_files() if p.endswith(".py")]
    else:
        targets = ["src"]

    if not targets:
        return

    try:
        logger.info(f"Formatting {len(targets)} target(s)...")
        cmd.isort[targets] & FG
        cmd.yapf["-i", "-r", targets] & FG
        if staged:
            cmd.git["add", targets] & FG
        logger.success("Formatting applied.")
    except ProcessExecutionError:
        sys.exit(1)


@main.command("ensure-sops")
def ensure_sops() -> None:
    secret_re = re.compile(r"^secrets/.*\.(yaml|yml|json|env|ini)$")
    targets = [p for p in get_staged_files() if secret_re.match(p)]

    if not targets:
        return

    try:
        logger.info(f"Checking SOPS encryption for {len(targets)} file(s)...")
        cmd.ensure_sops[targets] & FG
        logger.success("All secrets encrypted.")
    except ProcessExecutionError:
        logger.error("Unencrypted secret detected. Aborting commit.")
        sys.exit(1)
