"""Tests for the parser."""

from pathlib import Path

from relac.database import Database
from relac.project_parser import ProjectParser


def test_inject_files_loads_contents_recursively(tmp_path: Path) -> None:
    """Test injection."""
    file_contents = {
        'description.md': 'Description content',
        'summary.md': 'Summary content',
        'first.md': 'First item content',
        'analysis.md': 'Analysis content',
    }
    for filename, contents in file_contents.items():
        (tmp_path / filename).write_text(contents, encoding='utf-8')

    parser = ProjectParser(tmp_path, Database())
    data: dict[str, object] = {
        'description': '[file:description.md]',
        'nested': {'summary': '[file:summary.md]'},
        'items': [
            '[file:first.md]',
            {'analysis': '[file:analysis.md]'},
            'keep',
        ],
    }

    parser.inject_files(data)

    assert data == {
        'description': 'Description content',
        'nested': {'summary': 'Summary content'},
        'items': [
            'First item content',
            {'analysis': 'Analysis content'},
            'keep',
        ],
    }
