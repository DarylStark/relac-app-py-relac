"""Tests for the DataImporter class."""

import pytest

from relac.data_importer import DataImporter
from relac.database import Database
from relac.exceptions import DuplicateIdError, UnknownObjectTypeError
from relac.model import Book, BookOwner, Contributor, Owner


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


def test_importing_book_owners_with_legacy_and_detailed_data() -> None:
    """Import and resolve both simple and detailed book-owner relationships."""
    db = Database()
    importer = DataImporter(db)
    importer.import_data(
        {
            'owner.daryl': {'name': 'Daryl'},
            'owner.library': {'name': 'Library'},
            'book.stoner': {
                'title': 'Stoner',
                'owners': [
                    'owner.daryl',
                    {
                        'owner': 'owner.library',
                        'since': '2024-05-01',
                        'loaned_to': 'owner.daryl',
                        'loaned_on': '2024-10-01',
                        'due_date': '2024-10-15',
                        'link': {
                            'title': 'Loan record',
                            'url': 'https://example.com/loan',
                        },
                    },
                ],
            },
        }
    )

    db.resolve_all()

    book = db.get_all(Book)['book.stoner']
    owner = db.get_all(Owner)['owner.library']
    borrower = db.get_all(Owner)['owner.daryl']
    detailed_ownership = book.owners[1]
    legacy_loan = detailed_ownership.loans[0]

    assert isinstance(book.owners[0], BookOwner)
    assert book.owners[0].owner_obj is db.get_all(Owner)['owner.daryl']
    assert detailed_ownership.since is not None
    assert detailed_ownership.since.isoformat() == '2024-05-01'
    assert legacy_loan.loaned_to == 'owner.daryl'
    assert legacy_loan.loaned_to_obj is borrower
    assert legacy_loan.loaned_on is not None
    assert legacy_loan.loaned_on.isoformat() == '2024-10-01'
    assert legacy_loan.due_date is not None
    assert legacy_loan.due_date.isoformat() == '2024-10-15'
    assert detailed_ownership.link is not None
    assert detailed_ownership.link.title == 'Loan record'
    assert detailed_ownership.link.url == 'https://example.com/loan'
    assert detailed_ownership.owner_obj is owner
    assert book.owner_objs == [book.owners[0].owner_obj, owner]
    assert owner.book_objs == [book]


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
