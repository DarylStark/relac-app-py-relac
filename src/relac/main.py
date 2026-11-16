"""Module with the `main` method."""

import sys
from collections import Counter
from pathlib import Path

from pydantic import ValidationError
from rich.console import Console
from typer import Context, Option, Typer

from relac.exceptions import RelacError
from relac.yaml_repo_loader import YamlRepoLoader

from .relac import Relac

app = Typer(name='relac')


@app.callback()
def context(
    ctx: Context,
    project_path: Path = Option(
        default=Path('.'), help='The diretory with the YAML definitions.'
    ),
) -> None:
    """Default context for all CLI operations."""
    repo_loader = YamlRepoLoader(repo_path=project_path)
    console = Console()
    ctx.obj = {'relac': Relac(repo_loader=repo_loader), 'console': console}

    try:
        ctx.obj['relac'].import_data()
    except (RelacError, ValidationError) as exc:
        console.print(f'[red][b]ERROR: [/b][/red] {exc}')
        sys.exit(1)


@app.command(
    name='create-static-webpage',
    help='Create a static webpage for the Relac repository',
)
def create_static_webpage(ctx: Context, output: Path) -> None:
    """Create the static webpage."""
    relac: Relac = ctx.obj['relac']
    theme_module = 'relac_theme_default'  # TODO: Make this configurable
    relac.create_static_webpage(theme_module=theme_module, output=output)


@app.command(name='validate', help='Validate the Relac repository')
def validate(ctx: Context) -> None:
    """Create the static webpage."""
    console: Console = ctx.obj['console']
    console.print('[green][b]Relac repository is correct[/b][/green]')


@app.command(name='lint', help='Lint the Relac repository')
def lint(
    ctx: Context,
    use_ignores: bool = Option(
        default=True, help='Use the ignore lists for linting.'
    ),
) -> None:
    """Create the static webpage."""
    console: Console = ctx.obj['console']
    relac: Relac = ctx.obj['relac']
    findings = relac.lint_repo(use_ignores=use_ignores)

    if not findings:
        console.print('[green][b]All checks passed![/b][/green]')
        return

    for finding in findings:
        console.print(
            f'[u]{finding.resource_id}[/u] - [yellow][b]{finding.id}[/b]: '
            f'[/yellow]{finding.error}'
        )

    finding_ids = Counter(finding.id for finding in findings)

    console.print('\n[b]Finding totals:[/b]\n')
    for finding_id, count in finding_ids.items():
        console.print(f'{finding_id}: {count}')

    sys.exit(1)


def main() -> None:
    """Main entry point for the CLI app."""
    app()
