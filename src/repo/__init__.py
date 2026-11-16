import re

import click
from loguru import logger
from plumbum import FG, ProcessExecutionError, cmd


@click.group()
def main() -> None:
    pass


def get_staged_files() -> list[str]:
    args = ("diff", "--cached", "--name-only", "--diff-filter=ACM")
    return cmd.git(*args).splitlines()


def get_yaml_targets(sources: list[str]) -> list[str]:
    return [
        s for s in sources
        if s.endswith((".yaml", ".yml")) and not s.startswith("secrets/")
    ]


def get_python_targets(sources: list[str]) -> list[str]:
    return [s for s in sources if s.endswith(".py")]


def fmt_yaml(targets: list[str]) -> None:
    cmd.yamlfix[targets] & FG


def fmt_python(targets: list[str]) -> None:
    cmd.isort[targets] & FG
    cmd.yapf["-i", targets] & FG


def get_sops_targets(sources: list[str]) -> list[str]:
    secret_re = re.compile(r"^secrets/.*\.(yaml|yml|json|env|ini)$")
    return [s for s in sources if secret_re.match(s)]


def run_ensure_sops(targets: list[str]) -> None:
    cmd.ensure_sops[targets] & FG


@main.command()
@click.argument("files", nargs=-1)
def fmt(files: tuple[str, ...]) -> None:
    sources = list(files) if files else get_staged_files()
    yaml_targets = get_yaml_targets(sources)
    python_targets = get_python_targets(sources)

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
    sources = list(files) if files else get_staged_files()
    targets = get_sops_targets(sources)

    if not targets:
        logger.info("No staged secrets found, skipping.")
        return

    try:
        logger.info(f"Checking encryption for {len(targets)} file(s)...")
        run_ensure_sops(targets)
        logger.success("Secrets encryption verified.")
    except ProcessExecutionError:
        raise SystemExit(1)


@main.command("pre-commit")
@click.pass_context
def pre_commit(ctx: click.Context) -> None:
    staged = get_staged_files()
    for task in (fmt, ensure_sops):
        ctx.invoke(task, files=staged)
