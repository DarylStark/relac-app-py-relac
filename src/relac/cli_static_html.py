"""`static_html` part of the CLI application."""

import json
import shutil
from datetime import date
from importlib import import_module
from pathlib import Path

from isbnlib import mask
from jinja2 import Environment, FileSystemLoader
from markdown_it import MarkdownIt
from markupsafe import Markup
from pycountry import countries, languages
from typer import Context, Option, Typer

from relac.theme import RelacTheme

from .database import Database

_MARKDOWN = MarkdownIt('commonmark', {'html': False})


def _render_markdown(text: str) -> Markup:
    """Render Markdown while treating source HTML as plain text."""
    return Markup(_MARKDOWN.render(text))


def _calculate_age(
    birthdate: date | None, reference_date: date | None = None
) -> int | None:
    """Calculate an age in whole years at the reference date."""
    if birthdate is None:
        return None

    reference_date = reference_date or date.today()
    age = reference_date.year - birthdate.year
    if (reference_date.month, reference_date.day) < (
        birthdate.month,
        birthdate.day,
    ):
        age -= 1
    return age


def _format_enum_label(value: str) -> str:
    """Format enum values for display without changing their stored values."""
    labels = {
        'unavailable': 'Unavailable',
        'available-direct': 'Available',
        'available-indirect': 'Available (indirect)',
        'available-to-loan': 'Available to loan',
        'available-to-buy': 'Available to buy',
        'ebook': 'eBook',
        'epub': 'ePub',
        'epub-drm': 'ePub (DRM)',
        'epub-watermark': 'ePub (watermarked)',
        'graphical-novel-adaption': 'Graphic novel adaptation',
    }
    return labels.get(value, value.replace('-', ' ').capitalize())


def _code_to_language(language_code: str) -> str:
    """Get the name for a language code."""
    lang = languages.get(alpha_2=language_code)
    return lang.name if lang else language_code


def _code_to_country(country_code: str) -> str:
    """Get the name for a country code."""
    country = countries.get(alpha_2=country_code)
    return country.name if country else country_code


def _build_search_index(
    db: Database,
) -> dict[str, list[dict[str, str | list[str]]]]:
    """Build the client-side search data for every linked resource."""
    entries: list[dict[str, str | list[str]]] = []

    def add_entry(
        resource_type: str,
        resource_id: str | None,
        title: str,
        details: list[str],
        search_terms: list[str] | None = None,
        labels: list[str] | None = None,
    ) -> None:
        if resource_id is None:
            return

        if labels:
            details = [*details, f'Labels: {", ".join(labels)}']

        terms = [
            resource_type,
            resource_id,
            title,
            *details,
            *(search_terms or []),
        ]
        entries.append(
            {
                'type': resource_type,
                'title': title,
                'href': f'{resource_id}.html',
                'details': details,
                'searchText': ' '.join(terms),
            }
        )

    for book in db.get_books():
        contributors = ', '.join(
            contributor.name for contributor in book.contributor_objs
        )
        publisher = getattr(book.publisher_obj, 'name', '')
        imprint = getattr(book.publisher_obj, 'imprint', '')
        details = [
            f'Contributors: {contributors}' if contributors else '',
            f'Publisher: {publisher}' if publisher else '',
            f'Imprint: {imprint}' if imprint else '',
            f'ISBN: {mask(str(book.isbn13))}',
            f'Medium: {_format_enum_label(book.medium.value)}',
            f'Binding: {_format_enum_label(book.binding.value)}',
            f'Works: {", ".join(e.title for e in book.work_edition_objs)}',
            f'Collections: {", ".join(c.name for c in book.collection_objs)}',
        ]
        details = [detail for detail in details if not detail.endswith(': ')]
        add_entry(
            'Book',
            book.id,
            book.title,
            details,
            [str(book.isbn13)],
            [label.name for label in book.label_objs],
        )

    for work in db.get_works():
        authors = ', '.join(author.name for author in work.author_objs)
        details = [
            f'Authors: {authors}' if authors else '',
            f'Structure: {_format_enum_label(work.work_structure.value)}'
            if work.work_structure
            else '',
            f'Category: {_format_enum_label(work.work_type.value)}'
            if work.work_type
            else '',
            f'Editions: {", ''".join(e.title for e in work.edition_objs)}',
        ]
        add_entry(
            'Work',
            work.id,
            work.title,
            [detail for detail in details if detail],
            labels=[label.name for label in work.label_objs],
        )

    for contributor in db.get_contributors():
        details = [
            f'Works: {", ".join(work.title for work in contributor.work_objs)}',
            f'Books: {", ".join(book.title for book in contributor.book_objs)}',
        ]
        add_entry(
            'Contributor',
            contributor.id,
            contributor.name,
            [detail for detail in details if detail],
            labels=[label.name for label in contributor.label_objs],
        )

    for edition in db.get_work_editions():
        details = [
            f'Work: {edition.work_obj.title}' if edition.work_obj else '',
            f'Release date: {edition.release_date}'
            if edition.release_date
            else '',
            f'Language: {_code_to_language(edition.language)}'
            if edition.language
            else '',
            f'Type: {_format_enum_label(edition.edition_type.value)}',
            f'Books: {", ".join(book.title for book in edition.book_objs)}',
        ]
        add_entry(
            'Edition',
            edition.id,
            edition.title,
            [detail for detail in details if detail],
            labels=[label.name for label in edition.label_objs],
        )

    for collection in db.get_book_collections():
        details = [
            f'Books: {", ".join(book.title for book in collection.book_objs)}'
        ]
        add_entry(
            'Collection',
            collection.id,
            collection.name,
            [detail for detail in details if detail],
            labels=[label.name for label in collection.label_objs],
        )

    for owner in db.get_owners():
        details = [
            f'Type: {_format_enum_label(owner.owner_type.value)}',
            f'Availability: {_format_enum_label(owner.availability.value)}',
            f'Books: {", ".join(book.title for book in owner.book_objs)}',
        ]
        add_entry(
            'Owner',
            owner.id,
            owner.name,
            [detail for detail in details if not detail.endswith(': ')],
            labels=[label.name for label in owner.label_objs],
        )

    for reading_list in db.get_reading_lists():
        work_titles = [
            item.work_obj.title for item in reading_list.works if item.work_obj
        ]
        details = [f'Works: {", ".join(work_titles)}'] if work_titles else []
        add_entry(
            'Reading list',
            reading_list.id,
            reading_list.name,
            details,
            labels=[label.name for label in reading_list.label_objs],
        )

    for series in db.get_series():
        work_titles = [
            item.work_obj.title for item in series.works if item.work_obj
        ]
        details = [f'Works: {", ".join(work_titles)}'] if work_titles else []
        add_entry(
            'Series',
            series.id,
            series.name,
            details,
            labels=[label.name for label in series.label_objs],
        )

    for reading_session in db.get_reading_sessions():
        work_edition_title = (
            reading_session.work_edition_obj.title
            if reading_session.work_edition_obj
            else ''
        )
        book_title = (
            reading_session.book_obj.title if reading_session.book_obj else ''
        )
        details = [
            f'Work edition: {work_edition_title}' if work_edition_title else '',
            f'Book: {book_title}' if book_title else '',
            f'State: {_format_enum_label(reading_session.state.value)}',
            f'Start date: {reading_session.startdate}'
            if reading_session.startdate
            else '',
            f'End date: {reading_session.enddate}'
            if reading_session.enddate
            else '',
            f'Work rating: {reading_session.work_rating.rating}'
            if reading_session.work_rating
            else '',
            f'Work rating note: {reading_session.work_rating.note}'
            if reading_session.work_rating and reading_session.work_rating.note
            else '',
            f'Book rating: {reading_session.book_rating.rating}'
            if reading_session.book_rating
            else '',
            f'Book rating note: {reading_session.book_rating.note}'
            if reading_session.book_rating and reading_session.book_rating.note
            else '',
        ]
        add_entry(
            'Reading session',
            reading_session.id,
            work_edition_title
            or book_title
            or reading_session.id
            or 'Reading session',
            [detail for detail in details if detail],
            labels=[label.name for label in reading_session.label_objs],
        )

    for label in db.get_labels():
        add_entry('Label', label.id, label.name, [])

    return {'items': entries}


cli_static_html = Typer(name='static_html')


@cli_static_html.command(name='create')
def create(  # noqa: PLR0912, PLR0915
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

    output.mkdir(parents=True, exist_ok=True)
    (output / 'search-index.json').write_text(
        json.dumps(_build_search_index(db), ensure_ascii=False),
        encoding='utf-8',
    )

    env = Environment(loader=FileSystemLoader(metadata.source_dir))
    env.filters['isbn'] = lambda x: mask(str(x))
    env.filters['markdown'] = _render_markdown
    env.filters['enum_label'] = _format_enum_label
    env.filters['age'] = _calculate_age
    env.filters['language'] = _code_to_language
    env.filters['country'] = _code_to_country
    env.globals['config'] = db.get_relac_config()

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
        html = template.render(
            books=db.get_books(),
        )
        out_path = output / 'books.html'
        out_path.write_text(html)

    if 'works' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['works'])
        html = template.render(
            works=db.get_works(),
        )
        out_path = output / 'works.html'
        out_path.write_text(html)

    if 'work_editions' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['work_editions'])
        html = template.render(
            work_editions=db.get_work_editions(),
        )
        out_path = output / 'work-editions.html'
        out_path.write_text(html)

    if 'series' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['series'])
        html = template.render(
            series=db.get_series(),
        )
        out_path = output / 'series.html'
        out_path.write_text(html)

    if 'contributors' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['contributors'])
        html = template.render(
            contributors=db.get_contributors(),
        )
        out_path = output / 'contributors.html'
        out_path.write_text(html)

    if 'labels' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['labels'])
        html = template.render(
            labels=db.get_labels(),
        )
        out_path = output / 'labels.html'
        out_path.write_text(html)

    if 'owners' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['owners'])
        html = template.render(
            owners=db.get_owners(),
        )
        out_path = output / 'owners.html'
        out_path.write_text(html)

    if 'collections' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['collections'])
        html = template.render(
            collections=db.get_book_collections(),
        )
        out_path = output / 'collections.html'
        out_path.write_text(html)

    if 'lists' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['lists'])
        html = template.render(
            lists=db.get_reading_lists(),
        )
        out_path = output / 'lists.html'
        out_path.write_text(html)

    if 'reading_sessions' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['reading_sessions'])
        html = template.render(
            reading_sessions=db.get_reading_sessions(),
        )
        out_path = output / 'reading-sessions.html'
        out_path.write_text(html)

    # Books
    if 'book' in metadata.resource_pages:
        for book in db.get_books():
            template = env.get_template(metadata.resource_pages['book'])
            html = template.render(book=book)
            out_path = output / f'{book.id}.html'
            out_path.write_text(html)

    # Contributors
    if 'contributor' in metadata.resource_pages:
        for contributor in db.get_contributors():
            template = env.get_template(metadata.resource_pages['contributor'])
            html = template.render(contributor=contributor)
            out_path = output / f'{contributor.id}.html'
            out_path.write_text(html)

    # Labels
    if 'label' in metadata.resource_pages:
        for label in db.get_labels():
            template = env.get_template(metadata.resource_pages['label'])
            html = template.render(label=label)
            out_path = output / f'{label.id}.html'
            out_path.write_text(html)

    # Owners
    if 'owner' in metadata.resource_pages:
        for owner in db.get_owners():
            template = env.get_template(metadata.resource_pages['owner'])
            html = template.render(owner=owner)
            out_path = output / f'{owner.id}.html'
            out_path.write_text(html)

    # Works
    if 'work' in metadata.resource_pages:
        reading_lists = db.get_reading_lists()
        for work in db.get_works():
            template = env.get_template(metadata.resource_pages['work'])
            matching_reading_lists = [
                reading_list
                for reading_list in reading_lists
                if any(item.work == work.id for item in reading_list.works)
            ]
            html = template.render(
                work=work, reading_lists=matching_reading_lists
            )
            out_path = output / f'{work.id}.html'
            out_path.write_text(html)
            if (
                work.literary_analysis
                and 'literary_analysis' in metadata.resource_pages
            ):
                analysis_template = env.get_template(
                    metadata.resource_pages['literary_analysis']
                )
                analysis_html = analysis_template.render(work=work)
                analysis_path = output / f'literary_analysis.{work.id}.html'
                analysis_path.write_text(analysis_html)
                if (
                    work.literary_analysis.chapters
                    and 'literary_analysis_chapter' in metadata.resource_pages
                ):
                    chapter_template = env.get_template(
                        metadata.resource_pages['literary_analysis_chapter']
                    )
                    for chapter in work.literary_analysis.chapters:
                        chapter_html = chapter_template.render(
                            work=work, chapter=chapter
                        )
                        chapter_path = output / (
                            f'literary_analysis_chapter.{work.id}.'
                            f'{chapter.number}.html'
                        )
                        chapter_path.write_text(chapter_html)
                if (
                    work.literary_analysis.setting
                    and work.literary_analysis.setting.location_objs
                    and 'literary_analysis_locations' in metadata.resource_pages
                ):
                    locations_template = env.get_template(
                        metadata.resource_pages['literary_analysis_locations']
                    )
                    locations_html = locations_template.render(work=work)
                    locations_path = output / (
                        f'literary_analysis_locations.{work.id}.html'
                    )
                    locations_path.write_text(locations_html)
                if (
                    work.literary_analysis.characters
                    and 'literary_analysis_characters'
                    in metadata.resource_pages
                ):
                    characters_template = env.get_template(
                        metadata.resource_pages['literary_analysis_characters']
                    )
                    characters_html = characters_template.render(work=work)
                    characters_path = output / (
                        f'literary_analysis_characters.{work.id}.html'
                    )
                    characters_path.write_text(characters_html)

    # Work editions
    if 'work_edition' in metadata.resource_pages:
        for work_edition in db.get_work_editions():
            template = env.get_template(metadata.resource_pages['work_edition'])
            html = template.render(work_edition=work_edition)
            out_path = output / f'{work_edition.id}.html'
            out_path.write_text(html)

    # Collections
    if 'collection' in metadata.resource_pages:
        for collection in db.get_book_collections():
            template = env.get_template(metadata.resource_pages['collection'])
            html = template.render(collection=collection)
            out_path = output / f'{collection.id}.html'
            out_path.write_text(html)

    # Lists
    if 'list' in metadata.resource_pages:
        for lst in db.get_reading_lists():
            template = env.get_template(metadata.resource_pages['list'])
            html = template.render(list=lst)
            out_path = output / f'{lst.id}.html'
            out_path.write_text(html)

    # Series
    if 'series' in metadata.resource_pages:
        for series in db.get_series():
            template = env.get_template(metadata.resource_pages['series'])
            html = template.render(series=series)
            out_path = output / f'{series.id}.html'
            out_path.write_text(html)

    # Reading sessions
    if 'reading_session' in metadata.resource_pages:
        for reading_session in db.get_reading_sessions():
            template = env.get_template(
                metadata.resource_pages['reading_session']
            )
            html = template.render(reading_session=reading_session)
            out_path = output / f'{reading_session.id}.html'
            out_path.write_text(html)
