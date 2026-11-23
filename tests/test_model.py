"""Tests for the Relac Model."""

import pytest

from relac.exceptions import DoubleModelNameError
from relac.model import (
    Book,
    ReadingList,
    ReadingListItem,
    ReadingSession,
    ReadingState,
    ResourceBase,
    Work,
    WorkEdition,
    WorkEditionType,
    register_model,
)


def test_book_counts_read_abridged_work_edition() -> None:
    """An abridged edition counts as read for its containing book."""
    work = Work(id='work.test', title='Test Work', authors=[])
    edition = WorkEdition(
        id='work_edition.test',
        title='Abridged Edition',
        work='work.test',
        edition_type=WorkEditionType.ABRIGED,
        work_obj=work,
        reading_session_objs=[
            ReadingSession(
                work_edition='work_edition.test',
                book='book.test',
                state=ReadingState.FINISHED,
            )
        ],
    )
    work.edition_objs.append(edition)
    book = Book(
        id='book.test',
        title='Test Book',
        work_edition_objs=[edition],
    )

    assert work.reading_state == ReadingState.NOT_READ
    assert book.read_count == 1
    assert book.read_percentage == 100


def test_book_does_not_count_abridged_edition_in_another_book() -> None:
    """Abridged reading only counts for a book containing that edition."""
    work = Work(id='work.test', title='Test Work', authors=[])
    read_edition = WorkEdition(
        id='work_edition.read',
        title='Abridged Edition',
        work='work.test',
        edition_type=WorkEditionType.ABRIGED,
        work_obj=work,
        reading_session_objs=[
            ReadingSession(
                work_edition='work_edition.read',
                book='book.read',
                state=ReadingState.FINISHED,
            )
        ],
    )
    unread_edition = WorkEdition(
        id='work_edition.unread',
        title='Unread Edition',
        work='work.test',
        work_obj=work,
    )
    work.edition_objs.extend([read_edition, unread_edition])
    book = Book(
        id='book.unread',
        title='Unread Book',
        work_edition_objs=[unread_edition],
    )

    assert work.reading_state == ReadingState.NOT_READ
    assert book.read_count == 0
    assert book.not_read_count == 1


def test_reading_list_combines_inherited_work_orders() -> None:
    """Append inherited lists after local and preceding inherited works."""
    first_inherited = ReadingList(
        id='reading_list.first',
        name='First inherited list',
        works=[
            ReadingListItem(order=1, work='work.first'),
            ReadingListItem(order=2, work='work.second'),
        ],
    )
    second_inherited = ReadingList(
        id='reading_list.second',
        name='Second inherited list',
        works=[ReadingListItem(order=1, work='work.third')],
    )
    reading_list = ReadingList(
        id='reading_list.combined',
        name='Combined list',
        works=[
            ReadingListItem(order=3, work='work.local'),
            ReadingListItem(work='work.local_without_order'),
        ],
        inherit_objs=[first_inherited, second_inherited],
    )

    assert [item.order for item in reading_list.works] == [3, 4]
    assert [item.work for item in reading_list.combined_works] == [
        'work.local',
        'work.local_without_order',
        'work.first',
        'work.second',
        'work.third',
    ]
    assert [item.order for item in reading_list.combined_works] == [
        3,
        4,
        5,
        6,
        7,
    ]


def test_reading_list_cycle_is_linted_and_does_not_recurse_forever() -> None:
    """Ignore a repeated ancestor during expansion and report the cycle."""
    first = ReadingList(id='reading_list.first', name='First')
    second = ReadingList(
        id='reading_list.second',
        name='Second',
        works=[ReadingListItem(work='work.second')],
        inherit_objs=[first],
    )
    first.inherit_objs.append(second)

    assert first.combined_works == second.combined_works
    assert any(
        finding.id == 'reading-list-inheritance-cycle'
        for finding in first.linting_findings
    )


def test_book_counts_non_abridged_edition_read_in_another_book() -> None:
    """A non-abridged edition read elsewhere marks the work as read."""
    work = Work(id='work.test', title='Test Work', authors=[])
    translation = WorkEdition(
        id='work_edition.translation',
        title='Translated Edition',
        work='work.test',
        edition_type=WorkEditionType.TRANSLATION,
        work_obj=work,
        reading_session_objs=[
            ReadingSession(
                work_edition='work_edition.translation',
                book='book.translation',
                state=ReadingState.FINISHED,
            )
        ],
    )
    original = WorkEdition(
        id='work_edition.original',
        title='Original Edition',
        work='work.test',
        edition_type=WorkEditionType.ORIGINAL,
        work_obj=work,
    )
    work.edition_objs.extend([translation, original])
    book = Book(
        id='book.original',
        title='Original Book',
        work_edition_objs=[original],
    )

    assert work.reading_state == ReadingState.FINISHED
    assert book.read_count == 1


def test_register_model_with_double_model() -> None:
    """Test if we get an error when registering a double model name."""

    class MyModel(ResourceBase): ...

    register_model('test_model')(MyModel)

    with pytest.raises(DoubleModelNameError):
        register_model('test_model')(MyModel)
