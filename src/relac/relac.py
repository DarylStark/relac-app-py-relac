"""Module with the Relac class."""

from pathlib import Path

from .database import Database
from .project_parser import ProjectParser


class Relac:
    """Facade class for the application."""

    def __init__(self, project_path: Path) -> None:
        """Configure the class."""
        self._project_path = project_path
        self._database = Database()
        self._configure()

    def _configure(self) -> None:
        """Configure the application."""
        self._parser = ProjectParser(self._project_path, self._database)
        self._parser.parse()
        self._database.converge()

    @property
    def database(self) -> Database:
        """Property for the database."""
        return self._database
