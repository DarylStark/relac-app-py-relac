"""Tests for the database."""

from datetime import date
from typing import ClassVar

import pytest

from relac.database import Database, DataStore
from relac.exceptions import (
    DuplicateIdError,
    ObjectNotFoundError,
    RelacConfigNotSetError,
    UnknownObjectTypeAddedError,
    UnknownObjectTypeRequestedError,
)
from relac.model import (
    Availability,
    Book,
    BookOwner,
    BookOwnerLoan,
    Character,
    Contributor,
    Label,
    Owner,
    OwnerType,
    RelacConfig,
    ResolvableField,
    ResourceAvailability,
    ResourceBase,
    Work,
    WorkCharacter,
    WorkEdition,
)


def test_adding_one_contributor() -> None:
    """Test if we can add one contributor."""
    db = Database()
    contrib_id = 'contributor.testcontrib'
    contrib = Contributor(name='TestContrib')

    db.add_object(contrib_id, contrib)

    contribs = db.get_all(Contributor)
    assert len(contribs) == 1
    assert contribs[contrib_id].name == 'TestContrib'


def test_adding_more_contributors() -> None:
    """Test if we can add more then one contributor."""
    db = Database()

    for idx in range(0, 10):
        contrib_id = f'contributor.testcontrib_{idx}'
        contrib = Contributor(name=f'TestContrib_{idx}')
        db.add_object(contrib_id, contrib)

    contribs = db.get_all(Contributor)
    assert len(contribs) == 10
    assert contribs['contributor.testcontrib_1'].name == 'TestContrib_1'


def test_adding_more_contribs_same_id() -> None:
    """Test if we can add more then one contributor with the same id.

    Should raise an error
    """
    db = Database()
    contrib_id = 'contributor.testcontrib'
    contrib = Contributor(name='TestContrib')

    db.add_object(contrib_id, contrib)

    with pytest.raises(DuplicateIdError):
        db.add_object(contrib_id, contrib)


def test_resolving_fields_many_to_many() -> None:
    """Test if we can resolve fields."""

    class IncorrectModel(ResourceBase): ...

    db = Database()
    db.add_object('label.test_label_1', Label(name='test_label_1'))
    db.add_object('label.test_label_2', Label(name='test_label_2'))
    db.add_object('label.test_label_3', Label(name='test_label_3'))
    db.add_object(
        'contributor.john_williams',
        Contributor(
            name='test_label',
            labels=[
                'label.test_label_1',
                'label.test_label_2',
                'label.test_label_3',
            ],
        ),
    )
    db.resolve_all()

    contributors = db.get_all(Contributor)
    assert len(contributors['contributor.john_williams'].label_objs) == 3
    assert (
        contributors['contributor.john_williams'].label_objs[0].name
        == 'test_label_1'
    )

    labels = db.get_all(Label)
    assert len(labels['label.test_label_1'].contributor_objs) == 1


def test_resolving_fields_one_to_many() -> None:
    """Test if one-to-many fields resolve in both directions."""

    class QuoteReference(ResourceBase):
        contributor: str
        contributor_obj: Contributor | None = None
        resolvable_fields: ClassVar[list[ResolvableField]] = [
            ResolvableField(
                'contributor',
                'contributor_obj',
                'one-to-many',
                'quote_objs',
            )
        ]

    db = Database()
    contributor = Contributor(name='TestContrib', labels=[])
    quote = QuoteReference(contributor='contributor.testcontrib')
    db.add_object('contributor.testcontrib', contributor)
    quotes = DataStore[QuoteReference]()
    quotes.add('quote.testquote', quote)

    quotes.resolve_all(db)

    assert quote.contributor_obj is contributor
    assert contributor.quote_objs == [quote]


def test_resolving_nested_work_character_relationships() -> None:
    """Resolve character IDs and the owning work for nested appearances."""
    db = Database()
    character = Character(id='character.test', name='Test Character')
    work_character = WorkCharacter(character='character.test')
    work = Work(
        id='work.test',
        title='Test Work',
        authors=[],
        characters=[work_character],
    )
    db.add_object('character.test', character)
    db.add_object('work.test', work)

    db.resolve_all()

    assert work_character.character_obj is character
    assert work_character.work_obj is work
    assert character.work_objs == [work]
    assert character.work_character_objs == [work_character]


def test_work_books_are_derived_from_its_editions() -> None:
    """Include each book containing any edition of the work, only once."""
    db = Database()
    work = Work(
        id='work.test',
        title='Test Work',
        authors=[],
    )
    first_edition = WorkEdition(
        id='work_edition.test.first',
        title='First Edition',
        work='work.test',
    )
    second_edition = WorkEdition(
        id='work_edition.test.second',
        title='Second Edition',
        work='work.test',
    )
    shared_book = Book(
        id='book.shared',
        title='Shared Book',
        work_editions=[
            'work_edition.test.first',
            'work_edition.test.second',
        ],
    )
    other_book = Book(
        id='book.other',
        title='Other Book',
        work_editions=['work_edition.test.second'],
    )
    for obj_id, obj in (
        ('work.test', work),
        ('work_edition.test.first', first_edition),
        ('work_edition.test.second', second_edition),
        ('book.shared', shared_book),
        ('book.other', other_book),
    ):
        db.add_object(obj_id, obj)

    db.resolve_all()

    assert work.book_objs == [shared_book, other_book]


def test_book_availability_uses_active_loan_recipient() -> None:
    """Include the current borrower when aggregating book availability."""
    db = Database()
    library = Owner(
        name='Library',
        owner_type=OwnerType.LIBRARY,
        availability=Availability.DIRECTLY_AVAILABLE,
    )
    borrower = Owner(
        name='Borrower',
        owner_type=OwnerType.PERSON,
        availability=Availability.DIRECTLY_AVAILABLE,
    )
    book = Book(
        id='book.test',
        title='Test Book',
        work_editions=['work_edition.test'],
        owners=[
            BookOwner(
                owner='owner.library',
                loans=[BookOwnerLoan(loaned_to='owner.borrower')],
            )
        ],
    )
    work = Work(
        id='work.test',
        title='Test Work',
        authors=[],
    )
    edition = WorkEdition(
        id='work_edition.test',
        title='Test Edition',
        work='work.test',
    )
    db.add_object('owner.library', library)
    db.add_object('owner.borrower', borrower)
    db.add_object('book.test', book)
    db.add_object('work.test', work)
    db.add_object('work_edition.test', edition)
    returned_book = Book(
        id='book.returned',
        title='Returned Book',
        owners=[
            BookOwner(
                owner='owner.library',
                loans=[
                    BookOwnerLoan(
                        loaned_to='owner.borrower',
                        returned_on=date(2026, 1, 15),
                    )
                ],
            )
        ],
    )
    db.add_object('book.returned', returned_book)

    db.resolve_all()

    assert book.availability == ResourceAvailability.AVAILABLE_DIRECT
    assert edition.availability == ResourceAvailability.AVAILABLE_DIRECT
    assert work.availability == ResourceAvailability.AVAILABLE_DIRECT
    assert returned_book.availability == ResourceAvailability.AVAILABLE_TO_LOAN


def test_retrieving_invalid_relac_config() -> None:
    """Test if we get an error when retrieving invalid RelacConfig."""
    db = Database()
    with pytest.raises(RelacConfigNotSetError):
        db.get_relac_config()


def test_retrieving_invalid_relac_id() -> None:
    """Test if we get an error when retrieving invalid RelacConfig."""
    db = Database()
    db.add_object('relac.wrong_id', RelacConfig(title='test_config'))
    with pytest.raises(RelacConfigNotSetError):
        db.get_relac_config()


def test_retrieving_valid_relac_config() -> None:
    """Test if we get the correct RelacConfig."""
    db = Database()
    db.add_object('relac', RelacConfig(title='test_config'))
    config = db.get_relac_config()
    assert config.title == 'test_config'


def test_adding_invalid_object_type() -> None:
    """Test if we get an error when adding a invalid object type."""

    class TestClass(ResourceBase): ...

    db = Database()
    with pytest.raises(UnknownObjectTypeAddedError):
        db.add_object('testclass.test', TestClass())


def test_retrieving_invalid_object_type() -> None:
    """Test if we get an error when retrieving invalid object types."""
    db = Database()
    with pytest.raises(UnknownObjectTypeRequestedError):
        db.get_one('testclass.test')


def test_retrieving_non_existing_object() -> None:
    """Test if we get an error when retrieving a non-existing object."""
    db = Database()
    with pytest.raises(ObjectNotFoundError):
        db.get_one('contributor.non_existing')
