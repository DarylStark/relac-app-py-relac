"""Module with the DataImporter class."""

from .relac_database import RelacDatabase


class DataImporter:
    """Imports data from a `data` dictionary into the database."""

    def __init__(self, database: RelacDatabase) -> None:
        """Set values."""
        self._database = database

    def import_data(self, data: dict[str, dict]) -> None:
        """Import data from a dict into the database."""
