"""Tests for the ReadingSession Specifications."""

from datetime import date

import pytest

from relac.model import (
    AllResourceSpec,
    AnyResourceSpec,
    FinishedAfterReadingSessionSpec,
    FinishedBeforeReadingSessionSpec,
    IsFinishedReadingSessionSpec,
    ReadingSession,
    ReadingState,
    StartedAfterReadingSessionSpec,
    StartedBeforeReadingSessionSpec,
)


def test_valid_is_finished_reading_spec() -> None:
    """Test a finished reading session specification."""
    session = ReadingSession(
        work_edition='work_edition.test',
        book='book.test',
        state=ReadingState.FINISHED,
    )
    assert IsFinishedReadingSessionSpec().is_satisfied_by(session)


@pytest.mark.parametrize(
    'state',
    [
        ReadingState.DID_NOT_FINISH,
        ReadingState.NOT_READ,
        ReadingState.PAUSED,
        ReadingState.READING,
    ],
)
def test_invalid_is_finished_reading_spec(state: ReadingState) -> None:
    """Test a not-finished reading session specification."""
    session = ReadingSession(
        work_edition='work_edition.test',
        book='book.test',
        state=state,
    )
    assert not IsFinishedReadingSessionSpec().is_satisfied_by(session)


def test_valid_started_after_spec() -> None:
    """Test a reading session started after specification."""
    session = ReadingSession(
        work_edition='work_edition.test',
        book='book.test',
        state=ReadingState.FINISHED,
        startdate=date(2026, 1, 1),
    )
    assert StartedAfterReadingSessionSpec(
        date=date(2026, 1, 1)
    ).is_satisfied_by(session)


def test_invalid_started_after_spec() -> None:
    """Test a not-finished before reading specification."""
    session = ReadingSession(
        work_edition='work_edition.test',
        book='book.test',
        state=ReadingState.FINISHED,
        startdate=date(2025, 1, 1),
    )
    assert not StartedAfterReadingSessionSpec(
        date=date(2026, 1, 1)
    ).is_satisfied_by(session)


def test_invalid_started_after_spec_none() -> None:
    """Test a not-finished before reading specification."""
    session = ReadingSession(
        work_edition='work_edition.test',
        book='book.test',
        state=ReadingState.FINISHED,
    )
    assert not StartedAfterReadingSessionSpec(
        date=date(2026, 1, 1)
    ).is_satisfied_by(session)


def test_valid_started_before_spec() -> None:
    """Test a reading session started after specification."""
    session = ReadingSession(
        work_edition='work_edition.test',
        book='book.test',
        state=ReadingState.FINISHED,
        startdate=date(2025, 12, 1),
    )
    assert StartedBeforeReadingSessionSpec(
        date=date(2026, 1, 1)
    ).is_satisfied_by(session)


def test_invalid_started_before_spec() -> None:
    """Test a not-finished before reading specification."""
    session = ReadingSession(
        work_edition='work_edition.test',
        book='book.test',
        state=ReadingState.FINISHED,
        startdate=date(2026, 3, 1),
    )
    assert not StartedBeforeReadingSessionSpec(
        date=date(2026, 1, 1)
    ).is_satisfied_by(session)


def test_invalid_started_before_spec_none() -> None:
    """Test a not-finished before reading specification."""
    session = ReadingSession(
        work_edition='work_edition.test',
        book='book.test',
        state=ReadingState.FINISHED,
    )
    assert not StartedBeforeReadingSessionSpec(
        date=date(2026, 1, 1)
    ).is_satisfied_by(session)


def test_valid_finished_before_spec() -> None:
    """Test a finished before reading session specification."""
    session = ReadingSession(
        work_edition='work_edition.test',
        book='book.test',
        state=ReadingState.FINISHED,
        enddate=date(2026, 1, 1),
    )
    assert FinishedBeforeReadingSessionSpec(
        date=date(2026, 12, 31)
    ).is_satisfied_by(session)


def test_invalid_finished_before_spec() -> None:
    """Test a not-finished before reading specification."""
    session = ReadingSession(
        work_edition='work_edition.test',
        book='book.test',
        state=ReadingState.FINISHED,
        enddate=date(2027, 1, 1),
    )
    assert not FinishedBeforeReadingSessionSpec(
        date=date(2026, 12, 31)
    ).is_satisfied_by(session)


def test_invalid_finished_before_spec_none() -> None:
    """Test a not-finished before reading specification."""
    session = ReadingSession(
        work_edition='work_edition.test',
        book='book.test',
        state=ReadingState.FINISHED,
    )
    assert not FinishedBeforeReadingSessionSpec(
        date=date(2026, 12, 31)
    ).is_satisfied_by(session)


def test_valid_finished_after_spec() -> None:
    """Test a finished before reading session specification."""
    session = ReadingSession(
        work_edition='work_edition.test',
        book='book.test',
        state=ReadingState.FINISHED,
        enddate=date(2026, 2, 1),
    )
    assert FinishedAfterReadingSessionSpec(
        date=date(2026, 1, 1)
    ).is_satisfied_by(session)


def test_invalid_finished_after_spec() -> None:
    """Test a not-finished before reading specification."""
    session = ReadingSession(
        work_edition='work_edition.test',
        book='book.test',
        state=ReadingState.FINISHED,
        enddate=date(2026, 1, 1),
    )
    assert not FinishedAfterReadingSessionSpec(
        date=date(2027, 12, 31)
    ).is_satisfied_by(session)


def test_invalid_finished_after_spec_none() -> None:
    """Test a not-finished before reading specification."""
    session = ReadingSession(
        work_edition='work_edition.test',
        book='book.test',
        state=ReadingState.FINISHED,
    )
    assert not FinishedAfterReadingSessionSpec(
        date=date(2026, 12, 31)
    ).is_satisfied_by(session)


def test_any_reading_session_spec() -> None:
    """Test the any specification with reading specs."""
    session = ReadingSession(
        work_edition='work_edition.test',
        book='book.test',
        state=ReadingState.FINISHED,
        enddate=date(2026, 5, 1),
    )

    spec_a = FinishedAfterReadingSessionSpec(date=date(2026, 1, 1))
    spec_b = FinishedBeforeReadingSessionSpec(date=date(2026, 1, 1))

    spec = AnyResourceSpec[ReadingSession](specs=[])
    spec.spec_objs = [spec_a, spec_b]

    assert spec.is_satisfied_by(session)


def test_all_reading_session_spec() -> None:
    """Test the any specification with reading specs."""
    session = ReadingSession(
        work_edition='work_edition.test',
        book='book.test',
        state=ReadingState.FINISHED,
        enddate=date(2026, 5, 1),
    )

    spec_a = FinishedAfterReadingSessionSpec(date=date(2026, 1, 1))
    spec_b = FinishedBeforeReadingSessionSpec(date=date(2026, 12, 31))

    spec = AllResourceSpec[ReadingSession](specs=[])
    spec.spec_objs = [spec_a, spec_b]

    assert spec.is_satisfied_by(session)
