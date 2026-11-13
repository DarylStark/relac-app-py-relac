"""Module with fixtures for tests."""

from pathlib import Path

from pytest import fixture


@fixture(scope='session')
def simple_project_folder() -> Path:
    """Fixture for the path of the simple project folder."""
    return Path(__file__).parent / 'simple_project'


@fixture(scope='session')
def include_tests_folder_correct() -> Path:
    """Fixture for the path of a folder with include tests."""
    return Path(__file__).parent / 'include_tests' / 'correct'


@fixture(scope='session')
def include_tests_folder_incorrect_underscore() -> Path:
    """Fixture for the path of a folder with include tests."""
    return Path(__file__).parent / 'include_tests' / 'incorrect_underscore'


@fixture(scope='session')
def include_tests_folder_incorrect_nonexisting() -> Path:
    """Fixture for the path of a folder with include tests."""
    return Path(__file__).parent / 'include_tests' / 'incorrect_nonexisting'


@fixture(scope='session')
def yaml_parse_test_folder_duplicate_key() -> Path:
    """Fixture for the path of a folder with duplucate key tests."""
    return Path(__file__).parent / 'yaml_parse_tests' / 'duplicate_key'


@fixture(scope='session')
def yaml_parse_test_folder_duplicate_keys() -> Path:
    """Fixture for the path of a folder with duplicate keys text."""
    return Path(__file__).parent / 'duplicate_keys'
