"""Tests for model-derived properties."""

import pytest

from relac.model import (
    Availability,
    Book,
    Owner,
    WorkEdition,
)


@pytest.mark.parametrize(
    ('owner_availabilities', 'expected'),
    [
        ([], Availability.NOT_AVAILABLE),
        ([Availability.NOT_AVAILABLE], Availability.NOT_AVAILABLE),
        (
            [Availability.INDIRECTLY_AVAILABLE],
            Availability.INDIRECTLY_AVAILABLE,
        ),
        (
            [
                Availability.INDIRECTLY_AVAILABLE,
                Availability.DIRECTLY_AVAILABLE,
            ],
            Availability.DIRECTLY_AVAILABLE,
        ),
    ],
)
def test_book_availability(
    owner_availabilities: list[Availability], expected: Availability
) -> None:
    """Aggregate owner availability with direct access taking precedence."""
    book = Book(
        isbn13=9781234567897,
        title='Test Book',
        owner_objs=[
            Owner(name=str(index), availability=availability)
            for index, availability in enumerate(owner_availabilities)
        ],
    )

    assert book.availability is expected


def test_work_edition_availability_uses_book_availability() -> None:
    """Aggregate book availability with direct access taking precedence."""
    edition = WorkEdition(
        title='Test Edition',
        work='test_work',
        book_objs=[
            Book(
                isbn13=9781234567897,
                title='Indirect Book',
                owner_objs=[
                    Owner(
                        name='Library',
                        availability=Availability.INDIRECTLY_AVAILABLE,
                    )
                ],
            ),
            Book(
                isbn13=9781234567898,
                title='Direct Book',
                owner_objs=[
                    Owner(
                        name='Shelf',
                        availability=Availability.DIRECTLY_AVAILABLE,
                    )
                ],
            ),
        ],
    )

    assert edition.availability is Availability.DIRECTLY_AVAILABLE
