"""Main theme for Relac dashboard."""

from pathlib import Path

from relac.theme import RelacTheme

base_path = Path(__file__).parent

relac_theme = RelacTheme(
    name='Default Relac Theme',
    source_dir=base_path / 'templates',
    index_template='index.html',
    resource_pages={
        'book': 'book.html',
        'contributor': 'contributor.html',
        'label': 'label.html',
        'work': 'work.html',
        'work_edition': 'work_edition.html',
        'collection': 'collection.html',
        'list': 'list.html',
        'series': 'series_detail.html',
        'owner': 'owner.html',
        'reading_session': 'reading_session.html',
    },
    index_pages={
        'books': 'books.html',
        'works': 'works.html',
        'work_editions': 'work_editions.html',
        'series': 'series.html',
        'contributors': 'contributors.html',
        'labels': 'labels.html',
        'collections': 'collections.html',
        'lists': 'lists.html',
        'reading_sessions': 'reading_sessions.html',
        'owners': 'owners.html',
    },
    static_folder=base_path / 'static',
)
