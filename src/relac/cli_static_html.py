"""`static_html` part of the CLI application."""

import json
import shutil
from importlib import import_module
from pathlib import Path
from typing import cast

from jinja2 import Environment, FileSystemLoader
from typer import Context, Option, Typer

from relac.database import Database
from relac.model import (
    Book,
    BookCollection,
    Character,
    Contributor,
    Label,
    Location,
    Owner,
    ReadingList,
    ReadingSession,
    SearchIndexData,
    Series,
    Work,
    WorkEdition,
)
from relac.theme import RelacTheme

from .data_helpers import (
    _calculate_age,
    _code_to_country,
    _code_to_language,
    _format_enum_label,
    _format_isbn,
    _render_markdown,
)


def _build_search_index(  # noqa: PLR0912
    db: Database,
) -> dict[str, list[dict[str, str | list[str]]]]:
    """Build the client-side search data for every linked resource."""
    entries: list[dict[str, str | list[str]]] = []

    def add_entry(data: SearchIndexData) -> None:
        if data.resource_id is None:
            return

        if data.labels:
            details = [*data.details, f'Labels: {", ".join(data.labels)}']
        else:
            details = data.details

        terms = [
            data.resource_type,
            data.resource_id,
            data.title,
            *details,
            *(data.search_terms or []),
        ]
        entries.append(
            {
                'type': data.resource_type,
                'title': data.title,
                'href': f'{data.resource_id}.html',
                'details': details,
                'searchText': ' '.join(terms),
            }
        )
        for extra_data in data.extra_data or []:
            add_entry(extra_data)

    for resource in db.get_all_values_for_all_types():
        add_entry(resource.get_search_index_data())

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
    db: Database = ctx.obj.database

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
    env.filters['isbn'] = _format_isbn
    env.filters['markdown'] = _render_markdown
    env.filters['enum_label'] = _format_enum_label
    env.filters['age'] = _calculate_age
    env.filters['language'] = _code_to_language
    env.filters['country'] = _code_to_country
    cast(dict[str, object], env.globals)['config'] = db.get_relac_config()

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
            books=db.get_all_values(Book),
        )
        out_path = output / 'books.html'
        out_path.write_text(html)

    if 'works' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['works'])
        html = template.render(
            works=db.get_all_values(Work),
        )
        out_path = output / 'works.html'
        out_path.write_text(html)

    if 'work_editions' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['work_editions'])
        html = template.render(
            work_editions=db.get_all_values(WorkEdition),
        )
        out_path = output / 'work-editions.html'
        out_path.write_text(html)

    if 'series' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['series'])
        html = template.render(
            series=db.get_all_values(Series),
        )
        out_path = output / 'series.html'
        out_path.write_text(html)

    if 'contributors' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['contributors'])
        html = template.render(
            contributors=db.get_all_values(Contributor),
        )
        out_path = output / 'contributors.html'
        out_path.write_text(html)

    if 'characters' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['characters'])
        html = template.render(characters=db.get_all_values(Character))
        out_path = output / 'characters.html'
        out_path.write_text(html)

    if 'locations' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['locations'])
        html = template.render(locations=db.get_all_values(Location))
        out_path = output / 'locations.html'
        out_path.write_text(html)

    if 'labels' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['labels'])
        html = template.render(
            labels=db.get_all_values(Label),
        )
        out_path = output / 'labels.html'
        out_path.write_text(html)

    if 'owners' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['owners'])
        html = template.render(
            owners=db.get_all_values(Owner),
        )
        out_path = output / 'owners.html'
        out_path.write_text(html)

    if 'collections' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['collections'])
        html = template.render(
            collections=db.get_all_values(BookCollection),
        )
        out_path = output / 'collections.html'
        out_path.write_text(html)

    if 'lists' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['lists'])
        html = template.render(
            lists=db.get_all_values(ReadingList),
        )
        out_path = output / 'lists.html'
        out_path.write_text(html)

    if 'reading_sessions' in metadata.index_pages:
        template = env.get_template(metadata.index_pages['reading_sessions'])
        html = template.render(
            reading_sessions=db.get_all_values(ReadingSession),
        )
        out_path = output / 'reading-sessions.html'
        out_path.write_text(html)

    # Books
    if 'book' in metadata.resource_pages:
        for book in db.get_all_values(Book):
            template = env.get_template(metadata.resource_pages['book'])
            html = template.render(book=book)
            out_path = output / f'{book.id}.html'
            out_path.write_text(html)

    # Contributors
    if 'contributor' in metadata.resource_pages:
        for contributor in db.get_all_values(Contributor):
            template = env.get_template(metadata.resource_pages['contributor'])
            html = template.render(contributor=contributor)
            out_path = output / f'{contributor.id}.html'
            out_path.write_text(html)

    # Locations
    if 'location' in metadata.resource_pages:
        for location in db.get_all_values(Location):
            template = env.get_template(metadata.resource_pages['location'])
            html = template.render(location=location)
            out_path = output / f'{location.id}.html'
            out_path.write_text(html)

    # Characters
    if 'character' in metadata.resource_pages:
        for character in db.get_all_values(Character):
            template = env.get_template(metadata.resource_pages['character'])
            html = template.render(character=character)
            out_path = output / f'{character.id}.html'
            out_path.write_text(html)

    # Labels
    if 'label' in metadata.resource_pages:
        for label in db.get_all_values(Label):
            template = env.get_template(metadata.resource_pages['label'])
            html = template.render(label=label)
            out_path = output / f'{label.id}.html'
            out_path.write_text(html)

    # Owners
    if 'owner' in metadata.resource_pages:
        for owner in db.get_all_values(Owner):
            template = env.get_template(metadata.resource_pages['owner'])
            html = template.render(owner=owner)
            out_path = output / f'{owner.id}.html'
            out_path.write_text(html)

    # Works
    if 'work' in metadata.resource_pages:
        reading_lists = db.get_all_values(ReadingList)
        for work in db.get_all_values(Work):
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
                            f'{chapter.page_id}.html'
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
                if (
                    work.literary_analysis.motifs
                    and 'literary_analysis_motifs' in metadata.resource_pages
                ):
                    motifs_template = env.get_template(
                        metadata.resource_pages['literary_analysis_motifs']
                    )
                    motifs_html = motifs_template.render(work=work)
                    motifs_path = output / (
                        f'literary_analysis_motifs.{work.id}.html'
                    )
                    motifs_path.write_text(motifs_html)
                if (
                    work.literary_analysis.quote_objs
                    and 'literary_analysis_quotes' in metadata.resource_pages
                ):
                    quotes_template = env.get_template(
                        metadata.resource_pages['literary_analysis_quotes']
                    )
                    quotes_html = quotes_template.render(work=work)
                    quotes_path = output / (
                        f'literary_analysis_quotes.{work.id}.html'
                    )
                    quotes_path.write_text(quotes_html)

    # Work editions
    if 'work_edition' in metadata.resource_pages:
        for work_edition in db.get_all_values(WorkEdition):
            template = env.get_template(metadata.resource_pages['work_edition'])
            html = template.render(work_edition=work_edition)
            out_path = output / f'{work_edition.id}.html'
            out_path.write_text(html)

    # Collections
    if 'collection' in metadata.resource_pages:
        for collection in db.get_all_values(BookCollection):
            template = env.get_template(metadata.resource_pages['collection'])
            html = template.render(collection=collection)
            out_path = output / f'{collection.id}.html'
            out_path.write_text(html)

    # Lists
    if 'list' in metadata.resource_pages:
        for lst in db.get_all_values(ReadingList):
            template = env.get_template(metadata.resource_pages['list'])
            html = template.render(list=lst)
            out_path = output / f'{lst.id}.html'
            out_path.write_text(html)

    # Series
    if 'series' in metadata.resource_pages:
        for series in db.get_all_values(Series):
            template = env.get_template(metadata.resource_pages['series'])
            html = template.render(series=series)
            out_path = output / f'{series.id}.html'
            out_path.write_text(html)

    # Reading sessions
    if 'reading_session' in metadata.resource_pages:
        for reading_session in db.get_all_values(ReadingSession):
            template = env.get_template(
                metadata.resource_pages['reading_session']
            )
            html = template.render(reading_session=reading_session)
            out_path = output / f'{reading_session.id}.html'
            out_path.write_text(html)
