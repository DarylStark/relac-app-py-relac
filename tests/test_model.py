"""Tests for model-derived properties."""

from datetime import date, timedelta

import pytest

from relac.database import Database
from relac.model import (
    Availability,
    Book,
    BookCollection,
    Contributor,
    LiteraryAnalysis,
    Location,
    Owner,
    OwnerType,
    ReadingList,
    ReadingListItem,
    ReadingSession,
    ReadingState,
    RelacConfig,
    ResourceAvailability,
    Series,
    SeriesItem,
    StorySetting,
    Work,
    WorkEdition,
)


def test_book_collection_owned_percentage() -> None:
    """Calculate the share of collection books owned by a given owner."""
    library_owner = Owner(id='library', name='Library')
    owned_book = Book(
        id='owned_book',
        isbn13=9780000000001,
        title='Owned',
        owner_objs=[library_owner],
    )
    other_book = Book(
        id='other_book',
        isbn13=9780000000002,
        title='Other',
    )
    collection = BookCollection(
        id='collection',
        name='Collection',
        book_objs=[owned_book, other_book],
    )

    assert collection.owned_percentage(library_owner) == 50.0
    assert (
        BookCollection(id='empty', name='Empty').owned_percentage(library_owner)
        == 0.0
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


def test_work_edition_resolves_illustrators_and_translators() -> None:
    """Resolve optional edition contributor IDs to Contributor objects."""
    database = Database()
    database.set_relac_config(RelacConfig(title='Test Library'))
    author = Contributor(id='author', name='Author')
    illustrator = Contributor(id='illustrator', name='Illustrator')
    translator = Contributor(id='translator', name='Translator')
    work = Work(id='work', title='Test Work', authors=['author'])
    edition = WorkEdition(
        id='edition',
        title='Test Edition',
        work='work',
        illustrators=['illustrator'],
        translators=['translator'],
    )
    book = Book(
        id='book',
        isbn13=9781234567897,
        title='Test Book',
        work_editions=['edition'],
    )

    database.add_contributor('author', author)
    database.add_contributor('illustrator', illustrator)
    database.add_contributor('translator', translator)
    database.add_work('work', work)
    database.add_work_edition('edition', edition)
    database.add_book('book', book)
    database.converge()

    assert edition.illustrator_objs == [illustrator]
    assert edition.translator_objs == [translator]
    assert work.author_objs == [author]
    assert illustrator.illustrator_work_edition_objs == [edition]
    assert translator.translator_work_edition_objs == [edition]
    assert author.book_objs == [book]
    assert illustrator.book_objs == [book]
    assert translator.book_objs == [book]
    assert book.contributor_objs == [author, illustrator, translator]


def test_work_edition_contributors_are_optional() -> None:
    """Allow editions without illustrator or translator lists."""
    edition = WorkEdition(title='Test Edition', work='test_work')

    assert edition.illustrators is None
    assert edition.translators is None


def test_location_resolves_related_works() -> None:
    """Expose every work that references a location in its story setting."""
    database = Database()
    database.set_relac_config(RelacConfig(title='Test Library'))
    shared_location = Location(id='shared', name='Shared location')
    unused_location = Location(id='unused', name='Unused location')
    works = [
        Work(
            id=f'work-{index}',
            title=f'Work {index}',
            authors=[],
            literary_analysis=LiteraryAnalysis(
                setting=StorySetting(locations=['shared'])
            ),
        )
        for index in range(2)
    ]

    database.add_location('shared', shared_location)
    database.add_location('unused', unused_location)
    for work in works:
        database.add_work(work.id, work)  # ty: ignore[invalid-argument-type]
    database.converge()

    assert len(shared_location.work_objs) == 2
    assert all(
        related_work is work
        for related_work, work in zip(
            shared_location.work_objs, works, strict=True
        )
    )
    assert unused_location.work_objs == []


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


def test_contributor_reading_counts_and_percentage() -> None:
    """Count contributor works by reading state and calculate percentage."""
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

    contributor = Contributor(name='Test Contributor', work_objs=works)

    assert contributor.read_count == 1
    assert contributor.reading_count == 1
    assert contributor.paused_count == 1
    assert contributor.dnf_count == 1
    assert contributor.not_read_count == 1
    assert contributor.read_percentage == 20.0
    assert Contributor(name='Empty Contributor').read_percentage == 0.0


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
