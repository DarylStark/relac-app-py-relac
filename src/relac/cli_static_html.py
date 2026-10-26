"""`static_html` part of the CLI application."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from typer import Context, Typer

cli_static_html = Typer(name='static_html')


@cli_static_html.command(name='create')
def create(ctx: Context) -> None:
    """Create the Static HTML page."""
    db = ctx.obj.database
    template_dir = Path(__file__).parent / 'default_static'

    env = Environment(loader=FileSystemLoader(template_dir))

    template = env.get_template('default_static.html')

    html = template.render(db=db)

    print(html)
