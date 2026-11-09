"""Module with the models for the application."""

import statistics
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


class LabelledResource(ResourceBase):
    """Base model for labelled resources."""

    labels: list[str] | None = None
    label_objs: list[Label] = Field(default_factory=list)


class RelacConfig(BaseModel):
    """Model for Relac configuration."""

    title: str
    owner: str | None = None

    # Relation (real objects)
    owner_obj: Owner | None = None


class ContributorState(Enum):
    """States for contributors."""

    UNSPECIFIED = 'unspecified'
    ALIVE = 'alive'
    DECEASED = 'deceased'


class Contributor(LabelledResource):
    """Model for a contributor."""

    name: str
    state: ContributorState = ContributorState.UNSPECIFIED
    birthdate: date | None = None
    deceased_date: date | None = None
    countries: list[str] = Field(default_factory=list)
    # labels: list[str] | None = None

    # Relation (real objects)
    work_objs: list[Work] = Field(default_factory=list)
    book_objs: list[Book] = Field(default_factory=list)
    illustrator_work_edition_objs: list[WorkEdition] = Field(
        default_factory=list
    )
    translator_work_edition_objs: list[WorkEdition] = Field(
        default_factory=list
    )

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
        """Get the number of finished works by this contributor."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.FINISHED)
        )

    @property
    def reading_count(self) -> int:
        """Get the number of works being read by this contributor."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.READING)
        )

    @property
    def paused_count(self) -> int:
        """Get the number of paused works by this contributor."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.PAUSED)
        )

    @property
    def dnf_count(self) -> int:
        """Get the number of unfinished works by this contributor."""
        return len(
            self._get_works_with_specific_reading_state(
                ReadingState.DID_NOT_FINISH
            )
        )

    @property
    def not_read_count(self) -> int:
        """Get the number of unread works by this contributor."""
        return len(
            self._get_works_with_specific_reading_state(ReadingState.NOT_READ)
        )

    @property
    def read_percentage(self) -> float:
        """Get the percentage of this contributor's works that are finished."""
        if not self.work_objs:
            return 0.0

        return self.read_count / len(self.work_objs) * 100

    @property
    def rating(self) -> float | None:
        """Get the rating for this Contributor based on its works."""
        """Get the average rating for this book."""
        ratings = [rs_obj.rating for rs_obj in self.work_objs if rs_obj.rating]
        if not ratings:
            return None
        return statistics.mean(ratings)


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


class WorkChronology(Enum):
    """Work chronology."""

    LINEAR = 'linear'
    NON_LINEAR = 'non-linear'
    FRAMED = 'framed'
    DUAL_TIMELINE = 'dual-timeline'


class WorkPacing(Enum):
    """Work pacing."""

    GRADUAL_BUILD = 'gradual-build'
    FAST_PACED = 'fast-paced'
    IN_MEDIA_RES = 'in-media-res'
    CYCLICAL = 'cyclical'
    CONTEMPLATIVE = 'contemplative'
    FRONT_LOADED = 'front-loaded'


class StoryStructure(BaseModel):
    """Structure for the literary work."""

    chronology: WorkChronology
    pacing: WorkPacing


class Location(ResourceBase):
    """Model for a location."""

    name: str
    country: str | None = None
    description: str | None = None


class StorySetting(BaseModel):
    """The setting for a story."""

    time_period: str | None = None
    locations: list[str] | None = None

    # Relation (real objects)
    location_objs: list[Location] = Field(default_factory=list)


class Character(ResourceBase):
    """A character in a story."""

    name: str
    birthdate: date | None = None
    birthplace: str
    birthcountry: str
    deceased_date: date | None = None


class CharacterRole(Enum):
    """Roles for characters."""

    PROTAGONIST = 'protagonist'
    ANTAGONIST = 'antagonist'
    DEUTERAGONIST = 'deuteragonist'
    TRITAGONIST = 'tritagonist'
    MENTOR = 'mentor'
    FOIL = 'foil'
    LOVE_INTEREST = 'love-interest'
    CONFIDANT = 'confidant'


class StoryArc(Enum):
    """Story arcs for characters."""

    POSITIVE_CHANGE = 'positive-change'
    TRAGIC_FALL = 'tragic-fall'
    FLAT = 'flat'


class WorkCharacter(BaseModel):
    """A link between a character and a LiteraryAnalysis."""

    character: str
    roles: list[CharacterRole] = Field(default_factory=list)
    note: str | None = None
    story_arc: StoryArc | None = None

    # Relation (real objects)
    character_obj: Character | None = None


class ChapterAnalysis(BaseModel):
    """Analysis for a chapter."""

    number: int
    title: str | None = None
    summary: str | None = None
    analysis: str | None = None


class LiteraryAnalysis(BaseModel):
    """Model for a works literary analysis."""

    work_summary: str | None = None
    work_analysis: str | None = None
    structure: StoryStructure | None = None
    setting: StorySetting | None = None
    characters: list[WorkCharacter] = Field(default_factory=list)
    chapters: list[ChapterAnalysis] = Field(default_factory=list)


class Work(LabelledResource):
    """Model for a work."""

    title: str
    authors: list[str]
    work_type: WorkType | None = None
    work_structure: WorkStructure | None = None
    premise: str | None = None

    literary_analysis: LiteraryAnalysis | None = None

    # Relation (real objects)
    author_objs: list[Contributor] = Field(default_factory=list)
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

    @property
    def rating(self) -> float | None:
        """Get the average rating for this work."""
        ratings = [
            rs_obj.rating for rs_obj in self.edition_objs if rs_obj.rating
        ]
        if not ratings:
            return None
        return statistics.mean(ratings)


class WorkEditionType(Enum):
    """Work edition types."""

    UNSPECIFIED = 'unspecified'
    ORIGINAL = 'original'
    TRANSLATION = 'translation'
    REVISED = 'revised'  # Revised version
    UNCUT = 'uncut'  # Version without edit
    ABRIGED = 'abriged'  # Summarized of simplified text
    ANNOTATED = 'annotated'  # With study notes


class WorkEdition(LabelledResource):
    """A edition for a work."""

    title: str
    work: str
    release_date: date | None = None
    edition_type: WorkEditionType = WorkEditionType.UNSPECIFIED
    language: str | None = None
    illustrators: list[str] | None = None
    translators: list[str] | None = None

    # Relations (real objects)
    work_obj: Work | None = None
    book_objs: list[Book] = Field(default_factory=list)
    reading_session_objs: list[ReadingSession] = Field(default_factory=list)
    illustrator_objs: list[Contributor] = Field(default_factory=list)
    translator_objs: list[Contributor] = Field(default_factory=list)

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
    def authors(self) -> list[Contributor]:
        """Retrieve the authors for this WorkEdition."""
        if not self.work_obj:
            return []
        return self.work_obj.author_objs

    @property
    def rating(self) -> float | None:
        """Get the average rating for this work edition."""
        ratings = [
            rs_obj.work_rating.rating
            for rs_obj in self.reading_session_objs
            if rs_obj.work_rating
        ]
        if not ratings:
            return None
        return statistics.mean(ratings)


class BookCollection(LabelledResource):
    """A collection of books."""

    name: str
    books: list[str] = Field(default_factory=list)

    # Relations (real objects)
    book_objs: list[Book] = Field(default_factory=list)

    def owned_percentage(self, owner: Owner | None) -> float:
        """Get the percentage of books owned by the specified owner."""
        if not self.book_objs:
            return 0.0

        owned_count = sum(
            book.is_owned_by_owner(owner) for book in self.book_objs
        )
        return owned_count / len(self.book_objs) * 100

    @property
    def rating(self) -> float | None:
        """Get the average rating for this work."""
        ratings = [rs_obj.rating for rs_obj in self.book_objs if rs_obj.rating]
        rated_ratings = [rating for rating in ratings if rating is not None]
        if not rated_ratings:
            return None
        return statistics.mean(rated_ratings)


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


class Book(LabelledResource):
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
    contributor_objs: list[Contributor] = Field(default_factory=list)
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

    @property
    def rating(self) -> float | None:
        """Get the average rating for this book."""
        ratings = [
            rs_obj.book_rating.rating
            for rs_obj in self.reading_session_objs
            if rs_obj.book_rating
        ]
        if not ratings:
            return None
        return statistics.mean(ratings)

    # Data retrievals
    def is_owned_by_owner(self, owner: Owner | None) -> bool:
        """Check if this book is owned by a specific owner."""
        return owner in self.owner_objs


class ReadingState(Enum):
    """The state of a reading session."""

    NOT_READ = 'not-read'
    READING = 'reading'
    PAUSED = 'paused'
    FINISHED = 'finished'
    DID_NOT_FINISH = 'did-not-finish'


class Rating(BaseModel):
    """A object for a rating."""

    rating: float
    note: str | None = None


class ReadingSession(LabelledResource):
    """A reading session."""

    work_edition: str
    book: str
    state: ReadingState

    startdate: date | None = None
    enddate: date | None = None
    work_rating: Rating | None = None
    book_rating: Rating | None = None

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

    @property
    def rating(self) -> float | None:
        """Get the average rating for this Reading Session."""
        ratings: list[float] = []
        if self.work_rating:
            ratings.append(self.work_rating.rating)
        if self.book_rating:
            ratings.append(self.book_rating.rating)
        return None if len(ratings) == 0 else statistics.mean(ratings)


class Label(ResourceBase):
    """A label."""

    name: str

    # Relationships (real objects)
    contributor_objs: list[Contributor] = Field(default_factory=list)
    work_objs: list[Work] = Field(default_factory=list)
    work_edition_objs: list[WorkEdition] = Field(default_factory=list)
    series_objs: list[Series] = Field(default_factory=list)
    reading_list_objs: list[ReadingList] = Field(default_factory=list)
    reading_session_objs: list[ReadingSession] = Field(default_factory=list)
    book_objs: list[Book] = Field(default_factory=list)
    owner_objs: list[Owner] = Field(default_factory=list)
    book_collection_objs: list[BookCollection] = Field(default_factory=list)


class ReadingListItem(ResourceBase):
    """A item in a reading list."""

    order: int
    work: str

    # Relationships (real objects)
    work_obj: Work | None = None


class ReadingList(LabelledResource):
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

    @property
    def rating(self) -> float | None:
        """Get the average rating for this work."""
        ratings = [
            rs_obj.work_obj.rating for rs_obj in self.works if rs_obj.work_obj
        ]
        rated_ratings = [rating for rating in ratings if rating is not None]
        if not rated_ratings:
            return None
        return statistics.mean(rated_ratings)


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


class Owner(LabelledResource):
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


class Series(LabelledResource):
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

    @property
    def rating(self) -> float | None:
        """Get the average rating for this work."""
        ratings = [
            rs_obj.work_obj.rating for rs_obj in self.works if rs_obj.work_obj
        ]
        rated_ratings = [rating for rating in ratings if rating is not None]
        if not rated_ratings:
            return None
        return statistics.mean(rated_ratings)
