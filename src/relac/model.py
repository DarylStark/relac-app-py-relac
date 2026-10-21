"""Module with the models for the application."""

from abc import ABC, abstractmethod
from datetime import date
from enum import Enum
from typing import override

from pydantic import BaseModel, Field


class ResourceBase(ABC, BaseModel):
    """Base model for resources."""

    @abstractmethod
    def is_valid(self) -> bool:
        """Abstract method to determine if a resource is valid."""


class AuthorState(Enum):
    """States for authors."""

    UNSPECIFIED = 'unspecified'
    ALIVE = 'alive'
    DECEASED = 'deceased'


class Author(ResourceBase):
    """Model for a author."""

    name: str
    state: AuthorState = AuthorState.UNSPECIFIED
    birthdate: date | None = None
    deceased_date: date | None = None

    @override
    def is_valid(self) -> bool:
        """Check if this model is valid."""
        return self.name.strip() != ''


class WorkType(Enum):
    """Work types."""

    UNSPECIFIED = 'unspecified'
    LITERARY_FICTION = 'literary-fiction'
    GENRE_FICTION = 'genre-fiction'
    ACADEMIC = 'academic'
    MEMOIR = 'memoir'
    POETRY = 'poetry'
    EASSY = 'essay'


class WorkStructure(Enum):
    """Work structures."""

    UNSPECIFIED = 'unspecified'
    NOVEL = 'novel'
    SHORT_STORY = 'short-story'
    ESSAY = 'essay'
    TEXTBOOK = 'textbook'
    MANUAL = 'manual'


class Work(ResourceBase):
    """Model for a work."""

    title: str
    authors: list[Author] = Field(default_factory=list)
    work_type: WorkType | None = None
    work_structure: WorkStructure | None = None
    editions_objs: list[WorkEdition] = Field(default_factory=list)
    editions: list[str] = Field(default_factory=list)

    @override
    def is_valid(self) -> bool:
        """Check if this model is valid."""
        return self.title.strip() != ''


class WorkEditionType(Enum):
    """Work edition types."""

    UNSPECIFIED = 'unspecified'
    ORIGINAL = 'original'
    TRANSLATION = 'translation'
    REVISED = 'revised'  # Revised version
    UNCUT = 'uncut'  # Version without edit
    ABRIGED = 'abriged'  # Summarized of simplified text
    ANNOTATED = 'annotated'  # With study notes


class WorkEdition(ResourceBase):
    """A edition for a work."""

    title: str
    work: Work | None = None
    release_date: date | None = None
    edition_type: WorkEditionType = WorkEditionType.UNSPECIFIED
    language: str | None = None

    @override
    def is_valid(self) -> bool:
        """Check if this model is valid."""
        return self.title.strip() != ''


class BookCollection(ResourceBase):
    """A collection of books."""

    name: str

    @override
    def is_valid(self) -> bool:
        """Check if this model is valid."""
        return self.name.strip() != ''


class BookPublisher(ResourceBase):
    """Model for a publisher."""

    name: str
    imprint: str | None = None

    @override
    def is_valid(self) -> bool:
        """Check if this model is valid."""
        return self.name.strip() != ''


class BookMedium(Enum):
    """Mediums for books."""

    UNSPECIFIED = 'unspecified'
    PAPERBACK = 'paperback'
    HARDCOVER = 'hardcover'
    EBOOK = 'ebook'
    AUDIOBOOK = 'audiobook'


class BookBinding(Enum):
    """Mediums for books."""

    UNSPECIFIED = 'unspecified'
    POCKET = 'pocket'
    LUXE_EDITION = 'luxe_edition'
    GRAPHICAL_NOVEL_ADAPTION = 'graphical_novel_adaption'
    EPUB = 'epub'
    EPUB_WATERMARK = 'epub_watermark'
    EPUB_DRM = 'epub_drm'


class Book(ResourceBase):
    """A book."""

    isbn13: int
    title: str
    publisher: BookPublisher | None = None
    medium: BookMedium = BookMedium.UNSPECIFIED
    binding: BookBinding = BookBinding.UNSPECIFIED

    @override
    def is_valid(self) -> bool:
        """Check if this model is valid."""
        # TODO: Validate the isbn13
        return self.title.strip() != ''


class ReadingSession(ResourceBase):
    """A reading session."""

    startdate: date | None = None
    enddate: date | None = None
    finished: bool = False

    @override
    def is_valid(self) -> bool:
        """Check if this model is valid."""
        return True


class Label(ResourceBase):
    """A label."""

    name: str

    @override
    def is_valid(self) -> bool:
        """Check if this model is valid."""
        return self.name.strip() != ''


class ResourceList(ResourceBase):
    """A list of resources."""

    name: str

    @override
    def is_valid(self) -> bool:
        """Check if this model is valid."""
        return self.name.strip() != ''
