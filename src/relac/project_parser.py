"""Module with the ProjectParser."""

from collections.abc import Callable
from pathlib import Path

from ruamel.yaml import YAML

from .database import Database
from .model import (
    Book,
    BookCollection,
    BookPublisher,
    Character,
    Contributor,
    Label,
    Location,
    Owner,
    ReadingList,
    ReadingSession,
    RelacConfig,
    ResourceBase,
    Series,
    Work,
    WorkEdition,
)


class ProjectParser:
    """Parses a directory of YAML files into a working project."""

    def __init__(self, working_directory: Path, database: Database) -> None:
        """Set the values."""
        self._working_dir = working_directory
        self._database = database

    def parse(self) -> None:
        """Parse the directory."""
        all_yaml_files = self._find_all_yaml_files()
        combined_yaml = self._combine_yaml(all_yaml_files)
        self._parse_yaml_str(combined_yaml)

    def _find_all_yaml_files(self) -> list[Path]:
        """Find all YAML files in the working directory."""
        files = [
            path
            for pattern in ('*.yaml', '*.yml')
            for path in self._working_dir.rglob(pattern)
            if path.is_file()
        ]
        # Files starting with an underscore (like templates with YAML anchors)
        # must come first, since anchors have to be defined before use.
        return sorted(files, key=lambda p: (not p.name.startswith('_'), str(p)))

    def _combine_yaml(self, yaml_files: list[Path]) -> str:
        """Combine a lot of YAML files into one file."""
        output_str = ''
        for yaml_file in yaml_files:
            output_str += '\n' + yaml_file.read_text(encoding='utf-8')
        output_str = output_str.replace('\n---\n', '')
        return output_str

    def _parse_yaml_str(self, yaml_data: str) -> None:
        """Parse one specific YAML file."""
        yaml = YAML(typ='safe')

        raw_data = yaml.load(yaml_data)

        object_parsers: dict[
            str, Callable[[str, dict[str, str]], ResourceBase]
        ] = {
            'contributor': self._parse_contributor_object,
            'work': self._parse_work_object,
            'work_edition': self._parse_work_edition_object,
            'book': self._parse_book_object,
            'collection': self._parse_collection_object,
            'label': self._parse_label_object,
            'reading_list': self._parse_reading_list_object,
            'publisher': self._parse_book_publisher_object,
            'owner': self._parse_owner_object,
            'series': self._parse_series_object,
            'reading_session': self._parse_reading_session_object,
            'location': self._parse_location_object,
            'character': self._parse_character_object,
        }

        for obj_id, obj in raw_data.items():
            if not isinstance(obj_id, str) or obj_id.startswith('_'):
                continue

            if obj_id == 'relac':
                self._parse_relac_object(obj)
                continue

            obj_type = obj_id.split('.')[0]
            parser = object_parsers.get(obj_type)
            if not parser:
                # TODO: custom Exception
                raise ValueError(f'Object type "{obj_type}" invalid')

            new_obj = parser(obj_id, obj)
            new_obj.id = obj_id

    def _parse_object[ResourceModel: ResourceBase](
        self,
        model: type[ResourceModel],
        obj: dict[str, str],
    ) -> ResourceModel:
        """Generic method to parse data."""
        return model.model_validate(obj, extra='forbid')

    def _parse_contributor_object(
        self, obj_id: str, data: dict[str, str]
    ) -> Contributor:
        """Parse a raw contributor object."""
        obj = self._parse_object(Contributor, data)
        self._database.add_contributor(obj_id, obj)
        return obj

    def _parse_work_object(self, obj_id: str, data: dict[str, str]) -> Work:
        """Parse an raw work object into a Work object."""
        obj = self._parse_object(Work, data)
        self._database.add_work(obj_id, obj)
        return obj

    def _parse_work_edition_object(
        self, obj_id: str, data: dict[str, str]
    ) -> WorkEdition:
        """Parse an raw work edition object into a WorkEdition object."""
        obj = self._parse_object(WorkEdition, data)
        self._database.add_work_edition(obj_id, obj)
        return obj

    def _parse_book_object(self, obj_id: str, data: dict[str, str]) -> Book:
        """Parse an raw book object into a Book object."""
        obj = self._parse_object(Book, data)
        self._database.add_book(obj_id, obj)
        return obj

    def _parse_book_publisher_object(
        self, obj_id: str, data: dict[str, str]
    ) -> BookPublisher:
        """Parse an raw book publisher object into a BookPublisher object."""
        obj = self._parse_object(BookPublisher, data)
        self._database.add_book_publisher(obj_id, obj)
        return obj

    def _parse_collection_object(
        self, obj_id: str, data: dict[str, str]
    ) -> BookCollection:
        """Parse an raw collection object into a BookCollection object."""
        obj = self._parse_object(BookCollection, data)
        self._database.add_book_collections(obj_id, obj)
        return obj

    def _parse_label_object(self, obj_id: str, data: dict[str, str]) -> Label:
        """Parse an raw label object into a Label object."""
        obj = self._parse_object(Label, data)
        self._database.add_label(obj_id, obj)
        return obj

    def _parse_reading_list_object(
        self, obj_id: str, data: dict[str, str]
    ) -> ReadingList:
        """Parse an raw reading list object into a ReadingList object."""
        obj = self._parse_object(ReadingList, data)
        self._database.add_reading_list(obj_id, obj)
        return obj

    def _parse_owner_object(self, obj_id: str, data: dict[str, str]) -> Owner:
        """Parse an raw owner object into a Owner object."""
        obj = self._parse_object(Owner, data)
        self._database.add_owner(obj_id, obj)
        return obj

    def _parse_series_object(self, obj_id: str, data: dict[str, str]) -> Series:
        """Parse an raw series object into a Series object."""
        obj = self._parse_object(Series, data)
        self._database.add_series(obj_id, obj)
        return obj

    def _parse_reading_session_object(
        self, obj_id: str, data: dict[str, str]
    ) -> ReadingSession:
        """Parse an raw reading session object into a ReadingSession object."""
        obj = self._parse_object(ReadingSession, data)
        self._database.add_reading_session(obj_id, obj)
        return obj

    def _parse_relac_object(self, data: dict[str, str]) -> RelacConfig:
        """Parse an raw relac object into a RelacConfig object."""
        obj = RelacConfig.model_validate(data, extra='forbid')
        self._database.set_relac_config(obj)
        return obj

    def _parse_location_object(
        self, obj_id: str, data: dict[str, str]
    ) -> Location:
        """Parse an raw location object into a Location object."""
        obj = self._parse_object(Location, data)
        self._database.add_location(obj_id, obj)
        return obj

    def _parse_character_object(
        self, obj_id: str, data: dict[str, str]
    ) -> Character:
        """Parse an raw character object into a Character object."""
        obj = self._parse_object(Character, data)
        self._database.add_character(obj_id, obj)
        return obj
