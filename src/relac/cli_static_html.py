"""`static_html` part of the CLI application."""

import shutil
from importlib import import_module
from pathlib import Path

from isbnlib import mask
from jinja2 import Environment, FileSystemLoader
from typer import Context, Option, Typer

from relac.model import BookBinding, BookMedium, WorkStructure, WorkType
from relac.theme import RelacTheme


def _format_enum_label(value: str) -> str:
    """Format enum values for display without changing their stored values."""
    labels = {
        'ebook': 'eBook',
        'epub': 'ePub',
        'epub-drm': 'ePub (DRM)',
        'epub-watermark': 'ePub (watermarked)',
        'graphical-novel-adaption': 'Graphic novel adaptation',
    }
    return labels.get(value, value.replace('-', ' ').capitalize())


cli_static_html = Typer(name='static_html')


@cli_static_html.command(name='create')
def create(
    ctx: Context,
    output: Path = Option(
        default=Path('.'), help='The output folder for the static website'
    ),
) -> None:
    """Create the Static HTML page."""
    db = ctx.obj.database

    theme_module = 'relac_theme_default'  # TODO: Make this configurable

    theme_obj = import_module(theme_module)
    metadata = getattr(theme_obj, 'relac_theme', None)
    if not metadata or not isinstance(metadata, RelacTheme):
        # TODO: Custom exception
        raise TypeError(f'Module "{theme_module}" has no "relac_theme" object.')

    env = Environment(loader=FileSystemLoader(metadata.source_dir))
    env.filters['isbn'] = lambda x: mask(str(x))
    env.filters['enum_label'] = _format_enum_label

    # Copy static folder
    if metadata.static_folder:
        source = metadata.static_folder
        shutil.copytree(source, output / source.name, dirs_exist_ok=True)

    # Index page
    template = env.get_template(metadata.index_template)
    html = template.render(db=db)
    out_path = output / 'index.html'
    out_path.write_text(html)

    # Index pages
    if 'books' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['books'])
        book_items = list(db.get_books().items())
        publishers = sorted(
            {
                book.publisher_obj.name if book.publisher_obj else ''
                for _, book in book_items
            },
            key=lambda value: (bool(value), value.casefold()),
        )
        imprints = sorted(
            {
                book.publisher_obj.imprint
                if book.publisher_obj and book.publisher_obj.imprint
                else ''
                for _, book in book_items
            },
            key=lambda value: (bool(value), value.casefold()),
        )
        html = template.render(
            books=book_items,
            book_mediums=list(BookMedium),
            book_bindings=list(BookBinding),
            publishers=publishers,
            imprints=imprints,
        )
        out_path = output / 'books.html'
        out_path.write_text(html)

    if 'works' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['works'])
        work_items = list(db.get_works().items())
        author_names = {
            author_id: author.name
            for _, work in work_items
            for author_id, author in zip(
                work.authors, work.authors_objs, strict=True
            )
        }
        authors = sorted(
            (
                {'id': author_id, 'name': author_name}
                for author_id, author_name in author_names.items()
            ),
            key=lambda author: (author['name'].casefold(), author['id']),
        )
        html = template.render(
            works=work_items,
            work_types=list(WorkType),
            work_structures=list(WorkStructure),
            authors=authors,
        )
        out_path = output / 'works.html'
        out_path.write_text(html)

    # Books
    if 'book' in metadata.resource_pages:
        for book_id, book in db.get_books().items():
            template = env.get_template(metadata.resource_pages['book'])
            html = template.render(book=book)
            out_path = output / f'{book_id}.html'
            out_path.write_text(html)
