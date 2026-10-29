"""Tests for the ProjectParser."""

from pathlib import Path

from relac.database import Database
from relac.project_parser import ProjectParser


def test_parsing_directory() -> None:
    """Parse a directory and test for the correct project details."""
    database = Database()
    parser = ProjectParser(Path('tests/simple_project/'), database)
    parser.parse()
    database.converge()

    assert len(database.get_authors()) == 4
    assert len(database.get_works()) == 11
    assert len(database.get_work_editions()) == 12
    assert len(database.get_books()) == 7
    assert len(database.get_book_publishers()) == 4
    assert len(database.get_book_collections()) == 2
    assert len(database.get_labels()) == 0
    assert len(database.get_resource_lists()) == 1

    pass
