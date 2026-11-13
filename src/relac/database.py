"""Module with the RelacDatabase class."""

from typing import cast

from relac.exceptions import (
    DuplicateIdError,
    ObjectNotFoundError,
    RelacConfigNotSetError,
    UnknownObjectTypeAddedError,
    UnknownObjectTypeRequestedError,
)
from relac.model import RelacConfig, ResolvableField, ResourceBase, relac_models


class DataStore[T: ResourceBase]:
    """Class that keeps data for the database."""

    def __init__(self) -> None:
        """Initialize empty database."""
        self._data: dict[str, T] = {}

    def add(self, obj_id: str, obj: T) -> None:
        """Add a object to the datastore."""
        if self._data.get(obj_id) is not None:
            raise DuplicateIdError(obj_id)

        self._data[obj_id] = obj

    def get_one(self, obj_id: str) -> T | None:
        """Retrieve one element from the store."""
        return self._data.get(obj_id)

    def get_all(self) -> dict[str, T]:
        """Retrieve all objects from the database."""
        return self._data

    def __len__(self) -> int:
        """Get the length of the store."""
        return len(self._data)

    def _resolve_item(
        self,
        item: ResourceBase,
        database: Database,
        parent_item: ResourceBase | None = None,
    ) -> None:
        """Resolve the resolvable items for a object."""
        for field in getattr(item, 'resolvable_parent_fields', ()):
            if parent_item is not None:
                setattr(item, field, parent_item)

        for field in getattr(item, 'resolvable_fields', []):
            self._resolve_field(item, field, database, parent_item)

        for obj in getattr(item, 'resolvable_children', []):
            values = getattr(item, obj)
            if not isinstance(values, list):
                values = [values]
            for obj_to_resolve in values:
                self._resolve_item(
                    obj_to_resolve,
                    database,
                    parent_item if parent_item else item,
                )

    def resolve_all(self, database: Database) -> None:
        """Resolve all fields in all objects."""
        items_with_resolvable = [
            v
            for v in self._data.values()
            if 'resolvable_fields' in dir(v) or 'resolvable_children' in dir(v)
        ]
        for item in items_with_resolvable:
            self._resolve_item(item, database)

    def _resolve_field_one_to_many(
        self,
        item: ResourceBase,
        field: ResolvableField,
        database: Database,
        parent_item: ResourceBase | None = None,
    ) -> None:
        obj_id = getattr(item, field.source_field)
        if obj_id is None:
            return

        related_obj = database.get_one(obj_id)
        setattr(item, field.destination_field, related_obj)
        self._populate_back_reference(item, related_obj, field, parent_item)

    def _populate_back_reference(
        self,
        item: ResourceBase,
        related_obj: ResourceBase,
        field: ResolvableField,
        parent_item: ResourceBase | None,
    ) -> None:
        if field.populates_back is None:
            return

        back_reference = parent_item if parent_item is not None else item
        destination = related_obj
        path = field.populates_back.split('.')
        for path_part in path[:-1]:
            destination = getattr(destination, path_part)
            if destination is None:
                return

        getattr(destination, path[-1]).append(back_reference)

    def _resolve_field_many_to_many(
        self,
        item: ResourceBase,
        field: ResolvableField,
        database: Database,
        parent_item: ResourceBase | None = None,
    ) -> None:
        obj_value = getattr(item, field.source_field, None)
        if not obj_value:
            return

        for obj_id in obj_value:
            related_obj = database.get_one(obj_id)
            getattr(item, field.destination_field).append(related_obj)
            self._populate_back_reference(item, related_obj, field, parent_item)

    def _resolve_field(
        self,
        item: ResourceBase,
        field: ResolvableField,
        database: Database,
        parent_item: ResourceBase | None = None,
    ) -> None:
        """Resolve one field on an object."""
        if field.type in ('one-to-many', 'one-to-none'):
            self._resolve_field_one_to_many(item, field, database, parent_item)
            return

        self._resolve_field_many_to_many(item, field, database, parent_item)


class Database:
    """The database with the real objects."""

    def __init__(self) -> None:
        """Create empty dictionaries for the data."""
        self._data: dict[type[ResourceBase], DataStore] = {}
        self._config: RelacConfig | None = None
        for relac_type in relac_models.values():
            self._data[relac_type] = DataStore[ResourceBase]()

    def get_relac_config(self) -> RelacConfig:
        """Retrieve the Relac config."""
        configs = self._data.get(RelacConfig)
        if configs:
            relac_config = configs.get_one('relac')
            if relac_config is not None:
                return relac_config

        raise RelacConfigNotSetError()

    def add_object[T: ResourceBase](self, obj_id: str, obj: T) -> None:
        """Add the object to the database."""
        obj_type = type(obj)
        if obj_type not in self._data:
            raise UnknownObjectTypeAddedError(obj_id, obj_type.__name__)

        self._data[obj_type].add(obj_id, obj)

    def get_all[T: ResourceBase](self, obj_type: type[T]) -> dict[str, T]:
        """Retrieve all objects from a specific store."""
        store = cast(DataStore[T], self._data[obj_type])
        return store.get_all()

    def get_all_values[T: ResourceBase](self, obj_type: type[T]) -> list[T]:
        """Retrieve all values from a specific store."""
        store = cast(DataStore[T], self._data[obj_type])
        return list(store.get_all().values())

    def get_all_values_for_all_types(self) -> list[ResourceBase]:
        """Retrieve all values from all stores."""
        all_values: list[ResourceBase] = []
        for store in self._data:
            all_values.extend(self.get_all_values(store))
        return all_values

    def get_one(self, obj_id: str) -> ResourceBase:
        """Get one object on ID."""
        obj_type = relac_models.get(obj_id.split('.', maxsplit=1)[0])
        if obj_type is None:
            raise UnknownObjectTypeRequestedError(obj_id)

        obj = self._data[obj_type].get_one(obj_id)
        if obj is None:
            raise ObjectNotFoundError(obj_id)

        return obj

    def resolve_all(self) -> None:
        """Resolve all fields in all objects."""
        for data_store in self._data.values():
            data_store.resolve_all(self)
