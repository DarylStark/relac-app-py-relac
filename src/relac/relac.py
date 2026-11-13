"""Module with the Relac class."""

import json
import shutil
from importlib import import_module
from pathlib import Path
from typing import cast

from jinja2 import Environment, FileSystemLoader

from relac.database import Database
from relac.model import (
    Book,
    BookCollection,
    Character,
    Contributor,
    Label,
    LintingFinding,
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
from .data_importer import DataImporter
from .repo_loader import RepoLoader


class Relac:
    """Facade class for the application."""

    def __init__(self, repo_loader: RepoLoader) -> None:
        """Configure the class."""
        self._repo_loader = repo_loader
        self._database = Database()
        self._importer = DataImporter(self._database)

    def import_data(self) -> None:
        """Import the data into the database."""
        objects = self._repo_loader.retrieve_objects()
        self._importer.import_data(objects)
        self._database.resolve_all()

    @property
    def database(self) -> Database:
        """Property for the database."""
        return self._database

    def lint_repo(self) -> list[LintingFinding]:
        """Get all linting findings for all objects."""
        findings: list[LintingFinding] = []
        for resource in self.database.get_all_values_for_all_types():
            findings.extend(resource.linting_findings)
        return findings

    def _build_search_index(
        self,
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

        for resource in self.database.get_all_values_for_all_types():
            add_entry(resource.get_search_index_data())

        return {'items': entries}

    def create_static_webpage(self, theme_module: str, output: Path) -> None:  # noqa: PLR0912, PLR0915
        """Create static HTML page."""
        theme_obj = import_module(theme_module)
        metadata = getattr(theme_obj, 'relac_theme', None)
        if not metadata or not isinstance(metadata, RelacTheme):
            # TODO: Custom exception
            raise TypeError(
                f'Module "{theme_module}" has no "relac_theme" object.'
            )

        output.mkdir(parents=True, exist_ok=True)
        (output / 'search-index.json').write_text(
            json.dumps(self._build_search_index(), ensure_ascii=False),
            encoding='utf-8',
        )

        env = Environment(loader=FileSystemLoader(metadata.source_dir))
        env.filters['isbn'] = _format_isbn
        env.filters['markdown'] = _render_markdown
        env.filters['enum_label'] = _format_enum_label
        env.filters['age'] = _calculate_age
        env.filters['language'] = _code_to_language
        env.filters['country'] = _code_to_country
        cast(dict[str, object], env.globals)['config'] = (
            self.database.get_relac_config()
        )

        # Copy static folder
        if metadata.static_folder:
            source = metadata.static_folder
            shutil.copytree(source, output / source.name, dirs_exist_ok=True)

        # Index page
        template = env.get_template(metadata.index_template)
        html = template.render(db=self.database)
        out_path = output / 'index.html'
        out_path.write_text(html)

        index_pages = {
            'books': Book,
            'works': Work,
            'work_editions': WorkEdition,
            'series': Series,
            'contributors': Contributor,
            'characters': Character,
            'locations': Location,
            'labels': Label,
            'owners': Owner,
            'collections': BookCollection,
            'lists': ReadingList,
            'reading_sessions': ReadingSession,
        }

        # Add index pages
        for index_page, obj_type in index_pages.items():
            if index_page in metadata.index_pages:
                template = env.get_template(metadata.index_pages[index_page])
                html = template.render(
                    **{index_page: self.database.get_all_values(obj_type)}
                )
                out_path = output / f'{index_page.replace("_", "-")}.html'
                out_path.write_text(html)

        # Add detail pages
        detail_pages = {
            'book': Book,
            'work_edition': WorkEdition,
            'series': Series,
            'contributor': Contributor,
            'character': Character,
            'location': Location,
            'label': Label,
            'owner': Owner,
            'collection': BookCollection,
            'list': ReadingList,
            'reading_session': ReadingSession,
        }

        for detail_page, obj_type in detail_pages.items():
            if detail_page in metadata.resource_pages:
                for resource in self.database.get_all_values(obj_type):
                    if resource.id is None:
                        continue

                    template = env.get_template(
                        metadata.resource_pages[detail_page]
                    )
                    html = template.render(
                        **{detail_page: self.database.get_one(resource.id)}
                    )
                    out_path = output / f'{resource.id}.html'
                    out_path.write_text(html)

        # Works
        if 'work' in metadata.resource_pages:
            reading_lists = self.database.get_all_values(ReadingList)
            for work in self.database.get_all_values(Work):
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
                    work.work_summary
                    or work.work_analysis
                    or work.structure
                    or (work.setting and work.setting.time_period)
                ) and 'literary_analysis' in metadata.resource_pages:
                    analysis_template = env.get_template(
                        metadata.resource_pages['literary_analysis']
                    )
                    analysis_html = analysis_template.render(work=work)
                    analysis_path = output / f'literary_analysis.{work.id}.html'
                    analysis_path.write_text(analysis_html)

                if (
                    work.chapters
                    and 'literary_analysis_chapter' in metadata.resource_pages
                ):
                    chapter_template = env.get_template(
                        metadata.resource_pages['literary_analysis_chapter']
                    )
                    for chapter in work.chapters:
                        chapter_html = chapter_template.render(
                            work=work, chapter=chapter
                        )
                        chapter_path = output / (
                            f'literary_analysis_chapter.{work.id}.'
                            f'{chapter.page_id}.html'
                        )
                        chapter_path.write_text(chapter_html)

                if (
                    work.setting
                    and work.setting.location_objs
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
                    work.characters or work.narrator
                ) and 'literary_analysis_characters' in metadata.resource_pages:
                    characters_template = env.get_template(
                        metadata.resource_pages['literary_analysis_characters']
                    )
                    characters_html = characters_template.render(work=work)
                    characters_path = output / (
                        f'literary_analysis_characters.{work.id}.html'
                    )
                    characters_path.write_text(characters_html)

                if (
                    work.motifs
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
                    work.quote_objs
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
