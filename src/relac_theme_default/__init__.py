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
        'book_owner': 'book_owner.html',
        'contributor': 'contributor.html',
        'location': 'location.html',
        'character': 'character.html',
        'label': 'label.html',
        'work': 'work.html',
        'literary_analysis': 'literary_analysis.html',
        'literary_analysis_chapter': 'literary_analysis_chapter.html',
        'literary_analysis_locations': 'literary_analysis_locations.html',
        'literary_analysis_characters': 'literary_analysis_characters.html',
        'literary_analysis_motifs': 'literary_analysis_motifs.html',
        'literary_analysis_quotes': 'literary_analysis_quotes.html',
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
        'characters': 'characters.html',
        'locations': 'locations.html',
        'labels': 'labels.html',
        'collections': 'collections.html',
        'lists': 'lists.html',
        'reading_sessions': 'reading_sessions.html',
        'owners': 'owners.html',
    },
    static_folder=base_path / 'static',
)
