import re
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache

import click
from loguru import logger
from plumbum import FG, ProcessExecutionError, cmd


@dataclass(frozen=True)
class Targets:
    python: tuple[str, ...]
    yaml: tuple[str, ...]
    secrets: tuple[str, ...]


@click.group()
def main() -> None:
    pass


@cache
def get_targets(sources: tuple[str, ...]) -> Targets:
    python: list[str] = []
    yaml: list[str] = []
    secrets: list[str] = []

    secret_re = re.compile(r"^secrets/.*\.(yaml|yml|json|env|ini)$")

    for path in sources:
        if path.endswith(".py"):
            python.append(path)
        elif path.endswith(
            (".yaml", ".yml")) and not path.startswith("secrets/"):
            yaml.append(path)
        elif secret_re.match(path):
            secrets.append(path)

    return Targets(python=tuple(python),
                   yaml=tuple(yaml),
                   secrets=tuple(secrets))


@cache
def get_staged_files() -> tuple[str, ...]:
    args = ("diff", "--cached", "--name-only", "--diff-filter=ACM")
    return tuple(cmd.git(*args).splitlines())


def fmt_yaml(targets: Sequence[str]) -> None:
    cmd.yamlfix[targets] & FG


def fmt_python(targets: Sequence[str]) -> None:
    cmd.isort[targets] & FG
    cmd.yapf["-i", targets] & FG


def run_ensure_sops(targets: Sequence[str]) -> None:
    cmd.ensure_sops[targets] & FG


def run_checks(targets: Sequence[str]) -> None:
    cmd.ruff["check", targets] & FG
    cmd.mypy[targets] & FG


@main.command()
@click.argument("files", nargs=-1)
def fmt(files: tuple[str, ...]) -> None:
    sources = files if files else get_staged_files()
    yaml_targets = get_targets(sources).yaml
    python_targets = get_targets(sources).python

    if not (yaml_targets or python_targets):
        logger.info("No staged Python or YAML files found, skipping.")
        return

    try:
        if python_targets:
            logger.info(f"Formatting {len(python_targets)} Python file(s)...")
            fmt_python(python_targets)

        if yaml_targets:
            logger.info(f"Formatting {len(yaml_targets)} YAML file(s)...")
            fmt_yaml(yaml_targets)

        cmd.git["add", python_targets + yaml_targets] & FG
        logger.success("Formatting applied.")
    except ProcessExecutionError:
        raise SystemExit(1)


@main.command("ensure-sops")
@click.argument("files", nargs=-1)
def ensure_sops(files: tuple[str, ...]) -> None:
    sources = files if files else get_staged_files()
    targets = get_targets(sources).secrets

    if not targets:
        logger.info("No staged secrets found, skipping.")
        return

    try:
        logger.info(f"Checking encryption for {len(targets)} file(s)...")
        run_ensure_sops(targets)
        logger.success("Secrets encryption verified.")
    except ProcessExecutionError:
        raise SystemExit(1)


@main.command()
@click.argument("files", nargs=-1)
def check(files: tuple[str, ...]) -> None:
    sources = files if files else get_staged_files()
    targets = get_targets(sources).python

    if not targets:
        logger.info("No staged Python files found, skipping.")
        return

    try:
        logger.info(f"Checking {len(targets)} Python file(s)...")
        run_checks(targets)
        logger.success("Checks passed.")
    except ProcessExecutionError:
        raise SystemExit(1)


@main.command("pre-commit")
@click.pass_context
def pre_commit(ctx: click.Context) -> None:
    if not (staged := get_staged_files()):
        logger.info("No staged files found, skipping.")
        return

    for task in (fmt, check, ensure_sops):
        ctx.invoke(task, files=staged)
