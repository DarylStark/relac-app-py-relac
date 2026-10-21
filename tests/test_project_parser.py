"""Tests for the ProjectParser."""

from pathlib import Path

from relac.project_parser import ProjectParser


def test_parsing_directory() -> None:
    """Parse a directory and test for the correct project details."""
    parser = ProjectParser(Path('tests/simple_project/'))
    parser.parse()

    assert len(parser.get_authors()) == 2
    assert len(parser.get_works()) == 5
    assert len(parser.get_work_editions()) == 9
    assert len(parser.get_books()) == 3
    assert len(parser.get_book_collections()) == 1
    assert len(parser.get_labels()) == 0
    assert len(parser.get_resource_lists()) == 0
