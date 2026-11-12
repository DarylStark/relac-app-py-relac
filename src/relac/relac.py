"""Module with the Relac class."""

from .data_importer import DataImporter
from .relac_database import RelacDatabase
from .repo_loader import RepoLoader


class Relac:
    """Facade class for the application."""

    def __init__(self, repo_loader: RepoLoader) -> None:
        """Configure the class."""
        self._repo_loader = repo_loader
        self._database = RelacDatabase()
        self._importer = DataImporter(self._database)

    def import_data(self) -> None:
        """Import the data into the database."""
        objects = self._repo_loader.retrieve_objects()
        self._importer.import_data(objects)
        self._database.resolve_all()

    @property
    def database(self) -> RelacDatabase:
        """Property for the database."""
        return self._database
