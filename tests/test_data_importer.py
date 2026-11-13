"""Tests for the DataImporter class."""

import pytest

from relac.data_importer import DataImporter
from relac.database import Database
from relac.exceptions import DuplicateIdError, UnknownObjectTypeError
from relac.model import Book, Contributor


def test_importing_contributors() -> None:
    """Test if we can import a contributor."""
    db = Database()
    importer = DataImporter(db)
    importer.import_data(
        {'contributor.john_williams': {'name': 'John Williams'}}
    )

    in_db = db.get_all(Contributor)

    assert len(in_db) == 1
    assert in_db['contributor.john_williams'].name == 'John Williams'


def test_importing_books() -> None:
    """Test if we can import a book."""
    db = Database()
    importer = DataImporter(db)
    importer.import_data({'book.stoner': {'title': 'Stoner'}})

    in_db = db.get_all(Book)

    assert len(in_db) == 1
    assert in_db['book.stoner'].title == 'Stoner'


def test_importing_multiple_contributors() -> None:
    """Test if we can import mulitple contributor."""
    db = Database()
    importer = DataImporter(db)
    importer.import_data(
        {
            'contributor.john_williams': {'name': 'John Williams'},
            'contributor.george_orwell': {'name': 'George Orwell'},
        }
    )

    in_db = db.get_all(Contributor)

    assert len(in_db) == 2
    assert in_db['contributor.john_williams'].name == 'John Williams'
    assert in_db['contributor.george_orwell'].name == 'George Orwell'


def test_importing_double_id() -> None:
    """Test if we get an error when importing the same id twice."""
    db = Database()
    importer = DataImporter(db)
    importer.import_data(
        {'contributor.john_williams': {'name': 'John Williams'}}
    )
    with pytest.raises(DuplicateIdError):
        importer.import_data(
            {'contributor.john_williams': {'name': 'John Williams'}}
        )


def test_importing_unknown_model() -> None:
    """Test if we get an error when importing a unknown model."""
    db = Database()
    importer = DataImporter(db)
    with pytest.raises(UnknownObjectTypeError):
        importer.import_data(
            {'non_existing_object.john_williams': {'name': 'John Williams'}}
        )
