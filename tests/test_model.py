"""Tests for the Relac Model."""

import pytest

from relac.exceptions import DoubleModelNameError
from relac.model import (
    Book,
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
