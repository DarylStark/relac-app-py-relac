"""Module with the RelacDatabase class."""

from typing import cast

from relac.model import ResolvableField, ResourceBase, relac_models


class DataStore[T: ResourceBase]:
    """Class that keeps data for the database."""

    def __init__(self) -> None:
        """Initialize empty database."""
        self._data: dict[str, T] = {}

    def add(self, obj_id: str, obj: T) -> None:
        """Add a object to the datastore."""
        if self._data.get(obj_id) is not None:
            # TODO: Custom error
            raise ValueError(
                f'Object with id "{obj_id}" is already in the database'
            )

        self._data[obj_id] = obj

    def get_one(self, obj_id: str) -> T | None:
        """Retrieve one element from the store."""
        return self._data.get(obj_id)

    def get_all(self) -> dict[str, T]:
        """Retrieve all objects from the database."""
        return self._data

    def resolve_all(self, database: RelacDatabase) -> None:
        """Resolve all fields in all objects."""
        items_with_resolvable = [
            v for v in self._data.values() if 'resolvable_fields' in dir(v)
        ]
        for item in items_with_resolvable:
            for field in getattr(item, 'resolvable_fields', []):
                self._resolve_field(item, field, database)

    def _resolve_field_many_to_many(
        self,
        item: ResourceBase,
        field: ResolvableField,
        database: RelacDatabase,
    ) -> None:
        related_obj = database.get_one(getattr(item, field.source_field))
        setattr(item, field.destination_field, related_obj)
        getattr(related_obj, field.populates_back).append(item)

    def _resolve_field_on_to_many(
        self,
        item: ResourceBase,
        field: ResolvableField,
        database: RelacDatabase,
    ) -> None:
        for obj_id in getattr(item, field.source_field):
            related_obj = database.get_one(obj_id)
            getattr(item, field.destination_field).append(related_obj)
            getattr(related_obj, field.populates_back).append(item)

    def _resolve_field(
        self,
        item: ResourceBase,
        field: ResolvableField,
        database: RelacDatabase,
    ) -> None:
        """Resolve one field on an object."""
        if field.type == 'one-to-many':
            self._resolve_field_many_to_many(item, field, database)
            return

        self._resolve_field_on_to_many(item, field, database)


class RelacDatabase:
    """The database with the real objects."""

    def __init__(self) -> None:
        """Create empty dictionaries for the data."""
        self._data: dict[type[ResourceBase], DataStore] = {}
        for relac_type in relac_models.values():
            self._data[relac_type] = DataStore[ResourceBase]()

    def add_object[T: ResourceBase](self, obj_id: str, obj: T) -> None:
        """Add the object to the database."""
        obj_type = type(obj)
        if obj_type not in self._data:
            # TODO: Custom error
            raise TypeError(f'Type {obj_type} is not a valid type')

        self._data[obj_type].add(obj_id, obj)

    def get_all[T: ResourceBase](self, obj_type: type[T]) -> dict[str, T]:
        """Retrieve all objects from a specific store."""
        store = cast(DataStore[T], self._data[obj_type])
        return store.get_all()

    def get_one(self, obj_id: str) -> ResourceBase:
        """Get one object on ID."""
        obj_type = relac_models.get(obj_id.split('.', maxsplit=1)[0])
        if obj_type is None:
            # TODO: Custom error
            raise ValueError('Unknown object')
        obj = self._data[obj_type].get_one(obj_id)
        if obj is None:
            raise ValueError('Unknown object')
        return obj

    def resolve_all(self) -> None:
        """Resolve all fields in all objects."""
        for data_store in self._data.values():
            data_store.resolve_all(self)
