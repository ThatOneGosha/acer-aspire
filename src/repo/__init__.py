from pathlib import Path
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
@click.option(
    "--staged", is_flag=True, help="Format and re-stage only git staged files."
)
def fmt(staged: bool) -> None:
  if staged:
    targets = [p for p in get_staged_files() if p.endswith(".py")]
    yapf_flags = ["-i"]
  else:
    targets = ["src"]
    yapf_flags = ["-i", "-r"]

  if not targets:
    logger.info("No Python files to format, skipping.")
    return

  try:
    logger.info(f"Formatting {len(targets)} target(s)...")
    cmd.isort[targets] & FG
    cmd.yapf[*yapf_flags, *targets] & FG
    if staged:
      cmd.git["add", targets] & FG
    logger.success("Formatting applied.")
  except ProcessExecutionError:
    raise SystemExit(1)


@main.command("ensure-sops")
@click.option(
    "--staged", is_flag=True, help="Check only git staged secret files."
)
def ensure_sops(staged: bool) -> None:
  if staged:
    secret_re = re.compile(r"^secrets/.*\.(yaml|yml|json|env|ini)$")
    targets = [p for p in get_staged_files() if secret_re.match(p)]
  else:
    targets = [str(p) for p in Path("secrets").rglob("*") if p.is_file()]

  if not targets:
    logger.info("No secrets found, skipping.")
    return

  try:
    logger.info(f"Checking encryption for {len(targets)} file(s)...")
    cmd.ensure_sops[targets] & FG
    logger.success("All secrets encrypted.")
  except ProcessExecutionError:
    logger.error("Unencrypted secret detected. Aborting commit.")
    raise SystemExit(1)
