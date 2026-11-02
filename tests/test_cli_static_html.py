"""Tests for static HTML template helpers."""

from datetime import date

from relac.cli_static_html import _build_search_index, _calculate_age
from relac.database import Database
from relac.model import Author, Book


def test_calculate_age_before_birthday() -> None:
    """Do not count the current year before the birthday."""
    assert _calculate_age(date(1980, 7, 15), date(2026, 6, 20)) == 45


def test_calculate_age_on_birthday() -> None:
    """Count the new age on the birthday."""
    assert _calculate_age(date(1980, 7, 15), date(2026, 7, 15)) == 46


def test_calculate_age_at_death() -> None:
    """Calculate a deceased author's age at the death date."""
    assert _calculate_age(date(1980, 7, 15), date(2020, 7, 14)) == 39


def test_calculate_age_without_birthdate() -> None:
    """Do not show an age when the birthdate is unknown."""
    assert _calculate_age(None, date(2026, 7, 15)) is None


def test_build_search_index_includes_book_metadata_and_url() -> None:
    """Include a book's ID, related author, ISBN, and generated page URL."""
    database = Database()
    author = Author(id='jane_doe', name='Jane Doe')
    book = Book(
        id='glass_hotel',
        isbn13=9781982137984,
        title='The Glass Hotel',
        author_objs=[author],
    )
    database.add_author('jane_doe', author)
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
