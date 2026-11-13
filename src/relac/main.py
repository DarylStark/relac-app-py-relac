"""Module with the `main` method."""

import sys
from pathlib import Path

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
    except RelacError as exc:
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
def lint(ctx: Context) -> None:
    """Create the static webpage."""
    console: Console = ctx.obj['console']
    relac: Relac = ctx.obj['relac']
    findings = relac.lint_repo()

    if not findings:
        console.print('[green][b]All checks passed![/b][/green]')
        return

    for finding in findings:
        console.print(
            f'{finding.resource_id} - [yellow][b]{finding.id}[/b]: '
            '{finding.error}[/yellow]'
        )


def main() -> None:
    """Main entry point for the CLI app."""
    app()
