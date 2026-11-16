import re

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
def fmt(files: list[str] | None = None) -> None:
    staged = files if files is not None else get_staged_files()
    targets = [p for p in staged if p.endswith(".py")]

    if not targets:
        logger.info("No staged Python files found, skipping.")
        return

    try:
        logger.info(f"Formatting {len(targets)} file(s)...")
        cmd.isort[targets] & FG
        cmd.yapf["-i", targets] & FG
        cmd.git["add", targets] & FG
        logger.success("Formatting applied.")
    except ProcessExecutionError:
        raise SystemExit(1)


@main.command("ensure-sops")
def ensure_sops(files: list[str] | None = None) -> None:
    secret_re = re.compile(r"^secrets/.*\.(yaml|yml|json|env|ini)$")
    staged = files if files is not None else get_staged_files()
    targets = [p for p in staged if secret_re.match(p)]

    if not targets:
        logger.info("No staged secrets found, skipping.")
        return

    try:
        logger.info(f"Checking encryption for {len(targets)} file(s)...")
        cmd.ensure_sops[targets] & FG
        logger.success("Secrets encryption verified.")
    except ProcessExecutionError:
        raise SystemExit(1)


@main.command("pre-commit")
@click.pass_context
def pre_commit(ctx: click.Context) -> None:
    staged = get_staged_files()
    for task in (fmt, ensure_sops):
        ctx.invoke(task, files=staged)
