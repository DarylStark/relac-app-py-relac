"""Tests for the ProjectParser."""

from pathlib import Path

from relac.database import Database
from relac.project_parser import ProjectParser


def test_parsing_directory() -> None:
    """Parse a directory and test for the correct project details."""
    database = Database()
    parser = ProjectParser(Path('tests/simple_project/'), database)
    parser.parse()

    assert len(database.get_authors()) == 2
    assert len(database.get_works()) == 5
    assert len(database.get_work_editions()) == 9
    assert len(database.get_books()) == 3
    assert len(database.get_book_publishers()) == 2
    assert len(database.get_book_collections()) == 1
    assert len(database.get_labels()) == 0
    assert len(database.get_resource_lists()) == 0
