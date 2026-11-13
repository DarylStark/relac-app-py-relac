"""Tests for the YamlRepoLoader class."""

from pathlib import Path

import pytest

from relac.exceptions import YamlLoadingError
from relac.yaml_repo_loader import YamlRepoLoader


def test_find_all_yaml_files(simple_project_folder: Path) -> None:
    """Test if all Yaml files are found."""
    loader = YamlRepoLoader(repo_path=simple_project_folder)
    all_yaml_files = loader.discover_files()

    # Check if we have the needed files
    assert simple_project_folder / 'clothbound_classics.yml' in all_yaml_files
    assert simple_project_folder / 'no_isbn.yaml' in all_yaml_files

    # Check if we miss files that we should miss
    assert simple_project_folder / 'stoner_ch1_analyse.md' not in all_yaml_files
    assert simple_project_folder / '_templates.yaml' not in all_yaml_files


def test_includes_on_correct_directory(
    include_tests_folder_correct: Path,
) -> None:
    """Test if the YamlRepoLoader include functionality works."""
    loader = YamlRepoLoader(repo_path=include_tests_folder_correct)
    loader.retrieve_objects()


def test_duplicate_key_error(
    yaml_parse_test_folder_duplicate_key: Path,
) -> None:
    """Test if we get an error when importing a duplicate key."""
    loader = YamlRepoLoader(repo_path=yaml_parse_test_folder_duplicate_key)
    with pytest.raises(YamlLoadingError):
        loader.retrieve_objects()


def test_retrieving_objects(simple_project_folder: Path) -> None:
    """Test retrieving objects from a "real" project."""
    loader = YamlRepoLoader(repo_path=simple_project_folder)
    objects = loader.retrieve_objects()
    assert 'contributor.john_williams' in objects
    assert 'relac' in objects
    assert 'owner.daryl' in objects


def test_duplicate_keys(yaml_parse_test_folder_duplicate_keys: Path) -> None:
    """Test if we get an err when there are duplicate keys in multiple files."""
    loader = YamlRepoLoader(repo_path=yaml_parse_test_folder_duplicate_keys)
    with pytest.raises(YamlLoadingError):
        loader.retrieve_objects()
