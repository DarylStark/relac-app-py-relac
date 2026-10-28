"""Main theme for Relac dashboard."""

from pathlib import Path

from relac.theme import RelacTheme

base_path = Path(__file__).parent

relac_theme = RelacTheme(
    name='Default Relac Theme',
    source_dir=base_path / 'templates',
    index_template='index.html',
    resource_pages={'book': 'book.html', 'author': 'author.html'},
    index_pages={
        'books': 'books.html',
        'works': 'works.html',
        'authors': 'authors.html',
        'collections': 'collections.html',
        'lists': 'lists.html',
    },
    static_folder=base_path / 'static',
)
