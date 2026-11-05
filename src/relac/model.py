"""Module with the models for the application."""

from collections.abc import Iterable
from datetime import date, timedelta
from enum import Enum

from pydantic import BaseModel, Field


class ResourceAvailability(Enum):
    """Availability for resources."""

    UNAVAILABLE = 'unavailable'
    AVAILABLE_DIRECT = 'available-direct'
    AVAILABLE_INDIRECT = 'available-indirect'
    AVAILABLE_TO_LOAN = 'available-to-loan'
    AVAILABLE_TO_BUY = 'available-to-buy'


def _aggregate_availability(
    owners: Iterable[Owner],
) -> ResourceAvailability:
    """Aggregate owner availability using owner type and access level."""
    owner_list = tuple(owners)

    if any(
        owner.owner_type == OwnerType.PERSON
        and owner.availability == Availability.DIRECTLY_AVAILABLE
        for owner in owner_list
    ):
        return ResourceAvailability.AVAILABLE_DIRECT
    if any(
        owner.owner_type == OwnerType.PERSON
        and owner.availability == Availability.INDIRECTLY_AVAILABLE
        for owner in owner_list
    ):
        return ResourceAvailability.AVAILABLE_INDIRECT
    if any(
        owner.owner_type == OwnerType.LIBRARY
        and owner.availability == Availability.DIRECTLY_AVAILABLE
        for owner in owner_list
    ):
        return ResourceAvailability.AVAILABLE_TO_LOAN
    if any(
        owner.owner_type == OwnerType.STORE
        and owner.availability == Availability.DIRECTLY_AVAILABLE
        for owner in owner_list
    ):
        return ResourceAvailability.AVAILABLE_TO_BUY

    return ResourceAvailability.UNAVAILABLE


class ResourceBase(BaseModel):
    """Base model for resources."""

    id: str | None = Field(default=None)


class RelacConfig(BaseModel):
    """Model for Relac configuration."""

    title: str


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
    countries: list[str] = Field(default_factory=list)

    # Relation (real objects)
    work_objs: list[Work] = Field(default_factory=list)
    book_objs: list[Book] = Field(default_factory=list)

    def _get_works_with_specific_reading_state(
        self, reading_state: ReadingState
    ) -> list[Work]:
        return [
            work
            for work in self.work_objs
            if work.reading_state == reading_state
        ]

    @property
    def read_count(self) -> int:
        """Get the number of finished works by this author."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.FINISHED)
        )

    @property
    def reading_count(self) -> int:
        """Get the number of works being read by this author."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.READING)
        )

    @property
    def paused_count(self) -> int:
        """Get the number of paused works by this author."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.PAUSED)
        )

    @property
    def dnf_count(self) -> int:
        """Get the number of unfinished works by this author."""
        return len(
            self._get_works_with_specific_reading_state(
                ReadingState.DID_NOT_FINISH
            )
        )

    @property
    def not_read_count(self) -> int:
        """Get the number of unread works by this author."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.NOT_READ)
        )

    @property
    def read_percentage(self) -> float:
        """Get the percentage of this author's works that are finished."""
        if not self.work_objs:
            return 0.0

        return self.read_count / len(self.work_objs) * 100


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
    book_objs: list[Book] = Field(default_factory=list)
    series_objs: list[Series] = Field(default_factory=list)

    # Properties
    @property
    def availability(self) -> ResourceAvailability:
        """Get the availability for this edition."""
        return _aggregate_availability(
            owner for book in self.book_objs for owner in book.owner_objs
        )

    @property
    def reading_state(self) -> ReadingState:
        """Property for reading states."""
        if any(
            edition.reading_state == ReadingState.FINISHED
            for edition in self.edition_objs
            if edition.edition_type != WorkEditionType.ABRIGED
        ):
            return ReadingState.FINISHED

        if any(
            edition.reading_state == ReadingState.READING
            for edition in self.edition_objs
            if edition.edition_type != WorkEditionType.ABRIGED
        ):
            return ReadingState.READING

        if any(
            edition.reading_state == ReadingState.PAUSED
            for edition in self.edition_objs
            if edition.edition_type != WorkEditionType.ABRIGED
        ):
            return ReadingState.PAUSED

        if any(
            edition.reading_state == ReadingState.DID_NOT_FINISH
            for edition in self.edition_objs
            if edition.edition_type != WorkEditionType.ABRIGED
        ):
            return ReadingState.DID_NOT_FINISH

        return ReadingState.NOT_READ

    @property
    def reading_session_objs(self) -> list[ReadingSession]:
        """Get reading sessions from all editions of this work."""
        return [
            reading_session
            for edition in self.edition_objs
            for reading_session in edition.reading_session_objs
        ]


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
    book_objs: list[Book] = Field(default_factory=list)
    reading_session_objs: list[ReadingSession] = Field(default_factory=list)

    # Properties
    @property
    def availability(self) -> ResourceAvailability:
        """Get the availability for this edition."""
        return _aggregate_availability(
            owner for book in self.book_objs for owner in book.owner_objs
        )

    @property
    def reading_state(self) -> ReadingState:
        """Property for reading states."""
        if any(
            reading_session.state == ReadingState.FINISHED
            for reading_session in self.reading_session_objs
        ):
            return ReadingState.FINISHED

        if any(
            reading_session.state == ReadingState.READING
            for reading_session in self.reading_session_objs
        ):
            return ReadingState.READING

        if any(
            reading_session.state == ReadingState.PAUSED
            for reading_session in self.reading_session_objs
        ):
            return ReadingState.PAUSED

        if any(
            reading_session.state == ReadingState.DID_NOT_FINISH
            for reading_session in self.reading_session_objs
        ):
            return ReadingState.DID_NOT_FINISH

        return ReadingState.NOT_READ

    @property
    def authors(self) -> list[Author]:
        """Retrieve the authors for this WorkEdition."""
        if not self.work_obj:
            return []
        return self.work_obj.author_objs


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
    owners: list[str] | None = None

    # Relationships (real objects)
    work_edition_objs: list[WorkEdition] = Field(default_factory=list)
    author_objs: list[Author] = Field(default_factory=list)
    publisher_obj: BookPublisher = Field(default_factory=list)
    collection_objs: list[BookCollection] = Field(default_factory=list)
    owner_objs: list[Owner] = Field(default_factory=list)
    reading_session_objs: list[ReadingSession] = Field(default_factory=list)

    # Properties
    @property
    def availability(self) -> ResourceAvailability:
        """Get the availability for this book."""
        return _aggregate_availability(self.owner_objs)

    def _get_unique_works(self) -> list[Work]:
        works_by_id: dict[str, Work] = {}
        for edition in self.work_edition_objs:
            if edition.work_obj is not None:
                works_by_id.setdefault(edition.work, edition.work_obj)

        return list(works_by_id.values())

    def _get_works_with_specific_reading_state(
        self, reading_state: ReadingState
    ) -> list[Work]:
        return [
            work
            for work in self._get_unique_works()
            if work.reading_state == reading_state
        ]

    @property
    def read_count(self) -> int:
        """Get the number of finished works in this book."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.FINISHED)
        )

    @property
    def reading_count(self) -> int:
        """Get the number of works being read in this book."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.READING)
        )

    @property
    def dnf_count(self) -> int:
        """Get the number of unfinished works in this book."""
        return len(
            self._get_works_with_specific_reading_state(
                ReadingState.DID_NOT_FINISH
            )
        )

    @property
    def paused_count(self) -> int:
        """Get the number of paused works in this book."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.PAUSED)
        )

    @property
    def not_read_count(self) -> int:
        """Get the number of unread works in this book."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.NOT_READ)
        )

    @property
    def read_percentage(self) -> float:
        """Get the percentage of works for this book that are finished."""
        works = self._get_unique_works()
        if not works:
            return 0.0

        return self.read_count / len(works) * 100


class ReadingState(Enum):
    """The state of a reading session."""

    NOT_READ = 'not-read'
    READING = 'reading'
    PAUSED = 'paused'
    FINISHED = 'finished'
    DID_NOT_FINISH = 'did-not-finish'


class ReadingSession(ResourceBase):
    """A reading session."""

    work_edition: str
    book: str
    state: ReadingState

    startdate: date | None = None
    enddate: date | None = None

    # Relationships (real objects)
    work_edition_obj: WorkEdition | None = None
    book_obj: Book | None = None

    @property
    def effective_enddate(self) -> date | None:
        """Get the end date, using today for an active reading session."""
        if self.enddate is not None:
            return self.enddate
        if self.state is ReadingState.READING:
            return date.today()
        return None

    @property
    def duration(self) -> timedelta | None:
        """Get the elapsed time between the start and effective end dates."""
        if self.startdate is None or self.effective_enddate is None:
            return None

        return self.effective_enddate - self.startdate


class Label(ResourceBase):
    """A label."""

    name: str


class ReadingListItem(ResourceBase):
    """A item in a reading list."""

    order: int
    work: str

    # Relationships (real objects)
    work_obj: Work | None = None


class ReadingList(ResourceBase):
    """A list of resources."""

    name: str
    works: list[ReadingListItem] = Field(default_factory=list)

    def _get_works_with_specific_reading_state(
        self, reading_state: ReadingState
    ) -> list[Work]:
        return [
            work.work_obj
            for work in self.works
            if work.work_obj is not None
            and work.work_obj.reading_state == reading_state
        ]

    # Properties
    @property
    def read_count(self) -> int:
        """Get the number of works that are read in this list."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.FINISHED)
        )

    @property
    def reading_count(self) -> int:
        """Get the number of works that are being read in this list."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.READING)
        )

    @property
    def dnf_count(self) -> int:
        """Get the number of works that are are not finished in this list."""
        return len(
            self._get_works_with_specific_reading_state(
                ReadingState.DID_NOT_FINISH
            )
        )

    @property
    def paused_count(self) -> int:
        """Get the number of works that are are paused in this list."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.PAUSED)
        )

    @property
    def not_read_count(self) -> int:
        """Get the number of works that are are not read in this list."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.NOT_READ)
        )

    @property
    def read_percentage(self) -> float:
        """Get the percentage of works in this list that are finished."""
        if not self.works:
            return 0.0

        return self.read_count / len(self.works) * 100


class OwnerType(Enum):
    """Type for a owner."""

    UNSPECIFIED = 'unspecified'
    PERSON = 'person'
    LIBRARY = 'library'
    STORE = 'store'


class Availability(Enum):
    """Availability for a owner."""

    NOT_AVAILABLE = 'not-available'
    DIRECTLY_AVAILABLE = 'directly'
    INDIRECTLY_AVAILABLE = 'indirectly'


class Owner(ResourceBase):
    """Model for a owner."""

    name: str
    owner_type: OwnerType = OwnerType.UNSPECIFIED
    availability: Availability = Availability.NOT_AVAILABLE

    # Relationships (real objects)
    book_objs: list[Book] = Field(default_factory=list)


class SeriesItem(ResourceBase):
    """A item in a serie."""

    number: int
    work: str

    # Relationships (real objects)
    work_obj: Work | None = None


class Series(ResourceBase):
    """A serie of works."""

    name: str
    works: list[SeriesItem] = Field(default_factory=list)

    def _get_works_with_specific_reading_state(
        self, reading_state: ReadingState
    ) -> list[Work]:
        return [
            item.work_obj
            for item in self.works
            if item.work_obj is not None
            and item.work_obj.reading_state == reading_state
        ]

    @property
    def read_count(self) -> int:
        """Get the number of finished works in this series."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.FINISHED)
        )

    @property
    def reading_count(self) -> int:
        """Get the number of works being read in this series."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.READING)
        )

    @property
    def dnf_count(self) -> int:
        """Get the number of unfinished works in this series."""
        return len(
            self._get_works_with_specific_reading_state(
                ReadingState.DID_NOT_FINISH
            )
        )

    @property
    def paused_count(self) -> int:
        """Get the number of paused works in this series."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.PAUSED)
        )

    @property
    def not_read_count(self) -> int:
        """Get the number of unread works in this series."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.NOT_READ)
        )

    @property
    def read_percentage(self) -> float:
        """Get the percentage of works in this series that are finished."""
        if not self.works:
            return 0.0

        return self.read_count / len(self.works) * 100
