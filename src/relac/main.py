"""Module with the `main` method."""

from pathlib import Path

from typer import Context, Option, Typer

from .cli_static_html import cli_static_html
from .relac import Relac

app = Typer(name='relac')

app.add_typer(cli_static_html)


@app.callback()
def context(
    ctx: Context,
    project_path: Path = Option(
        default=Path('.'), help='The diretory with the YAML definitions.'
    ),
) -> None:
    """Default context for all CLI operations."""
    ctx.obj = Relac(project_path=project_path)


def main() -> None:
    """Main entry point for the CLI app."""
    app()
