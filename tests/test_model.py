"""Tests for model-derived properties."""

import pytest

from relac.model import (
    Availability,
    Book,
    Owner,
    OwnerType,
    ResourceAvailability,
    Work,
    WorkEdition,
)


@pytest.mark.parametrize(
    ('owners', 'expected'),
    [
        ([], ResourceAvailability.UNAVAILABLE),
        (
            [
                (OwnerType.PERSON, Availability.NOT_AVAILABLE),
            ],
            ResourceAvailability.UNAVAILABLE,
        ),
        (
            [
                (OwnerType.PERSON, Availability.INDIRECTLY_AVAILABLE),
            ],
            ResourceAvailability.AVAILABLE_INDIRECT,
        ),
        (
            [
                (OwnerType.PERSON, Availability.DIRECTLY_AVAILABLE),
            ],
            ResourceAvailability.AVAILABLE_DIRECT,
        ),
        (
            [
                (OwnerType.LIBRARY, Availability.DIRECTLY_AVAILABLE),
            ],
            ResourceAvailability.AVAILABLE_TO_LOAN,
        ),
        (
            [
                (OwnerType.STORE, Availability.DIRECTLY_AVAILABLE),
            ],
            ResourceAvailability.AVAILABLE_TO_BUY,
        ),
        (
            [
                (OwnerType.LIBRARY, Availability.INDIRECTLY_AVAILABLE),
                (OwnerType.STORE, Availability.INDIRECTLY_AVAILABLE),
            ],
            ResourceAvailability.UNAVAILABLE,
        ),
    ],
)
def test_book_availability(
    owners: list[tuple[OwnerType, Availability]],
    expected: ResourceAvailability,
) -> None:
    """Aggregate availability from each owner's type and access level."""
    book = Book(
        isbn13=9781234567897,
        title='Test Book',
        owner_objs=[
            Owner(
                name=str(index),
                owner_type=owner_type,
                availability=availability,
            )
            for index, (owner_type, availability) in enumerate(owners)
        ],
    )

    assert book.availability is expected


def test_work_availability_uses_book_owners() -> None:
    """Aggregate availability from owners across the work's books."""
    work = Work(
        title='Test Work',
        authors=[],
        book_objs=[
            Book(
                isbn13=9781234567897,
                title='Indirect Book',
                owner_objs=[
                    Owner(
                        name='Person',
                        owner_type=OwnerType.PERSON,
                        availability=Availability.INDIRECTLY_AVAILABLE,
                    )
                ],
            ),
        ],
    )

    assert work.availability is ResourceAvailability.AVAILABLE_INDIRECT


def test_work_edition_availability_uses_book_owners() -> None:
    """Aggregate availability from owners across the edition's books."""
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
                        owner_type=OwnerType.LIBRARY,
                        availability=Availability.INDIRECTLY_AVAILABLE,
                    )
                ],
            ),
            Book(
                isbn13=9781234567898,
                title='Direct Book',
                owner_objs=[
                    Owner(
                        name='Library',
                        owner_type=OwnerType.LIBRARY,
                        availability=Availability.DIRECTLY_AVAILABLE,
                    )
                ],
            ),
        ],
    )

    assert edition.availability is ResourceAvailability.AVAILABLE_TO_LOAN
