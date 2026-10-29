"""Module with the models for the application."""

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, PrivateAttr


class ResourceBase(BaseModel):
    """Base model for resources."""

    _id: str | None = PrivateAttr(default=None)


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

    # Relation (real objects)
    work_objs: list[Work] = Field(default_factory=list)


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
    authors: list[str]
    work_type: WorkType | None = None
    work_structure: WorkStructure | None = None

    # Relation (real objects)
    author_objs: list[Author] = Field(default_factory=list)
    edition_objs: list[WorkEdition] = Field(default_factory=list)


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
    work: str
    release_date: date | None = None
    edition_type: WorkEditionType = WorkEditionType.UNSPECIFIED
    language: str | None = None

    # Relations (real objects)
    work_obj: Work | None = None


class BookCollection(ResourceBase):
    """A collection of books."""

    name: str
    books: list[str] = Field(default_factory=list)

    # Relations (real objects)
    book_objs: list[Book] = Field(default_factory=list)


class BookPublisher(ResourceBase):
    """Model for a publisher."""

    name: str
    imprint: str | None = None

    # Relations (real objects)
    book_objs: list[Book] = Field(default_factory=list)


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
    NOVELLA = 'novella'
    LUXE_EDITION = 'luxe-edition'
    GRAPHICAL_NOVEL_ADAPTION = 'graphical-novel-adaption'
    EPUB = 'epub'
    EPUB_WATERMARK = 'epub-watermark'
    EPUB_DRM = 'epub-drm'


class Book(ResourceBase):
    """A book."""

    isbn13: int
    title: str
    publisher: str | None = None
    work_editions: list[str] = Field(default_factory=list)
    medium: BookMedium = BookMedium.UNSPECIFIED
    binding: BookBinding = BookBinding.UNSPECIFIED

    # Relationships (real objects)
    work_edition_objs: list[WorkEdition] = Field(default_factory=list)
    publisher_obj: BookPublisher = Field(default_factory=list)
    collection_objs: list[BookCollection] = Field(default_factory=list)


class ReadingSession(ResourceBase):
    """A reading session."""

    startdate: date | None = None
    enddate: date | None = None
    finished: bool = False
    work_edition: str | None = None
    book: str | None = None

    # Relationships (real objects)
    work_edition_obj: WorkEdition | None = None
    book_obj: Book | None = None


class Label(ResourceBase):
    """A label."""

    name: str


class ResourceList(ResourceBase):
    """A list of resources."""

    name: str
