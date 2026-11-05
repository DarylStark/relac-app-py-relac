"""Tests for static HTML template helpers."""

from datetime import date

import pytest

from relac.cli_static_html import (
    _build_search_index,
    _calculate_age,
    _format_enum_label,
)
from relac.database import Database
from relac.model import (
    Availability,
    Book,
    Contributor,
    Owner,
    OwnerType,
    ResourceAvailability,
    Series,
)


def test_calculate_age_before_birthday() -> None:
    """Do not count the current year before the birthday."""
    assert _calculate_age(date(1980, 7, 15), date(2026, 6, 20)) == 45


def test_calculate_age_on_birthday() -> None:
    """Count the new age on the birthday."""
    assert _calculate_age(date(1980, 7, 15), date(2026, 7, 15)) == 46


def test_calculate_age_at_death() -> None:
    """Calculate a deceased contributor's age at the death date."""
    assert _calculate_age(date(1980, 7, 15), date(2020, 7, 14)) == 39


def test_calculate_age_without_birthdate() -> None:
    """Do not show an age when the birthdate is unknown."""
    assert _calculate_age(None, date(2026, 7, 15)) is None


@pytest.mark.parametrize(
    ('availability', 'expected'),
    [
        (ResourceAvailability.UNAVAILABLE, 'Unavailable'),
        (ResourceAvailability.AVAILABLE_DIRECT, 'Available'),
        (ResourceAvailability.AVAILABLE_INDIRECT, 'Available (indirect)'),
        (ResourceAvailability.AVAILABLE_TO_LOAN, 'Available to loan'),
        (ResourceAvailability.AVAILABLE_TO_BUY, 'Available to buy'),
    ],
)
def test_resource_availability_labels(
    availability: ResourceAvailability, expected: str
) -> None:
    """Format the new resource availability values for display."""
    assert _format_enum_label(availability.value) == expected


def test_build_search_index_includes_book_metadata_and_url() -> None:
    """Include a book's ID, related author, ISBN, and generated page URL."""
    database = Database()
    contributor = Contributor(id='jane_doe', name='Jane Doe')
    book = Book(
        id='glass_hotel',
        isbn13=9781982137984,
        title='The Glass Hotel',
        author_objs=[contributor],
    )
    database.add_contributor('jane_doe', contributor)
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

    contributor_entry = next(
        item
        for item in _build_search_index(database)['items']
        if item['type'] == 'Contributor'
    )
    assert contributor_entry['href'] == 'jane_doe.html'
    assert contributor_entry['title'] == 'Jane Doe'


def test_build_search_index_includes_owner_metadata_and_url() -> None:
    """Include an owner's type, availability, books, and page URL."""
    database = Database()
    book = Book(
        id='glass_hotel',
        isbn13=9781982137984,
        title='The Glass Hotel',
    )
    owner = Owner(
        id='city_library',
        name='City Library',
        owner_type=OwnerType.LIBRARY,
        availability=Availability.INDIRECTLY_AVAILABLE,
        book_objs=[book],
    )
    database.add_owner('city_library', owner)

    owner_entry = next(
        item
        for item in _build_search_index(database)['items']
        if item['type'] == 'Owner'
    )

    assert owner_entry['href'] == 'city_library.html'
    assert owner_entry['title'] == 'City Library'
    assert 'Library' in owner_entry['searchText']
    assert 'Indirectly' in owner_entry['searchText']
    assert 'The Glass Hotel' in owner_entry['searchText']

    owner_without_books = Owner(id='local_store', name='Local Store')
    database.add_owner('local_store', owner_without_books)
    index = _build_search_index(database)['items']
    store_entry = next(
        item for item in index if item['href'] == 'local_store.html'
    )
    assert not any(
        detail.startswith('Books:') for detail in store_entry['details']
    )


def test_build_search_index_includes_series_and_url() -> None:
    """Include series names and generated detail page URLs."""
    database = Database()
    series = Series(id='the_housemaid', name='The Housemaid')
    database.add_series('the_housemaid', series)

    series_entry = next(
        item
        for item in _build_search_index(database)['items']
        if item['type'] == 'Series'
    )

    assert series_entry['href'] == 'the_housemaid.html'
    assert series_entry['title'] == 'The Housemaid'
    assert 'The Housemaid' in series_entry['searchText']
