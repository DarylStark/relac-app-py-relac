"""Module with the models for the application."""

import statistics
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import ClassVar, Literal, override

from pydantic import BaseModel, Field

from relac.data_helpers import (
    _code_to_language,
    _format_enum_label,
    _format_isbn,
)
from relac.exceptions import DoubleModelNameError

relac_models: dict[str, type[ResourceBase]] = {}


def register_model[TResource: ResourceBase](
    model_name: str,
) -> Callable[[type[TResource]], type[TResource]]:
    """Decorator to register a model for data."""

    def model_decorator(class_: type[TResource]) -> type[TResource]:
        if model_name in relac_models:
            raise DoubleModelNameError(model_name)
        relac_models[model_name] = class_
        return class_

    return model_decorator


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


@dataclass
class ResolvableField:
    """Field that can be resolved."""

    source_field: str
    destination_field: str
    type: Literal['many-to-many', 'one-to-many', 'one-to-none']
    populates_back: str | None = None


def search_detail(name: str, value: str | None) -> str:
    """Generate a search detail."""
    if value is None:
        return ''
    return f'{name}: {value}'


def search_detail_for_obj[T: BaseModel](
    name: str, field: str, obj: T | None
) -> str:
    """Create a search detail for a enum value."""
    if obj is None:
        return ''

    return search_detail(name, getattr(obj, field, ''))


def search_detail_for_obj_list[T: BaseModel](
    name: str, field: str, lst: list[T] | None
) -> str:
    """Create a search detail for a enum value."""
    if not lst:
        return ''

    values = [getattr(value, field) for value in lst]
    return search_detail(name, ', '.join(values))


def search_detail_for_str_list(name: str, lst: list[str] | None) -> str:
    """Create a search detail for a enum value."""
    if not lst:
        return ''
    return search_detail(name, ', '.join(lst))


def transformed_search_detail[T](
    name: str, value: T | None, transform: Callable[[T], str]
) -> str:
    """Transform a search detail."""
    if value is None:
        return ''
    return search_detail(name, transform(value))


def search_detail_for_enum[T: Enum](name: str, obj: T | None) -> str:
    """Create a search detail for a enum value."""
    if obj is None:
        return ''
    return transformed_search_detail(name, obj.value, _format_enum_label)


@dataclass
class SearchIndexData:
    """Class that contains search index data."""

    resource_type: str
    resource_id: str | None
    title: str
    details: list[str]
    search_terms: list[str] | None = None
    labels: list[str] | None = None

    extra_data: list[SearchIndexData] | None = None


@dataclass
class LintingFinding:
    """Class for a Linting Error."""

    id: str
    resource_id: str | None
    error: str


class ResourceBase(BaseModel):
    """Base model for resources."""

    id: str | None = Field(default=None, exclude=False)

    @property
    def linting_findings(self) -> list[LintingFinding]:
        """Get linting findings for the model."""
        return []

    def _get_resource_type(self) -> str:
        """Get the resource type for this object."""
        return type(self).__name__

    def _get_title(self) -> str:
        """Get the title for this object."""
        fields = ('title', 'name')
        for field in fields:
            value = getattr(self, field, None)
            if value:
                return value
        return ''

    def _get_details(self) -> list[str]:
        """Get the details for this object."""
        return []

    def _get_search_terms(self) -> list[str] | None:
        """Get the search terms for this object."""
        return None

    def _get_label_names(self) -> list[str] | None:
        """Get the label names for this object."""
        return None

    def _get_extra_data(self) -> list[SearchIndexData] | None:
        """Get additional search entries for this object."""
        return None

    def get_search_index_data(self) -> SearchIndexData:
        """Build the data for the search index."""
        return SearchIndexData(
            resource_type=self._get_resource_type(),
            resource_id=self.id,
            title=self._get_title(),
            details=[detail for detail in self._get_details() if detail],
            search_terms=self._get_search_terms(),
            labels=self._get_label_names(),
            extra_data=self._get_extra_data(),
        )

    def __repr__(self) -> str:
        """The repr for this model."""
        # TODO: Implement something sensible
        return ''

    def __str__(self) -> str:
        """The str representation for this model."""
        # TODO: Implement something sensible
        return ''


class LabelledResource(ResourceBase):
    """Base model for labelled resources."""

    labels: list[str] = Field(default_factory=list)

    # Relation (real objects)
    label_objs: list[Label] = Field(default_factory=list, exclude=True)

    @override
    def _get_label_names(self) -> list[str]:
        """Get the label names for this object."""
        return [label.name for label in self.label_objs]


@register_model('relac')
class RelacConfig(ResourceBase):
    """Model for Relac configuration."""

    title: str
    owner: str | None = None

    # Relation (real objects)
    owner_obj: Owner | None = Field(default=None, exclude=True)

    # Resolve definitions
    resolvable_fields: ClassVar[list[ResolvableField]] = [
        ResolvableField('owner', 'owner_obj', 'one-to-none'),
    ]


class ContributorState(Enum):
    """States for contributors."""

    UNSPECIFIED = 'unspecified'
    ALIVE = 'alive'
    DECEASED = 'deceased'


@register_model('contributor')
class Contributor(LabelledResource):
    """Model for a contributor."""

    name: str
    state: ContributorState = ContributorState.UNSPECIFIED
    birthdate: date | None = None
    deceased_date: date | None = None
    countries: list[str] = Field(default_factory=list)

    # Relation (real objects)
    work_objs: list[Work] = Field(default_factory=list, exclude=True)
    book_objs: list[Book] = Field(default_factory=list, exclude=True)
    quote_objs: list[Quote] = Field(default_factory=list, exclude=True)
    illustrator_work_edition_objs: list[WorkEdition] = Field(
        default_factory=list, exclude=True
    )
    translator_work_edition_objs: list[WorkEdition] = Field(
        default_factory=list, exclude=True
    )

    # Resolve definitions
    resolvable_fields: ClassVar[list[ResolvableField]] = [
        ResolvableField(
            'labels', 'label_objs', 'many-to-many', 'contributor_objs'
        ),
    ]

    @override
    def _get_details(self) -> list[str]:
        """Get the details for this object."""
        return [
            search_detail_for_obj_list('Works', 'title', self.work_objs),
            search_detail_for_obj_list('Books', 'title', self.book_objs),
        ]

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


@register_model('location')
class Location(ResourceBase):
    """Model for a location."""

    name: str
    country: str | None = None
    description: str | None = None

    # Relation (real objects)
    work_objs: list[Work] = Field(default_factory=list, exclude=True)

    @override
    def _get_details(self) -> list[str]:
        """Get the details for this object."""
        return [
            search_detail('Country', self.country),
            search_detail('Description', self.description),
            search_detail_for_obj_list('Works', 'title', self.work_objs),
        ]


class StorySetting(BaseModel):
    """The setting for a story."""

    time_period: str | None = None
    locations: list[str] | None = None

    # Relation (real objects)
    location_objs: list[Location] = Field(default_factory=list, exclude=True)

    resolvable_fields: ClassVar[list[ResolvableField]] = [
        ResolvableField(
            'locations', 'location_objs', 'many-to-many', 'work_objs'
        )
    ]


@register_model('character')
class Character(ResourceBase):
    """A character in a story."""

    name: str
    birthdate: date | None = None
    birthplace: str | None = None
    birthcountry: str | None = None
    deceased_date: date | None = None
    description: str | None = None

    # Relation (real objects)
    work_objs: list[Work] = Field(default_factory=list, exclude=True)
    quote_objs: list[Quote] = Field(default_factory=list, exclude=True)

    @override
    def _get_details(self) -> list[str]:
        """Get the details for this object."""
        return [
            search_detail('Birthplace', self.birthplace),
            search_detail('Birth country', self.birthcountry),
            search_detail_for_obj_list('Works', 'title', self.work_objs),
        ]

    def _get_works_with_specific_reading_state(
        self, reading_state: ReadingState
    ) -> list[Work]:
        return [
            work
            for work in self.work_objs
            if work.reading_state == reading_state
        ]

    @property
    def work_character_objs(self) -> list[WorkCharacter]:
        """Get all Work Character objects for this character."""
        rv: list[WorkCharacter] = list()
        for work_obj in self.work_objs:
            if work_obj.literary_analysis:
                rv.extend(work_obj.literary_analysis.characters or [])
        return rv


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
    character_obj: Character | None = Field(default=None, exclude=True)
    work_obj: Work | None = Field(default=None, exclude=True)

    # Resolve definitions
    resolvable_fields: ClassVar[list[ResolvableField]] = [
        ResolvableField(
            'character', 'character_obj', 'one-to-many', 'work_objs'
        )
    ]
    resolvable_parent_fields: ClassVar[tuple[str, ...]] = ('work_obj',)


class ChapterAnalysis(BaseModel):
    """Analysis for a chapter."""

    number: int
    part: int | None = None
    title: str | None = None
    summary: str | None = None
    analysis: str | None = None

    @property
    def page_id(self) -> str:
        """Get a page identifier that distinguishes chapters across parts."""
        if self.part is None:
            return str(self.number)
        return f'part-{self.part}.chapter-{self.number}'


@register_model('quote')
class Quote(ResourceBase):
    """A quote from a contributor."""

    quote: str
    contributor: str
    quote_date: date | None = None
    character: str | None = None
    work: str | None = None

    # Relation (real objects)
    contributor_obj: Contributor | None = Field(default=None, exclude=True)
    character_obj: Character | None = Field(default=None, exclude=True)
    work_obj: Work | None = Field(default=None, exclude=True)

    # Resolve definitions
    resolvable_fields: ClassVar[list[ResolvableField]] = [
        ResolvableField(
            'contributor', 'contributor_obj', 'one-to-many', 'quote_objs'
        ),
        ResolvableField(
            'character', 'character_obj', 'one-to-many', 'quote_objs'
        ),
        ResolvableField(
            'work',
            'work_obj',
            'one-to-many',
            'literary_analysis.quote_objs',
        ),
    ]


class MotifType(Enum):
    """Types of motif."""

    LEITMOTIV = 'leitmotiv'
    SITUATION = 'situation'
    THEMATIC = 'thematic'


class Motif(BaseModel):
    """A motif for a work."""

    name: str
    motif_type: MotifType
    symbolizes: str | None = None
    description: str | None = None


class Perspective(Enum):
    """Perspectives for a story."""

    FIRST_PERSON = 'first-person'
    THIRD_PERSON_LIMITED = 'third-person-limited'
    THIRD_PERSON_OMNISCENT = 'third-person-omniscent'
    MULTIPLE_POV = 'multiple-pov'


class Narrator(BaseModel):
    """Model for a narrator."""

    perspective: Perspective
    character: str | None = None
    reliable: bool | None = None
    notes: str | None = None

    # Relation (real objects)
    character_obj: Character | None = Field(default=None, exclude=True)

    resolvable_fields: ClassVar[list[ResolvableField]] = [
        ResolvableField('character', 'character_obj', 'one-to-none')
    ]


class LiteraryAnalysis(BaseModel):
    """Model for a works literary analysis."""

    work_summary: str | None = None
    work_analysis: str | None = None
    structure: StoryStructure | None = None
    setting: StorySetting | None = None
    characters: list[WorkCharacter] = Field(default_factory=list)
    chapters: list[ChapterAnalysis] = Field(default_factory=list)
    quotes: list[str] = Field(default_factory=list)
    motifs: list[Motif] = Field(default_factory=list)
    narrator: Narrator | None = None

    # Relation (real objects)
    quote_objs: list[Quote] = Field(default_factory=list, exclude=True)

    resolvable_fields: ClassVar[list[ResolvableField]] = [
        ResolvableField('quotes', 'quote_objs', 'many-to-many', 'work_objs'),
    ]
    resolvable_children: ClassVar[tuple[str, ...]] = (
        'characters',
        'narrator',
        'setting',
    )


class PrimaryGenre(Enum):
    """Enum for the primary genre of a work."""

    CRIME_THRILLER = 'crime_thriller'
    LITERARY_FICTION = 'literary_fiction'
    SCI_FI_FANTASY = 'sci_fi_fantasy'
    HORROR = 'horror'
    HISTORICAL = 'historical'
    NON_FICTION = 'non_fiction'


class GenreClassification(BaseModel):
    """Classifications for genre's."""

    primary: PrimaryGenre
    subgenres: list[str] = Field(default_factory=list)


@register_model('work')
class Work(LabelledResource):
    """Model for a work."""

    title: str
    authors: list[str]
    work_type: WorkType | None = None
    work_structure: WorkStructure | None = None
    premise: str | None = None
    genre: GenreClassification | None = None

    literary_analysis: LiteraryAnalysis | None = None

    # Relation (real objects)
    author_objs: list[Contributor] = Field(default_factory=list, exclude=True)
    edition_objs: list[WorkEdition] = Field(default_factory=list, exclude=True)
    book_objs: list[Book] = Field(default_factory=list, exclude=True)
    series_objs: list[Series] = Field(default_factory=list, exclude=True)
    quote_objs: list[Quote] = Field(default_factory=list, exclude=True)

    # Resolve definitions
    resolvable_fields: ClassVar[list[ResolvableField]] = [
        ResolvableField('labels', 'label_objs', 'many-to-many', 'work_objs'),
        ResolvableField('authors', 'author_objs', 'many-to-many', 'work_objs'),
    ]
    resolvable_children: ClassVar[tuple[str, ...]] = ('literary_analysis',)

    @override
    def _get_details(self) -> list[str]:
        """Get the details for this object."""
        rv = [
            search_detail_for_obj_list('Authors', 'name', self.author_objs),
            search_detail_for_enum('Structure', self.work_structure),
            search_detail_for_enum('Category', self.work_type),
            search_detail_for_obj_list('Editions', 'title', self.edition_objs),
        ]

        if self.genre:
            genres = [
                _format_enum_label(self.genre.primary.value.replace('_', '-')),
                *self.genre.subgenres,
            ]
            rv.append(search_detail('Genres', ', '.join(genres)))

        return rv

    @override
    def _get_extra_data(self) -> list[SearchIndexData] | None:
        """Get titled chapter entries associated with this work."""
        if self.id is None or self.literary_analysis is None:
            return None

        return [
            SearchIndexData(
                resource_type='Chapter',
                resource_id=(
                    f'literary_analysis_chapter.{self.id}.{chapter.page_id}'
                ),
                title=(
                    f'Part {chapter.part}: ' if chapter.part is not None else ''
                )
                + f'{chapter.number}. {chapter.title}',
                details=[search_detail('Work', self.title)],
                search_terms=[self.title],
            )
            for chapter in self.literary_analysis.chapters
            if chapter.title
        ]

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


@register_model('work_edition')
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
    work_obj: Work | None = Field(default=None, exclude=True)
    book_objs: list[Book] = Field(default_factory=list, exclude=True)
    reading_session_objs: list[ReadingSession] = Field(
        default_factory=list, exclude=True
    )
    illustrator_objs: list[Contributor] = Field(
        default_factory=list, exclude=True
    )
    translator_objs: list[Contributor] = Field(
        default_factory=list, exclude=True
    )

    # Resolve definitions
    resolvable_fields: ClassVar[list[ResolvableField]] = [
        ResolvableField(
            'labels', 'label_objs', 'many-to-many', 'work_edition_objs'
        ),
        ResolvableField('work', 'work_obj', 'one-to-many', 'edition_objs'),
        ResolvableField(
            'illustrators',
            'illustrator_objs',
            'many-to-many',
            'illustrator_work_edition_objs',
        ),
        ResolvableField(
            'translators',
            'translator_objs',
            'many-to-many',
            'translator_work_edition_objs',
        ),
    ]

    @override
    def _get_resource_type(self) -> str:
        """Get the resource type for this object."""
        return 'Edition'

    @override
    def _get_details(self) -> list[str]:
        """Get the details for this object."""
        return [
            search_detail_for_obj('Work', 'title', self.work_obj),
            search_detail(
                'Release date',
                str(self.release_date) if self.release_date else None,
            ),
            transformed_search_detail(
                'Language', self.language, _code_to_language
            ),
            search_detail_for_enum('Type', self.edition_type),
            search_detail_for_obj_list('Books', 'title', self.book_objs),
        ]

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


@register_model('collection')
class BookCollection(LabelledResource):
    """A collection of books."""

    name: str
    books: list[str] = Field(default_factory=list)

    # Relations (real objects)
    book_objs: list[Book] = Field(default_factory=list, exclude=True)

    resolvable_fields: ClassVar[list[ResolvableField]] = [
        ResolvableField(
            'labels', 'label_objs', 'many-to-many', 'book_collection_objs'
        ),
        ResolvableField(
            'books', 'book_objs', 'many-to-many', 'collection_objs'
        ),
    ]

    @override
    def _get_resource_type(self) -> str:
        """Get the resource type for this object."""
        return 'Collection'

    @override
    def _get_details(self) -> list[str]:
        """Get the details for this object."""
        return [
            search_detail_for_obj_list('Books', 'title', self.book_objs),
        ]

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


@register_model('publisher')
class BookPublisher(ResourceBase):
    """Model for a publisher."""

    name: str
    imprint: str | None = None

    # Relations (real objects)
    book_objs: list[Book] = Field(default_factory=list, exclude=True)


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
    PDF = 'pdf'
    PDF_WATERMARK = 'pdf-watermark'
    PDF_DRM = 'pdf-drm'


@register_model('book')
class Book(LabelledResource):
    """A book."""

    title: str
    isbn13: int | None = None
    publisher: str | None = None
    work_editions: list[str] = Field(default_factory=list)
    medium: BookMedium = BookMedium.UNSPECIFIED
    binding: BookBinding = BookBinding.UNSPECIFIED
    owners: list[str] | None = None

    @override
    def _get_details(self) -> list[str]:
        """Get the details for this object."""
        return [
            search_detail_for_obj_list(
                'Contributors', 'name', self.contributor_objs
            ),
            search_detail_for_obj('Publisher', 'name', self.publisher_obj),
            search_detail_for_obj('Imprint', 'imprint', self.publisher_obj),
            transformed_search_detail('ISBN', self.isbn13, _format_isbn),
            search_detail_for_enum('Medium', self.medium),
            search_detail_for_enum('Binding', self.binding),
            search_detail_for_obj_list(
                'Works', 'title', self.work_edition_objs
            ),
            search_detail_for_obj_list(
                'Collections', 'name', self.collection_objs
            ),
        ]

    @override
    def _get_search_terms(self) -> list[str]:
        """Get the search terms for this object."""
        return [str(self.isbn13)] if self.isbn13 is not None else []

    # Relationships (real objects)
    work_edition_objs: list[WorkEdition] = Field(
        default_factory=list, exclude=True
    )
    publisher_obj: BookPublisher = Field(default_factory=list, exclude=True)
    collection_objs: list[BookCollection] = Field(
        default_factory=list, exclude=True
    )
    owner_objs: list[Owner] = Field(default_factory=list, exclude=True)
    reading_session_objs: list[ReadingSession] = Field(
        default_factory=list, exclude=True
    )

    resolvable_fields: ClassVar[list[ResolvableField]] = [
        ResolvableField('labels', 'label_objs', 'many-to-many', 'book_objs'),
        ResolvableField(
            'publisher', 'publisher_obj', 'one-to-many', 'book_objs'
        ),
        ResolvableField(
            'work_editions', 'work_edition_objs', 'many-to-many', 'book_objs'
        ),
        ResolvableField('owners', 'owner_objs', 'many-to-many', 'book_objs'),
    ]

    @property
    def contributor_objs(self) -> list[Contributor]:
        """Get a list of all contributors in this model."""
        all_contribs: list[Contributor] = []
        for work_edition in self.work_edition_objs:
            if work_edition.work_obj:
                all_contribs.extend(work_edition.work_obj.author_objs)
            all_contribs.extend(work_edition.illustrator_objs)
            all_contribs.extend(work_edition.translator_objs)

        rv: list[Contributor] = []
        for contributor in all_contribs:
            if contributor not in rv:
                rv.append(contributor)
        return rv

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


@register_model('reading_session')
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
    work_edition_obj: WorkEdition | None = Field(default=None, exclude=True)
    book_obj: Book | None = Field(default=None, exclude=True)

    resolvable_fields: ClassVar[list[ResolvableField]] = [
        ResolvableField(
            'labels', 'label_objs', 'many-to-many', 'reading_sessions_objs'
        ),
        ResolvableField(
            'work_edition',
            'work_edition_obj',
            'one-to-many',
            'reading_session_objs',
        ),
        ResolvableField(
            'book', 'book_obj', 'one-to-many', 'reading_session_objs'
        ),
    ]

    @override
    @property
    def linting_findings(self) -> list[LintingFinding]:
        """Get linting findings for the model."""
        rv = super().linting_findings

        if all(
            [
                self.state != ReadingState.FINISHED,
                self.state != ReadingState.DID_NOT_FINISH,
                self.enddate is not None,
            ]
        ):
            rv.append(
                LintingFinding(
                    id='reading-session-enddate-set',
                    resource_id=self.id,
                    error='Enddate set but work not '
                    '"Finished" or "Did not finish".',
                )
            )

        if self.startdate and self.enddate and self.startdate > self.enddate:
            rv.append(
                LintingFinding(
                    id='reading-session-enddate-smaller-then-startdate',
                    resource_id=self.id,
                    error='Enddate is bigger then startdate',
                )
            )

        return rv

    @override
    def _get_resource_type(self) -> str:
        """Get the resource type for this object."""
        return 'Reading session'

    @override
    def _get_title(self) -> str:
        """Get a display title for this reading session."""
        if self.work_edition_obj:
            return self.work_edition_obj.title
        if self.book_obj:
            return self.book_obj.title
        return self.id or 'Reading session'

    @override
    def _get_details(self) -> list[str]:
        """Get the details for this object."""
        return [
            search_detail_for_obj(
                'Work edition', 'title', self.work_edition_obj
            ),
            search_detail_for_obj('Book', 'title', self.book_obj),
            search_detail_for_enum('State', self.state),
            search_detail(
                'Start date',
                str(self.startdate) if self.startdate else None,
            ),
            search_detail(
                'End date', str(self.enddate) if self.enddate else None
            ),
            search_detail(
                'Work rating',
                str(self.work_rating.rating) if self.work_rating else None,
            ),
            search_detail(
                'Work rating note',
                self.work_rating.note if self.work_rating else None,
            ),
            search_detail(
                'Book rating',
                str(self.book_rating.rating) if self.book_rating else None,
            ),
            search_detail(
                'Book rating note',
                self.book_rating.note if self.book_rating else None,
            ),
        ]

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


@register_model('label')
class Label(ResourceBase):
    """A label."""

    name: str

    # Relationships (real objects)
    contributor_objs: list[Contributor] = Field(
        default_factory=list, exclude=True
    )
    work_objs: list[Work] = Field(default_factory=list, exclude=True)
    work_edition_objs: list[WorkEdition] = Field(
        default_factory=list, exclude=True
    )
    series_objs: list[Series] = Field(default_factory=list, exclude=True)
    reading_list_objs: list[ReadingList] = Field(
        default_factory=list, exclude=True
    )
    reading_session_objs: list[ReadingSession] = Field(
        default_factory=list, exclude=True
    )
    book_objs: list[Book] = Field(default_factory=list, exclude=True)
    owner_objs: list[Owner] = Field(default_factory=list, exclude=True)
    book_collection_objs: list[BookCollection] = Field(
        default_factory=list, exclude=True
    )


class ReadingListItem(BaseModel):
    """A item in a reading list."""

    order: int
    work: str

    # Relationships (real objects)
    work_obj: Work | None = Field(default=None, exclude=True)

    # Resolve definitions
    resolvable_fields: ClassVar[list[ResolvableField]] = [
        ResolvableField('work', 'work_obj', 'one-to-none'),
    ]


@register_model('reading_list')
class ReadingList(LabelledResource):
    """A list of resources."""

    name: str
    works: list[ReadingListItem] = Field(default_factory=list)

    resolvable_children: ClassVar[tuple[str, ...]] = ('works',)

    resolvable_fields: ClassVar[list[ResolvableField]] = [
        ResolvableField(
            'labels', 'label_objs', 'many-to-many', 'reading_list_objs'
        )
    ]

    @override
    @property
    def linting_findings(self) -> list[LintingFinding]:
        """Get linting findings for the model."""
        rv = super().linting_findings

        orders = [work.order for work in self.works]
        double = set([order for order in orders if orders.count(order) > 1])

        for double_order in double:
            rv.append(
                LintingFinding(
                    id='reading-list-double-order',
                    resource_id=self.id,
                    error=f'Order {double_order} is double in the list.',
                )
            )

        all_works = [
            work.work_obj.id or ''
            for work in self.works
            if work.work_obj is not None
        ]
        double_works: set[str] = set(
            [work for work in all_works if all_works.count(work) > 1]
        )

        for double_work in double_works:
            rv.append(
                LintingFinding(
                    id='reading-list-double-work',
                    resource_id=self.id,
                    error=f'Work "{double_work}" is double in the list.',
                )
            )

        return rv

    @override
    def _get_resource_type(self) -> str:
        """Get the resource type for this object."""
        return 'Reading list'

    @override
    def _get_details(self) -> list[str]:
        """Get the details for this object."""
        works = [
            item.work_obj for item in self.works if item.work_obj is not None
        ]
        return [search_detail_for_obj_list('Works', 'title', works)]

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


@register_model('owner')
class Owner(LabelledResource):
    """Model for a owner."""

    name: str
    owner_type: OwnerType = OwnerType.UNSPECIFIED
    availability: Availability = Availability.NOT_AVAILABLE

    # Relationships (real objects)
    book_objs: list[Book] = Field(default_factory=list, exclude=True)

    resolvable_fields: ClassVar[list[ResolvableField]] = [
        ResolvableField('labels', 'label_objs', 'many-to-many', 'owner_objs')
    ]

    @override
    @property
    def linting_findings(self) -> list[LintingFinding]:
        """Get linting findings for the model."""
        rv = super().linting_findings
        if (
            self.owner_type in (OwnerType.STORE, OwnerType.LIBRARY)
            and self.availability == Availability.INDIRECTLY_AVAILABLE
        ):
            rv.append(
                LintingFinding(
                    id='owner-store-library-indirect',
                    resource_id=self.id,
                    error='A "store" or "library" should never '
                    'be "indirectly" available.',
                )
            )
        return rv

    @override
    def _get_details(self) -> list[str]:
        """Get the details for this object."""
        return [
            search_detail_for_enum('Type', self.owner_type),
            search_detail_for_enum('Availability', self.availability),
            search_detail_for_obj_list('Books', 'title', self.book_objs),
        ]


class SeriesItem(BaseModel):
    """A item in a serie."""

    number: int
    work: str

    # Relationships (real objects)
    work_obj: Work | None = Field(default=None, exclude=True)
    series_obj: Series | None = Field(default=None, exclude=True)

    # Resolve definitions
    resolvable_fields: ClassVar[list[ResolvableField]] = [
        ResolvableField('work', 'work_obj', 'one-to-many', 'series_objs'),
    ]


@register_model('series')
class Series(LabelledResource):
    """A serie of works."""

    name: str
    works: list[SeriesItem] = Field(default_factory=list)

    resolvable_children: ClassVar[tuple[str, ...]] = ('works',)

    resolvable_fields: ClassVar[list[ResolvableField]] = [
        ResolvableField('labels', 'label_objs', 'many-to-many', 'series_objs')
    ]

    @override
    @property
    def linting_findings(self) -> list[LintingFinding]:
        """Get linting findings for the model."""
        rv = super().linting_findings

        orders = [work.number for work in self.works]
        double = set([order for order in orders if orders.count(order) > 1])

        for double_order in double:
            rv.append(
                LintingFinding(
                    id='series-double-number',
                    resource_id=self.id,
                    error=f'Number {double_order} is double in the series.',
                )
            )

        all_works = [
            work.work_obj.id or ''
            for work in self.works
            if work.work_obj is not None
        ]
        double_works: set[str] = set(
            [work for work in all_works if all_works.count(work) > 1]
        )

        for double_work in double_works:
            rv.append(
                LintingFinding(
                    id='series-double-work',
                    resource_id=self.id,
                    error=f'Work "{double_work}" is double in the series.',
                )
            )

        return rv

    @override
    def _get_details(self) -> list[str]:
        """Get the details for this object."""
        works = [
            item.work_obj for item in self.works if item.work_obj is not None
        ]
        return [search_detail_for_obj_list('Works', 'title', works)]

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


# relac_models: dict[str, type[ResourceBase]] = {'contributor': Contributor}
