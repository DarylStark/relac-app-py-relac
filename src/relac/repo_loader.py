"""Module with a abstract repo loader."""

from abc import ABC, abstractmethod


class RepoLoader(ABC):
    """Abstract repo loader."""

    @abstractmethod
    def retrieve_objects(self) -> dict[str, dict]:
        """Retrieve the objects from the repo."""
