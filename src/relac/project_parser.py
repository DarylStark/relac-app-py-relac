"""Module with the ProjectParser."""

from collections.abc import Callable
from pathlib import Path

from ruamel.yaml import YAML

from relac.model import (
    Author,
    Book,
    BookCollection,
    Label,
    ResourceBase,
    ResourceList,
    Work,
    WorkEdition,
)


class ProjectParser:
    """Parses a directory of YAML files into a working project."""

    def __init__(self, working_directory: Path) -> None:
        """Set the values."""
        self._working_dir = working_directory
        self._data_authors: dict[str, Author] = {}
        self._data_works: dict[str, Work] = {}
        self._data_work_editions: dict[str, WorkEdition] = {}
        self._data_books: dict[str, Book] = {}
        self._data_book_collections: dict[str, BookCollection] = {}
        self._data_labels: dict[str, Label] = {}
        self._data_resource_lists: dict[str, ResourceList] = {}

    def get_authors(self) -> dict[str, Author]:
        """Retrieve a list of authors in the memory database."""
        return self._data_authors

    def get_works(self) -> dict[str, Work]:
        """Retrieve a list of works in the memory database."""
        return self._data_works

    def get_work_editions(self) -> dict[str, WorkEdition]:
        """Retrieve a list of work auditions in the memory database."""
        return self._data_work_editions

    def get_books(self) -> dict[str, Book]:
        """Retrieve a list of books in the memory database."""
        return self._data_books

    def get_book_collections(self) -> dict[str, BookCollection]:
        """Retrieve a list of book collections in the memory database."""
        return self._data_book_collections

    def get_labels(self) -> dict[str, Label]:
        """Retrieve a list of labels in the memory database."""
        return self._data_labels

    def get_resource_lists(self) -> dict[str, ResourceList]:
        """Retrieve a list of ResourceLists in the memory database."""
        return self._data_resource_lists

    def parse(self) -> None:
        """Parse the directory."""
        all_yaml_files = self._find_all_yaml_files()
        combined_yaml = self._combine_yaml(all_yaml_files)
        self._parse_yaml_str(combined_yaml)

        pass

    def _find_all_yaml_files(self) -> list[Path]:
        """Find all YAML files in the working directory."""
        return [
            path
            for pattern in ('*.yaml', '*.yml')
            for path in self._working_dir.rglob(pattern)
            if path.is_file()
        ]

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

        object_parsers: dict[str, Callable[[str, dict[str, str]], None]] = {
            'author': self._parse_author_object,
            'work': self._parse_work_object,
            'work_edition': self._parse_work_edition_object,
            'book': self._parse_book_object,
            'collection': self._parse_collection_object,
            'label': self._parse_label_object,
            'resource_list': self._parse_resource_list_object,
        }

        for obj_id, obj in raw_data.items():
            if not isinstance(obj_id, str) or obj_id.startswith('_'):
                continue

            obj_type = obj_id.split('.')[0]
            parser = object_parsers.get(obj_type)
            if not parser:
                # TODO: custom Exception
                raise ValueError(f'Object type "{obj_type}" invalid')

            parser(obj_id, obj)

    def _parse_object[ResourceModel: ResourceBase](
        self,
        model: type[ResourceModel],
        data_dict: dict[str, ResourceModel],
        obj_id: str,
        obj: dict[str, str],
    ) -> None:
        """Generic method to parse data."""
        if obj_id in data_dict:
            raise ValueError(f'Object with it "{obj_id}" already exists.')
        data_dict[obj_id] = model.model_validate(obj)

    def _parse_author_object(self, obj_id: str, obj: dict[str, str]) -> None:
        """Parse an raw author object into a Author object."""
        self._parse_object(Author, self._data_authors, obj_id, obj)

    def _parse_work_object(self, obj_id: str, obj: dict[str, str]) -> None:
        """Parse an raw work object into a Work object."""
        self._parse_object(Work, self._data_works, obj_id, obj)

    def _parse_work_edition_object(
        self, obj_id: str, obj: dict[str, str]
    ) -> None:
        """Parse an raw work edition object into a WorkEdition object."""
        self._parse_object(WorkEdition, self._data_work_editions, obj_id, obj)

    def _parse_book_object(self, obj_id: str, obj: dict[str, str]) -> None:
        """Parse an raw book object into a Book object."""
        self._parse_object(Book, self._data_books, obj_id, obj)

    def _parse_collection_object(
        self, obj_id: str, obj: dict[str, str]
    ) -> None:
        """Parse an raw collection object into a BookCollection object."""
        self._parse_object(
            BookCollection, self._data_book_collections, obj_id, obj
        )

    def _parse_label_object(self, obj_id: str, obj: dict[str, str]) -> None:
        """Parse an raw label object into a Label object."""
        self._parse_object(Label, self._data_labels, obj_id, obj)

    def _parse_resource_list_object(
        self, obj_id: str, obj: dict[str, str]
    ) -> None:
        """Parse an raw resource list object into a ResourceList object."""
        self._parse_object(ResourceList, self._data_resource_lists, obj_id, obj)
