"""Module with the `main` method."""

from pathlib import Path

from typer import Context, Option, Typer

from relac.yaml_repo_loader import YamlRepoLoader

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
    repo_loader = YamlRepoLoader(repo_path=project_path)
    ctx.obj = Relac(repo_loader=repo_loader)
    ctx.obj.import_data()


def main() -> None:
    """Main entry point for the CLI app."""
    app()
