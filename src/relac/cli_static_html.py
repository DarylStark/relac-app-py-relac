"""`static_html` part of the CLI application."""

from importlib import import_module

from jinja2 import Environment, FileSystemLoader
from typer import Context, Typer

from relac.theme import RelacTheme

cli_static_html = Typer(name='static_html')


@cli_static_html.command(name='create')
def create(ctx: Context) -> None:
    """Create the Static HTML page."""
    db = ctx.obj.database

    theme_module = 'relac_theme_default'  # TODO: Make this configurable

    theme_obj = import_module(theme_module)
    metadata = getattr(theme_obj, 'relac_theme', None)
    if not metadata or not isinstance(metadata, RelacTheme):
        # TODO: Custom exception
        raise TypeError(f'Module "{theme_module}" has no "relac_theme" object.')

    env = Environment(loader=FileSystemLoader(metadata.source_dir))

    template = env.get_template(metadata.index_template)

    html = template.render(db=db)

    print(html)
