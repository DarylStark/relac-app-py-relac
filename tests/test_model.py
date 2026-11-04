"""Tests for model-derived properties."""

from datetime import date, timedelta

import pytest

from relac.model import (
    Author,
    Availability,
    Book,
    Owner,
    OwnerType,
    ReadingList,
    ReadingListItem,
    ReadingSession,
    ReadingState,
    ResourceAvailability,
    Series,
    SeriesItem,
    Work,
    WorkEdition,
)


@pytest.mark.parametrize(
    ('state', 'startdate', 'enddate', 'expected'),
    [
        (
            ReadingState.READING,
            date(2025, 1, 1),
            date(2025, 1, 8),
            timedelta(days=7),
        ),
        (ReadingState.PAUSED, date(2025, 1, 1), None, None),
        (ReadingState.READING, None, date(2025, 1, 8), None),
        (ReadingState.PAUSED, None, None, None),
    ],
)
def test_reading_session_duration(
    state: ReadingState,
    startdate: date | None,
    enddate: date | None,
    expected: timedelta | None,
) -> None:
    """Return the date difference only when both session dates are known."""
    session = ReadingSession(
        work_edition='test_edition',
        book='test_book',
        state=state,
        startdate=startdate,
        enddate=enddate,
    )

    assert session.duration == expected


def test_reading_session_uses_today_for_open_reading_session() -> None:
    """Use today as the end date for an active reading session."""
    today = date.today()
    session = ReadingSession(
        work_edition='test_edition',
        book='test_book',
        state=ReadingState.READING,
        startdate=today - timedelta(days=5),
    )

    assert session.effective_enddate == today
    assert session.duration == timedelta(days=5)


def test_work_reading_sessions_aggregate_from_editions() -> None:
    """Expose reading sessions from every work edition."""
    sessions = [
        ReadingSession(
            work_edition='edition-1',
            book='book-1',
            state=ReadingState.READING,
        ),
        ReadingSession(
            work_edition='edition-2',
            book='book-2',
            state=ReadingState.FINISHED,
        ),
    ]
    work = Work(
        title='Test Work',
        authors=[],
        edition_objs=[
            WorkEdition(
                title=f'Edition {index}',
                work='test_work',
                reading_session_objs=[session],
            )
            for index, session in enumerate(sessions, start=1)
        ],
    )

    assert work.reading_session_objs == sessions


@pytest.mark.parametrize(
    ('states', 'expected'),
    [
        ([], 0.0),
        ([ReadingState.FINISHED, ReadingState.READING], 50.0),
        ([ReadingState.FINISHED, ReadingState.FINISHED], 100.0),
    ],
)
def test_reading_list_read_percentage(
    states: list[ReadingState], expected: float
) -> None:
    """Calculate the percentage of listed works that have been finished."""
    works = []
    for index, state in enumerate(states):
        edition = WorkEdition(
            title=f'Edition {index}',
            work=f'work-{index}',
            reading_session_objs=(
                [
                    ReadingSession(
                        work_edition=f'edition-{index}',
                        book='book',
                        state=state,
                    )
                ]
                if state is not ReadingState.NOT_READ
                else []
            ),
        )
        work = Work(
            title=f'Work {index}',
            authors=[],
            edition_objs=[edition],
        )
        works.append(
            ReadingListItem(
                order=index,
                work=f'work-{index}',
                work_obj=work,
            )
        )

    reading_list = ReadingList(name='Test list', works=works)

    assert reading_list.read_percentage == expected


def test_series_reading_counts_and_percentage() -> None:
    """Count works by reading state and calculate the finished percentage."""
    states = [
        ReadingState.FINISHED,
        ReadingState.READING,
        ReadingState.PAUSED,
        ReadingState.DID_NOT_FINISH,
        ReadingState.NOT_READ,
    ]
    works = []
    for index, state in enumerate(states):
        edition = WorkEdition(
            title=f'Edition {index}',
            work=f'work-{index}',
            reading_session_objs=(
                []
                if state is ReadingState.NOT_READ
                else [
                    ReadingSession(
                        work_edition=f'edition-{index}',
                        book='book',
                        state=state,
                    )
                ]
            ),
        )
        work = Work(
            title=f'Work {index}',
            authors=[],
            edition_objs=[edition],
        )
        works.append(
            SeriesItem(
                number=index,
                work=f'work-{index}',
                work_obj=work,
            )
        )

    series = Series(name='Test series', works=works)

    assert series.read_count == 1
    assert series.reading_count == 1
    assert series.paused_count == 1
    assert series.dnf_count == 1
    assert series.not_read_count == 1
    assert series.read_percentage == 20.0
    assert Series(name='Empty series').read_percentage == 0.0


def test_book_reading_counts_deduplicate_works() -> None:
    """Count each linked Work once, even when the book has multiple editions."""
    states = [
        ReadingState.FINISHED,
        ReadingState.READING,
        ReadingState.PAUSED,
        ReadingState.DID_NOT_FINISH,
        ReadingState.NOT_READ,
    ]
    editions = []
    for index, state in enumerate(states):
        edition = WorkEdition(
            title=f'Edition {index}',
            work=f'work-{index}',
            reading_session_objs=(
                []
                if state is ReadingState.NOT_READ
                else [
                    ReadingSession(
                        work_edition=f'edition-{index}',
                        book='test_book',
                        state=state,
                    )
                ]
            ),
        )
        work = Work(
            title=f'Work {index}',
            authors=[],
            edition_objs=[edition],
        )
        edition.work_obj = work
        editions.append(edition)

    editions.append(
        WorkEdition(
            title='Another edition of the finished work',
            work='work-0',
            work_obj=editions[0].work_obj,
        )
    )
    book = Book(
        isbn13=9781234567897,
        title='Test Book',
        work_edition_objs=editions,
    )

    assert book.read_count == 1
    assert book.reading_count == 1
    assert book.paused_count == 1
    assert book.dnf_count == 1
    assert book.not_read_count == 1
    assert book.read_percentage == 20.0


def test_author_reading_counts_and_percentage() -> None:
    """Count author works by reading state and calculate finished percentage."""
    states = [
        ReadingState.FINISHED,
        ReadingState.READING,
        ReadingState.PAUSED,
        ReadingState.DID_NOT_FINISH,
        ReadingState.NOT_READ,
    ]
    works = []
    for index, state in enumerate(states):
        edition = WorkEdition(
            title=f'Edition {index}',
            work=f'work-{index}',
            reading_session_objs=(
                []
                if state is ReadingState.NOT_READ
                else [
                    ReadingSession(
                        work_edition=f'edition-{index}',
                        book='book',
                        state=state,
                    )
                ]
            ),
        )
        works.append(
            Work(
                title=f'Work {index}',
                authors=[],
                edition_objs=[edition],
            )
        )

    author = Author(name='Test Author', work_objs=works)

    assert author.read_count == 1
    assert author.reading_count == 1
    assert author.paused_count == 1
    assert author.dnf_count == 1
    assert author.not_read_count == 1
    assert author.read_percentage == 20.0
    assert Author(name='Empty Author').read_percentage == 0.0


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
