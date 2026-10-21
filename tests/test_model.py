"""Tests for the mode."""

from relac.model import (
    Author,
    Book,
    BookCollection,
    BookPublisher,
    Label,
    ReadingSession,
    ResourceList,
    Work,
    WorkEdition,
)


def test_author_validation_valid() -> None:
    """Test the validation for a Author object."""
    resource = Author(name='Stephen King')
    assert resource.is_valid()


def test_author_validation_invalid() -> None:
    """Test the validation for a Author object."""
    resource = Author(name='  ')
    assert not resource.is_valid()


def test_work_validation_valid() -> None:
    """Test the validation for a Work object."""
    resource = Work(title='Stephen King')
    assert resource.is_valid()


def test_work_validation_invalid() -> None:
    """Test the validation for a Work object."""
    resource = Work(title='  ')
    assert not resource.is_valid()


def test_work_edition_validation_valid() -> None:
    """Test the validation for a Work object."""
    resource = WorkEdition(title='Stephen King')
    assert resource.is_valid()


def test_work_edition_validation_invalid() -> None:
    """Test the validation for a Work object."""
    resource = WorkEdition(title='  ')
    assert not resource.is_valid()


def test_book_collection_validation_valid() -> None:
    """Test the validation for a Work object."""
    resource = BookCollection(name='Penguin Classic Clothbound')
    assert resource.is_valid()


def test_book_collection_validation_invalid() -> None:
    """Test the validation for a Work object."""
    resource = BookCollection(name='  ')
    assert not resource.is_valid()


def test_book_publisher_validation_valid() -> None:
    """Test the validation for a Work object."""
    resource = BookPublisher(name='Penguin Classic Clothbound')
    assert resource.is_valid()


def test_book_publisher_validation_invalid() -> None:
    """Test the validation for a Work object."""
    resource = BookPublisher(name='  ')
    assert not resource.is_valid()


def test_book_validation_valid() -> None:
    """Test the validation for a Work object."""
    resource = Book(isbn13='9780241453513', title='Ninetheen Eightyfour')
    assert resource.is_valid()


def test_book_validation_invalid() -> None:
    """Test the validation for a Work object."""
    resource = Book(isbn13='9780241453513', title='  ')
    assert not resource.is_valid()


def test_label_validation_valid() -> None:
    """Test the validation for a Work object."""
    resource = Label(name='Highschool book')
    assert resource.is_valid()


def test_label_validation_invalid() -> None:
    """Test the validation for a Work object."""
    resource = Label(name='  ')
    assert not resource.is_valid()


def test_reading_session_validation_valid() -> None:
    """Test the validation for a Work object."""
    resource = ReadingSession()
    assert resource.is_valid()


def test_resource_list_validation_valid() -> None:
    """Test the validation for a Work object."""
    resource = ResourceList(name='Highschool book')
    assert resource.is_valid()


def test_resource_list_validation_invalid() -> None:
    """Test the validation for a Work object."""
    resource = ResourceList(name='  ')
    assert not resource.is_valid()
