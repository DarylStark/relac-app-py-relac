"""Tests for static HTML template helpers."""

from datetime import date
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader
from typer.testing import CliRunner

from relac.cli_static_html import (
    _build_search_index,
    _calculate_age,
    _format_enum_label,
)
from relac.database import Database
from relac.main import app
from relac.model import (
    Availability,
    Book,
    BookCollection,
    Contributor,
    Label,
    Owner,
    OwnerType,
    Rating,
    ReadingList,
    ReadingListItem,
    ReadingSession,
    ReadingState,
    RelacConfig,
    ResourceAvailability,
    Series,
    SeriesItem,
    Work,
    WorkEdition,
    WorkStructure,
    WorkType,
)


def test_calculate_age_before_birthday() -> None:
    """Do not count the current year before the birthday."""
    assert _calculate_age(date(1980, 7, 15), date(2026, 6, 20)) == 45


def test_calculate_age_on_birthday() -> None:
    """Count the new age on the birthday."""
    assert _calculate_age(date(1980, 7, 15), date(2026, 7, 15)) == 46


def test_calculate_age_at_death() -> None:
    """Calculate a deceased contributor's age at the death date."""
    assert _calculate_age(date(1980, 7, 15), date(2020, 7, 14)) == 39


def test_calculate_age_without_birthdate() -> None:
    """Do not show an age when the birthdate is unknown."""
    assert _calculate_age(None, date(2026, 7, 15)) is None


@pytest.mark.parametrize(
    ('rating', 'expected_class', 'expected_display'),
    [
        (4.9, 'rating-value--low', '4.9'),
        (5.0, 'rating-value--medium', '5.0'),
        (6.9, 'rating-value--medium', '6.9'),
        (7.0, 'rating-value--high', '7.0'),
        (8.9, 'rating-value--high', '8.9'),
        (9.0, 'rating-value--excellent', '9.0'),
    ],
)
def test_rating_values_use_expected_color_category(
    rating: float, expected_class: str, expected_display: str
) -> None:
    """Apply rating colors at each threshold."""
    template_directory = (
        Path(__file__).parents[1] / 'src' / 'relac_theme_default' / 'templates'
    )
    template = Environment(
        loader=FileSystemLoader(template_directory)
    ).get_template('_rating_value.html')
    rendered = template.module.rating_value(rating)  # ty: ignore[unresolved-attribute]

    assert (
        f'class="availability-badge rating-value {expected_class}"' in rendered
    )
    assert f'>{expected_display}</span>' in rendered


@pytest.mark.parametrize(
    ('availability', 'expected'),
    [
        (ResourceAvailability.UNAVAILABLE, 'Unavailable'),
        (ResourceAvailability.AVAILABLE_DIRECT, 'Available'),
        (ResourceAvailability.AVAILABLE_INDIRECT, 'Available (indirect)'),
        (ResourceAvailability.AVAILABLE_TO_LOAN, 'Available to loan'),
        (ResourceAvailability.AVAILABLE_TO_BUY, 'Available to buy'),
    ],
)
def test_resource_availability_labels(
    availability: ResourceAvailability, expected: str
) -> None:
    """Format the new resource availability values for display."""
    assert _format_enum_label(availability.value) == expected


def test_build_search_index_includes_book_metadata_and_url() -> None:
    """Include a book's ID, related contributor, ISBN, and page URL."""
    database = Database()
    contributor = Contributor(id='jane_doe', name='Jane Doe')
    book = Book(
        id='glass_hotel',
        isbn13=9781982137984,
        title='The Glass Hotel',
        contributor_objs=[contributor],
    )
    database.add_contributor('jane_doe', contributor)
    database.add_book('glass_hotel', book)

    book_entry = next(
        item
        for item in _build_search_index(database)['items']
        if item['type'] == 'Book'
    )

    assert book_entry['href'] == 'glass_hotel.html'
    assert 'glass_hotel' in book_entry['searchText']
    assert 'glass_hotel' not in book_entry['details']
    assert 'Jane Doe' in book_entry['searchText']
    assert str(book.isbn13) in book_entry['searchText']

    contributor_entry = next(
        item
        for item in _build_search_index(database)['items']
        if item['type'] == 'Contributor'
    )
    assert contributor_entry['href'] == 'jane_doe.html'
    assert contributor_entry['title'] == 'Jane Doe'


def test_build_search_index_includes_reading_session_details() -> None:
    """Include reading-session metadata and its detail-page URL in search."""
    database = Database()
    book = Book(
        id='test_book',
        isbn13=9781234567897,
        title='Test Book',
    )
    edition = WorkEdition(
        id='test_edition',
        title='Test Edition',
        work='test_work',
        language='en',
    )
    session = ReadingSession(
        id='test_session',
        work_edition='test_edition',
        book='test_book',
        state=ReadingState.FINISHED,
        startdate=date(2026, 1, 1),
        work_rating=Rating(rating=9.0, note='Great story'),
        book_obj=book,
        work_edition_obj=edition,
    )
    database.add_reading_session('test_session', session)

    entry = next(
        item
        for item in _build_search_index(database)['items']
        if item['type'] == 'Reading session'
    )

    assert entry['href'] == 'test_session.html'
    assert entry['title'] == 'Test Edition'
    assert 'Test Book' in entry['searchText']
    assert 'Great story' in entry['searchText']
    assert '2026-01-01' in entry['searchText']


def test_reading_session_table_shows_ongoing_end_date() -> None:
    """Show an ongoing label for sessions with no end date."""
    template_directory = (
        Path(__file__).parents[1] / 'src' / 'relac_theme_default' / 'templates'
    )
    environment = Environment(loader=FileSystemLoader(template_directory))
    environment.filters['enum_label'] = _format_enum_label
    session = ReadingSession(
        id='ongoing_session',
        work_edition='test_edition',
        book='test_book',
        state=ReadingState.READING,
    )

    reading_sessions = environment.get_template(
        '_reading_session_table.html'
    ).module.reading_session_table([session])  # ty: ignore[unresolved-attribute]

    assert 'Ongoing' in reading_sessions
    assert 'data-filter-values=\'["Ongoing"]\'' in reading_sessions


def test_reading_list_rating_renders_in_table_and_detail() -> None:
    """Show reading-list ratings with one decimal, including unrated lists."""
    template_directory = (
        Path(__file__).parents[1] / 'src' / 'relac_theme_default' / 'templates'
    )
    environment = Environment(loader=FileSystemLoader(template_directory))
    environment.filters['enum_label'] = _format_enum_label
    environment.filters['language'] = lambda language: language or ''
    environment.filters['age'] = _calculate_age
    environment.filters['country'] = lambda country: country
    environment.filters['isbn'] = str
    config = RelacConfig(title='Test Library')

    session = ReadingSession(
        id='rated_session',
        work_edition='rated_edition',
        book='rated_book',
        state=ReadingState.FINISHED,
        work_rating=Rating(rating=8.5),
    )
    edition = WorkEdition(
        id='rated_edition',
        title='Rated Edition',
        work='rated_work',
        language='en',
        reading_session_objs=[session],
    )
    work = Work(
        id='rated_work',
        title='Rated Work',
        authors=[],
        work_structure=WorkStructure.UNSPECIFIED,
        work_type=WorkType.UNSPECIFIED,
        edition_objs=[edition],
    )
    rated_list = ReadingList(
        id='rated_list',
        name='Rated List',
        works=[ReadingListItem(order=1, work='rated_work', work_obj=work)],
    )
    list_table = environment.get_template('_list_table.html').module.list_table(  # ty: ignore[unresolved-attribute]
        [rated_list]
    )
    list_detail = environment.get_template('list.html').render(
        list=rated_list,
        config=config,
    )

    assert list_table.index('>Works read</th>') < list_table.index(
        '>Rating</th>'
    )
    rated_row = list_table.split('<tr data-href="rated_list.html">', 1)[
        1
    ].split('</tr>', 1)[0]
    assert rated_row.index('data-sort-value="8.5"') > rated_row.rindex('<td')
    assert (
        'class="availability-badge rating-value rating-value--high">8.5</span>'
        in rated_row
    )
    rating_fact = list_detail.split('<dt>Rating</dt>', 1)[1].split('</div>', 1)[
        0
    ]
    assert 'rating-value--high">8.5</span>' in rating_fact

    unrated_work = Work(
        id='unrated_work',
        title='Unrated Work',
        authors=[],
        work_structure=WorkStructure.UNSPECIFIED,
        work_type=WorkType.UNSPECIFIED,
    )
    unrated_list = ReadingList(
        id='unrated_list',
        name='Unrated List',
        works=[
            ReadingListItem(
                order=1,
                work='unrated_work',
                work_obj=unrated_work,
            )
        ],
    )
    unrated_table = environment.get_template(
        '_list_table.html'
    ).module.list_table([unrated_list])  # ty: ignore[unresolved-attribute]
    unrated_detail = environment.get_template('list.html').render(
        list=unrated_list,
        config=config,
    )

    assert 'data-filter-values=\'["Unrated"]\'' in unrated_table
    assert 'rating-value--unrated">Unrated</span>' in unrated_table
    assert 'rating-value--unrated">Unrated</span>' in unrated_detail


def test_series_rating_renders_in_table_and_detail() -> None:
    """Show a series rating in the final column and its detail metadata."""
    template_directory = (
        Path(__file__).parents[1] / 'src' / 'relac_theme_default' / 'templates'
    )
    environment = Environment(loader=FileSystemLoader(template_directory))
    environment.filters['enum_label'] = _format_enum_label
    environment.filters['language'] = lambda language: language or ''
    environment.filters['age'] = _calculate_age
    environment.filters['country'] = lambda country: country
    environment.filters['isbn'] = str
    config = RelacConfig(title='Test Library')

    session = ReadingSession(
        id='series_session',
        work_edition='series_edition',
        book='series_book',
        state=ReadingState.FINISHED,
        work_rating=Rating(rating=8.5),
    )
    edition = WorkEdition(
        id='series_edition',
        title='Series Edition',
        work='series_work',
        language='en',
        reading_session_objs=[session],
    )
    work = Work(
        id='series_work',
        title='Series Work',
        authors=[],
        work_structure=WorkStructure.UNSPECIFIED,
        work_type=WorkType.UNSPECIFIED,
        edition_objs=[edition],
    )
    series = Series(
        id='test_series',
        name='Test Series',
        works=[SeriesItem(number=1, work='series_work', work_obj=work)],
    )
    series_table = environment.get_template(
        '_series_table.html'
    ).module.series_table([series])  # ty: ignore[unresolved-attribute]
    series_detail = environment.get_template('series_detail.html').render(
        series=series,
        config=config,
    )

    assert series_table.index('>Works read</th>') < series_table.index(
        '>Rating</th>'
    )
    series_row = series_table.split('<tr data-href="test_series.html">', 1)[
        1
    ].split('</tr>', 1)[0]
    assert series_row.index('data-sort-value="8.5"') > series_row.rindex('<td')
    assert 'rating-value--high">8.5</span>' in series_row
    rating_fact = series_detail.split('<dt>Rating</dt>', 1)[1].split(
        '</div>', 1
    )[0]
    assert 'rating-value--high">8.5</span>' in rating_fact


def test_book_collection_rating_renders_in_table_and_detail() -> None:
    """Show BookCollection ratings in the table and detail metadata."""
    template_directory = (
        Path(__file__).parents[1] / 'src' / 'relac_theme_default' / 'templates'
    )
    environment = Environment(loader=FileSystemLoader(template_directory))
    environment.filters['enum_label'] = _format_enum_label
    environment.filters['language'] = lambda language: language or ''
    environment.filters['age'] = _calculate_age
    environment.filters['country'] = lambda country: country
    environment.filters['isbn'] = str
    config = RelacConfig(title='Test Library')
    environment.globals['config'] = config  # ty: ignore[invalid-assignment]

    session = ReadingSession(
        id='rated_book_session',
        work_edition='rated_book_edition',
        book='rated_book',
        state=ReadingState.FINISHED,
        book_rating=Rating(rating=8.5),
    )
    book = Book(
        id='rated_book',
        isbn13=9781234567897,
        title='Rated Book',
        reading_session_objs=[session],
    )
    collection = BookCollection(
        id='rated_collection',
        name='Rated Collection',
        book_objs=[book],
    )
    collection_table = environment.get_template(
        '_collection_table.html'
    ).module.collection_table([collection])  # ty: ignore[unresolved-attribute]
    collection_detail = environment.get_template('collection.html').render(
        collection=collection,
        config=config,
    )

    assert collection_table.index('>Owned</th>') < collection_table.index(
        '>Rating</th>'
    )
    collection_row = collection_table.split(
        '<tr data-href="rated_collection.html">', 1
    )[1].split('</tr>', 1)[0]
    assert collection_row.index(
        'data-sort-value="8.5"'
    ) > collection_row.rindex('<td')
    assert 'rating-value--high">8.5</span>' in collection_row
    rating_fact = collection_detail.split('<dt>Rating</dt>', 1)[1].split(
        '</div>', 1
    )[0]
    assert 'rating-value--high">8.5</span>' in rating_fact

    unrated_collection = BookCollection(
        id='unrated_collection',
        name='Unrated Collection',
    )
    unrated_table = environment.get_template(
        '_collection_table.html'
    ).module.collection_table([unrated_collection])  # ty: ignore[unresolved-attribute]
    unrated_detail = environment.get_template('collection.html').render(
        collection=unrated_collection,
        config=config,
    )
    assert 'data-filter-values=\'["Unrated"]\'' in unrated_table
    assert 'rating-value--unrated">Unrated</span>' in unrated_table
    assert 'rating-value--unrated">Unrated</span>' in unrated_detail


def test_static_html_create_generates_reading_session_detail(
    tmp_path: Path,
) -> None:
    """Generate a dedicated HTML page for each reading session."""
    project_path = Path(__file__).parent / 'simple_project'
    result = CliRunner().invoke(
        app,
        [
            '--project-path',
            str(project_path),
            'static_html',
            'create',
            '--output',
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.exception or result.output
    session_pages = list(tmp_path.glob('reading_session.*.html'))
    assert session_pages
    assert '<title>Reading session:' in session_pages[0].read_text()
    labels_page = tmp_path / 'labels.html'
    assert labels_page.exists()
    labels_html = labels_page.read_text()
    assert 'Contributor count' in labels_html
    assert (
        'href="labels.html" class="active" aria-current="page">Labels</a>'
        in labels_html
    )
    label_row = labels_html.split('<tr data-href="label.test_label.html">', 1)[
        1
    ].split('</tr>', 1)[0]
    assert 'href="label.test_label.html">testlabel</a>' in label_row
    assert '<pre>1</pre>' in label_row
    label_page = tmp_path / 'label.test_label.html'
    assert label_page.exists()
    label_html = label_page.read_text()
    assert 'Contributors with this label' in label_html
    assert (
        'href="contributor.john_williams.html">John Willams</a>' in label_html
    )


def test_work_edition_credits_render_in_table_and_detail() -> None:  # noqa: PLR0915
    """Render optional illustrators and translators as linked contributors."""
    template_directory = (
        Path(__file__).parents[1] / 'src' / 'relac_theme_default' / 'templates'
    )
    environment = Environment(loader=FileSystemLoader(template_directory))
    environment.filters['enum_label'] = _format_enum_label
    environment.filters['language'] = lambda language: language or ''
    environment.filters['age'] = _calculate_age
    environment.filters['country'] = lambda country: country
    environment.filters['isbn'] = str
    config = RelacConfig(title='Test Library')
    environment.globals['config'] = config  # ty: ignore[invalid-assignment]

    work = Work(
        id='test_work',
        title='Test Work',
        authors=[],
        work_structure=WorkStructure.UNSPECIFIED,
        work_type=WorkType.UNSPECIFIED,
    )
    illustrator = Contributor(id='illustrator', name='Test Illustrator')
    translator = Contributor(id='translator', name='Test Translator')
    edition = WorkEdition(
        id='test_edition',
        title='Test Edition',
        work='test_work',
        work_obj=work,
        language='en',
        illustrator_objs=[illustrator],
        translator_objs=[translator],
    )
    session = ReadingSession(
        id='test_session',
        work_edition='test_edition',
        book='test_book',
        state=ReadingState.FINISHED,
        work_rating=Rating(rating=8.5, note='Great characterization'),
        book_rating=Rating(rating=6.5, note='Comfortable binding'),
        startdate=date(2026, 1, 1),
        enddate=date(2026, 1, 5),
        work_edition_obj=edition,
    )
    edition.reading_session_objs.append(session)
    edition.illustrator_objs.append(translator)
    work.edition_objs.append(edition)

    table_template = environment.get_template('_work_edition_table.html')
    table_macro = table_template.module.work_edition_table  # ty: ignore[unresolved-attribute]
    table_html = table_macro([edition])
    reading_session_html = environment.get_template(
        '_reading_session_table.html'
    ).module.reading_session_table([session])  # ty: ignore[unresolved-attribute]
    work_editions_html = environment.get_template('work_editions.html').render(
        work_editions=[edition],
        config=config,
    )
    detail_html = environment.get_template('work_edition.html').render(
        work_edition=edition,
        config=config,
    )

    assert 'Work Editions' in work_editions_html
    assert 'Test Edition' in work_editions_html
    assert (
        'href="work-editions.html" class="active" aria-current="page"'
        in detail_html
    )
    assert '<th scope="col">Work</th>' in table_html
    assert 'href="test_work.html">Test Work</a>' in table_html
    assert 'data-sort-value="8.5"' in table_html
    assert 'data-sort-value="8.5"' in reading_session_html
    assert 'data-sort-value="6.5"' in reading_session_html
    assert 'Work rating' in reading_session_html
    assert 'Book rating' in reading_session_html
    assert 'Work rating note' in reading_session_html
    assert 'Book rating note' in reading_session_html
    assert 'Great characterization' in reading_session_html
    assert 'Comfortable binding' in reading_session_html
    assert 'data-href="test_session.html"' in reading_session_html

    assert '8.5' in detail_html
    assert '<title>Work Editions | Test Library</title>' in work_editions_html
    assert 'href="works.html" class="active"' in work_editions_html
    assert (
        'href="work-editions.html" class="active" aria-current="page"'
        in work_editions_html
    )
    assert 'href="works.html">Works</a>' in work_editions_html

    for html in (table_html, detail_html):
        assert 'Test Illustrator' in html
        assert 'href="illustrator.html"' in html
        assert 'Test Translator' in html
        assert 'href="translator.html"' in html

    contributor = Contributor(
        id='test_contributor',
        name='Test Contributor',
        label_objs=[
            Label(id='label_zebra', name='Zebra'),
            Label(id='label_author', name='Author'),
        ],
        work_objs=[work],
        illustrator_work_edition_objs=[edition],
        translator_work_edition_objs=[edition],
    )
    work.author_objs.append(contributor)
    work_table_html = environment.get_template(
        '_work_table.html'
    ).module.work_table([work])  # ty: ignore[unresolved-attribute]
    work_detail_html = environment.get_template('work.html').render(
        work=work,
        reading_lists=[],
        config=config,
    )
    assert 'data-sort-value="8.5"' in work_table_html
    assert '<dt>Rating</dt>' in work_detail_html
    assert '8.5' in work_detail_html
    book = Book(
        id='test_book',
        isbn13=9781234567897,
        title='Test Book',
        contributor_objs=[contributor, illustrator, translator],
        work_edition_objs=[edition],
        reading_session_objs=[session],
    )
    session.book_obj = book
    book_html = environment.get_template('book.html').render(
        book=book,
        config=config,
    )
    reading_session_detail_html = environment.get_template(
        'reading_session.html'
    ).render(reading_session=session, config=config)
    assert (
        '<title>Reading session: Test Edition | Test Library</title>'
        in reading_session_detail_html
    )
    assert (
        'href="test_edition.html">Test Edition</a>'
        in reading_session_detail_html
    )
    assert 'href="test_work.html">Test Work</a>' in reading_session_detail_html
    assert 'href="test_book.html">Test Book</a>' in reading_session_detail_html
    assert (
        'href="test_contributor.html">Test Contributor</a>'
        in reading_session_detail_html
    )
    assert (
        'href="translator.html">Test Translator</a>'
        in reading_session_detail_html
    )
    assert (
        'href="illustrator.html">Test Illustrator</a>'
        in reading_session_detail_html
    )
    assert 'Great characterization' in reading_session_detail_html
    assert 'Comfortable binding' in reading_session_detail_html
    assert 'datetime="2026-01-01"' in reading_session_detail_html
    work_edition_fact = reading_session_detail_html.split(
        '<dt>Work edition</dt>', 1
    )[1].split('</div>', 1)[0]
    assert 'href="test_edition.html">Test Edition</a>' in work_edition_fact
    assert 'Authors:' in work_edition_fact
    assert 'Translators:' in work_edition_fact
    assert 'Illustrators:' in work_edition_fact
    assert (
        'href="test_contributor.html">Test Contributor</a>' in work_edition_fact
    )
    assert 'href="translator.html">Test Translator</a>' in work_edition_fact
    assert 'href="illustrator.html">Test Illustrator</a>' in work_edition_fact

    session.work_rating = Rating(rating=8.5)
    session.book_rating = Rating(rating=6.5)
    reading_session_html = environment.get_template(
        '_reading_session_table.html'
    ).module.reading_session_table([session])  # ty: ignore[unresolved-attribute]
    assert '<td>None</td>' not in reading_session_html

    assert (
        reading_session_detail_html.index('href="test_work.html">Test Work</a>')
        < reading_session_detail_html.index('8.5')
        < reading_session_detail_html.index(
            'href="test_book.html">Test Book</a>'
        )
        < reading_session_detail_html.index('6.5')
    )
    books_html = environment.get_template('books.html').render(
        books=[book],
        config=config,
    )
    assert (
        '<th scope="col" class="right fit-content"'
        ' data-sort-type="number">Rating</th>' in books_html
    )
    assert 'data-sort-value="6.5"' in books_html
    assert '<dt>Rating</dt>' in book_html
    assert '8.5' in book_html
    assert 'href="test_contributor.html">Test Contributor</a>' in book_html
    assert (
        'href="illustrator.html">Test Illustrator</a> (Illustrator)</span>'
        in book_html
    )
    assert (
        'href="translator.html">Test Translator</a> '
        '(Illustrator and Translator)</span>' in book_html
    )
    assert 'Test Contributor</a>, <a' not in book_html

    contributor_page = environment.get_template('contributor.html')
    contributor_html = contributor_page.render(
        contributor=contributor,
        config=config,
    )
    contributor_table_html = environment.get_template(
        '_contributor_table.html'
    ).module.contributor_table([contributor])  # ty: ignore[unresolved-attribute]

    assert 'Works for this contributor' in contributor_html
    assert 'rating-value--high' in contributor_html
    labels_html = contributor_html.split('<section class="detail-labels"', 1)[
        1
    ].split('</section>', 1)[0]
    assert labels_html.index('Author') < labels_html.index('Zebra')
    assert (
        '<a class="detail-label-pill" href="label_author.html">Author</a>'
        in labels_html
    )
    assert (
        '<a class="detail-label-pill" href="label_zebra.html">Zebra</a>'
        in labels_html
    )
    assert 'data-sort-value="8.5"' in contributor_table_html
    assert contributor_table_html.index(
        '>Works read</th>'
    ) < contributor_table_html.index('>Rating</th>')
    assert contributor_table_html.index(
        '%</pre>'
    ) < contributor_table_html.index('data-sort-value="8.5"')
    assert 'rating-value--high' in contributor_table_html
    assert 'Work Editions illustrated by this contributor' in contributor_html
    assert 'Work Editions translated by this contributor' in contributor_html
    assert 'id="illustrator-work-editions-table"' in contributor_html
    assert 'id="translator-work-editions-table"' in contributor_html

    contributor_without_credits = Contributor(
        id='empty_contributor',
        name='Empty Contributor',
    )
    empty_contributor_html = contributor_page.render(
        contributor=contributor_without_credits,
        config=config,
    )

    assert 'Works for this contributor' not in empty_contributor_html
    assert (
        'Work Editions illustrated by this contributor'
        not in empty_contributor_html
    )
    assert (
        'Work Editions translated by this contributor'
        not in empty_contributor_html
    )
    assert 'Books with this contributor' not in empty_contributor_html
    assert 'detail-labels' not in empty_contributor_html

    edition_without_credits = WorkEdition(
        id='no_credits',
        title='No Credits',
        work='test_work',
        work_obj=work,
        language='en',
    )
    empty_table_html = table_macro([edition_without_credits])
    empty_detail_html = environment.get_template('work_edition.html').render(
        work_edition=edition_without_credits,
        config=config,
    )

    assert empty_table_html.count('Unspecified') >= 2
    assert 'Unrated' in empty_table_html
    assert empty_detail_html.count('Unspecified') >= 2
    assert 'Unrated' in empty_detail_html
    session_without_credits = ReadingSession(
        id='session_without_credits',
        work_edition='no_credits',
        book='test_book',
        state=ReadingState.FINISHED,
        work_edition_obj=edition_without_credits,
    )
    session_without_credits_html = environment.get_template(
        'reading_session.html'
    ).render(reading_session=session_without_credits, config=config)
    session_work_edition_fact = session_without_credits_html.split(
        '<dt>Work edition</dt>', 1
    )[1].split('</div>', 1)[0]
    assert 'Translators:' not in session_work_edition_fact
    assert 'Illustrators:' not in session_work_edition_fact


def test_build_search_index_includes_owner_metadata_and_url() -> None:
    """Include an owner's type, availability, books, and page URL."""
    database = Database()
    book = Book(
        id='glass_hotel',
        isbn13=9781982137984,
        title='The Glass Hotel',
    )
    owner = Owner(
        id='city_library',
        name='City Library',
        owner_type=OwnerType.LIBRARY,
        availability=Availability.INDIRECTLY_AVAILABLE,
        book_objs=[book],
    )
    database.add_owner('city_library', owner)

    owner_entry = next(
        item
        for item in _build_search_index(database)['items']
        if item['type'] == 'Owner'
    )

    assert owner_entry['href'] == 'city_library.html'
    assert owner_entry['title'] == 'City Library'
    assert 'Library' in owner_entry['searchText']
    assert 'Indirectly' in owner_entry['searchText']
    assert 'The Glass Hotel' in owner_entry['searchText']

    owner_without_books = Owner(id='local_store', name='Local Store')
    database.add_owner('local_store', owner_without_books)
    index = _build_search_index(database)['items']
    store_entry = next(
        item for item in index if item['href'] == 'local_store.html'
    )
    assert not any(
        detail.startswith('Books:') for detail in store_entry['details']
    )


def test_build_search_index_includes_series_and_url() -> None:
    """Include series names and generated detail page URLs."""
    database = Database()
    series = Series(id='the_housemaid', name='The Housemaid')
    database.add_series('the_housemaid', series)

    series_entry = next(
        item
        for item in _build_search_index(database)['items']
        if item['type'] == 'Series'
    )

    assert series_entry['href'] == 'the_housemaid.html'
    assert series_entry['title'] == 'The Housemaid'
    assert 'The Housemaid' in series_entry['searchText']
