"""Module with the DataImporter class."""

from typing import Any

from .model import ResourceBase, relac_models
from .relac_database import RelacDatabase


class DataImporter:
    """Imports data from a `data` dictionary into the database."""

    def __init__(self, database: RelacDatabase) -> None:
        """Set values."""
        self._database = database

    def _parse_object[ResourceModel: ResourceBase](
        self,
        model: type[ResourceModel],
        obj: dict[str, Any],
    ) -> ResourceModel:
        """Generic method to parse data."""
        return model.model_validate(obj, extra='forbid')

    def import_data(self, data: dict[str, dict]) -> None:
        """Import data from a dict into the database."""
        for obj_id, obj_data in data.items():
            obj_type = obj_id.split('.', maxsplit=1)[0]
            model = relac_models.get(obj_type)
            if not model:
                # TODO: Custom exception
                raise ValueError(f'Unknown object type: "{obj_type}".')

            obj = self._parse_object(model, obj_data)
            self._database.add_object(obj_id, obj)
