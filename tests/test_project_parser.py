"""Tests for the ProjectParser."""

from pathlib import Path

from relac.database import Database
from relac.project_parser import ProjectParser


def test_parsing_directory() -> None:
    """Parse a directory and test for the correct project details."""
    database = Database()
    parser = ProjectParser(Path('tests/simple_project/'), database)
    parser.parse()

    book = next(
        book
        for book in database.get_books()
        if book.id == 'book.stephen_king__if_it_bleeds'
    )
    book.work_editions.append(
        'work_edition.stephen_king__mr_harrigans_phone__nl'
    )
    database.converge()

    assert len(database.get_authors()) == 4
    assert len(database.get_works()) == 11
    assert len(database.get_work_editions()) == 12
    assert len(database.get_books()) == 7
    assert len(database.get_book_publishers()) == 4
    assert len(database.get_book_collections()) == 2
    assert len(database.get_labels()) == 0
    assert len(database.get_resource_lists()) == 1

    work = next(
        work
        for work in database.get_works()
        if work.id == 'work.stephen_king__mr_harrigans_phone'
    )
    assert {book.id for book in work.book_objs} == {
        'book.stephen_king__als_het_bloedt',
        'book.stephen_king__if_it_bleeds',
    }
    assert len(work.book_objs) == 2
