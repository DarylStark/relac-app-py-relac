"""Module with the RelacDatabase class."""

from typing import cast

from relac.model import ResourceBase, relac_models


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

    def get_all(self) -> dict[str, T]:
        """Retrieve all objects from the database."""
        return self._data


class RelacDatabase:
    """The database with the real objects."""

    def __init__(self) -> None:
        """Create empty dictionaries for the data."""
        self._data: dict[type[ResourceBase], DataStore] = {}
        # self._data[Contributor] = DataStore[Contributor]()
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
