"""Module with the Database class."""

from collections.abc import Sequence

from relac.model import (
    Book,
    BookCollection,
    BookPublisher,
    Character,
    Contributor,
    Label,
    Location,
    Owner,
    Quote,
    ReadingList,
    ReadingSession,
    RelacConfig,
    ResourceBase,
    Series,
    StorySetting,
    Work,
    WorkCharacter,
    WorkEdition,
)


class Database:
    """Class for the database."""

    def __init__(self) -> None:
        """Create empty data."""
        self._relac_config: RelacConfig | None = None
        self._contributors: dict[str, Contributor] = {}
        self._works: dict[str, Work] = {}
        self._work_editions: dict[str, WorkEdition] = {}
        self._books: dict[str, Book] = {}
        self._book_publishers: dict[str, BookPublisher] = {}
        self._book_collections: dict[str, BookCollection] = {}
        self._labels: dict[str, Label] = {}
        self._reading_lists: dict[str, ReadingList] = {}
        self._owners: dict[str, Owner] = {}
        self._series: dict[str, Series] = {}
        self._reading_sessions: dict[str, ReadingSession] = {}
        self._locations: dict[str, Location] = {}
        self._characters: dict[str, Character] = {}
        self._quotes: dict[str, Quote] = {}

    def _id_exists[ResourceModel: ResourceBase](
        self, id: str, collection: dict[str, ResourceModel]
    ) -> bool:
        """Check if an specific ID already exists."""
        return collection.get(id) is not None

    def _add_object[ResourceModel: ResourceBase](
        self, id: str, obj: ResourceModel, collection: dict[str, ResourceModel]
    ) -> None:
        """Add a object to the database."""
        if self._id_exists(id, collection):
            raise ValueError(f'Object with it "{id}" already exists.')
        collection[id] = obj

    def _converge_works_editions(self) -> None:
        """Converge all work editions."""
        for obj in self._work_editions.values():
            work_obj = self._works.get(obj.work)
            if not work_obj:
                # TODO: Custom error
                raise ValueError(f'Work with id "{obj.work}" doesn\'t exist')
            obj.work_obj = work_obj
            work_obj.edition_objs.append(obj)

            for contributor_ids, contributor_objs, is_illustrator in (
                (obj.illustrators, obj.illustrator_objs, True),
                (obj.translators, obj.translator_objs, False),
            ):
                for contributor_id in contributor_ids or []:
                    contributor = self._contributors.get(contributor_id)
                    if contributor is None:
                        raise ValueError(
                            f'Contributor with id "{contributor_id}" '
                            "doesn't exist"
                        )
                    contributor_objs.append(contributor)
                    if is_illustrator:
                        contributor.illustrator_work_edition_objs.append(obj)
                    else:
                        contributor.translator_work_edition_objs.append(obj)

            obj.label_objs = self._get_labels(obj.labels)
            for label in obj.label_objs:
                label.work_edition_objs.append(obj)

    def _converge_works(self) -> None:
        """Converge all works."""
        for obj in self._works.values():
            for contributor_id in obj.authors:
                contributor = self._contributors.get(contributor_id)
                if not contributor:
                    # TODO: Custom error
                    raise ValueError(
                        f'Contributor with id "{contributor_id}" doesn\'t exist'
                    )
                obj.author_objs.append(contributor)
                contributor.work_objs.append(obj)

            obj.label_objs = self._get_labels(obj.labels)
            for label in obj.label_objs:
                label.work_objs.append(obj)

            if obj.literary_analysis is not None:
                if obj.literary_analysis.setting:
                    self._converge_story_setting(
                        obj.literary_analysis.setting, obj
                    )

                for character_obj in obj.literary_analysis.characters or []:
                    self._converge_work_character(character_obj, obj)

                if obj.literary_analysis.narrator:
                    character_id = obj.literary_analysis.narrator.character
                    if character_id:
                        character_obj = self._characters.get(character_id)
                        if not character_obj:
                            # TODO: Custom error
                            raise ValueError(
                                f'Character with id "{character_id}" '
                                "doesn't exist"
                            )
                        obj.literary_analysis.narrator.character_obj = (
                            character_obj
                        )

    def _converge_books(self) -> None:  # noqa: PLR0912
        """Converge all books."""
        for obj in self._books.values():
            if obj.publisher is not None:
                publisher_obj = self._book_publishers.get(obj.publisher)
                if not publisher_obj:
                    # TODO: Custom error
                    raise ValueError(
                        f'Publisher with id "{obj.publisher}" doesn\'t exist'
                    )
                obj.publisher_obj = publisher_obj
                publisher_obj.book_objs.append(obj)

            for work_edition in obj.work_editions:
                work_edition_obj = self._work_editions.get(work_edition)
                if work_edition_obj is None:
                    raise ValueError(
                        f'WorkEdition with id "{work_edition}" doesn\'t exist'
                    )
                obj.work_edition_objs.append(work_edition_obj)
                work_edition_obj.book_objs.append(obj)
                if work_edition_obj.work_obj:
                    work_obj = work_edition_obj.work_obj
                    if not any(
                        book.id == obj.id for book in work_obj.book_objs
                    ):
                        work_obj.book_objs.append(obj)
                edition_contributors = [
                    *(
                        work_edition_obj.work_obj.author_objs
                        if work_edition_obj.work_obj
                        else []
                    ),
                    *work_edition_obj.illustrator_objs,
                    *work_edition_obj.translator_objs,
                ]
                for contributor in edition_contributors:
                    if not any(
                        book_contributor.id == contributor.id
                        for book_contributor in obj.contributor_objs
                    ):
                        obj.contributor_objs.append(contributor)
                    if not any(
                        book.id == obj.id for book in contributor.book_objs
                    ):
                        contributor.book_objs.append(obj)

            for owner in obj.owners or []:
                owner_obj = self._owners.get(owner)
                if not owner_obj:
                    # TODO: Custom error
                    raise ValueError(f'Owner with id "{owner}" doesn\'t exist')
                obj.owner_objs.append(owner_obj)
                owner_obj.book_objs.append(obj)

            obj.label_objs = self._get_labels(obj.labels)
            for label in obj.label_objs:
                label.book_objs.append(obj)

    def _converge_book_collections(self) -> None:
        """Converge all book collections."""
        for obj in self._book_collections.values():
            for book in obj.books:
                book_obj = self._books.get(book)
                if book_obj is None:
                    raise ValueError(f'Book with id "{book}" doesn\'t exist')
                obj.book_objs.append(book_obj)
                book_obj.collection_objs.append(obj)

            obj.label_objs = self._get_labels(obj.labels)
            for label in obj.label_objs:
                label.book_collection_objs.append(obj)

    def _converge_reading_lists(self) -> None:
        """Converge all book reading lists."""
        for obj in self._reading_lists.values():
            for work in obj.works:
                work_obj = self._works.get(work.work)
                if work_obj is None:
                    raise ValueError(f'Work with id "{work}" doesn\'t exist')
                work.work_obj = work_obj

            obj.label_objs = self._get_labels(obj.labels)
            for label in obj.label_objs:
                label.reading_list_objs.append(obj)

    def _converge_series(self) -> None:
        """Converge all book reading lists."""
        for obj in self._series.values():
            for serie_item in obj.works:
                work_obj = self._works.get(serie_item.work)
                if work_obj is None:
                    raise ValueError(
                        f'Work with id "{serie_item}" doesn\'t exist'
                    )
                serie_item.work_obj = work_obj
                work_obj.series_objs.append(obj)

            obj.label_objs = self._get_labels(obj.labels)
            for label in obj.label_objs:
                label.series_objs.append(obj)

    def _converge_reading_sessions(self) -> None:
        """Converge all reading sessions."""
        for obj in self._reading_sessions.values():
            book_obj = self._books.get(obj.book)
            if book_obj is None:
                raise ValueError(f'Book with id "{obj.book}" doesn\'t exist')

            work_edition_obj = self._work_editions.get(obj.work_edition)
            if work_edition_obj is None:
                raise ValueError(
                    f'Work edition with id "{obj.work_edition}" doesn\'t exist'
                )

            obj.book_obj = book_obj
            obj.work_edition_obj = work_edition_obj

            book_obj.reading_session_objs.append(obj)
            work_edition_obj.reading_session_objs.append(obj)

            obj.label_objs = self._get_labels(obj.labels)
            for label in obj.label_objs:
                label.reading_session_objs.append(obj)

    def _converge_relac_config(self) -> None:
        """Converge the RelacConfig object."""
        if self._relac_config is None:
            # TODO: Custom error
            raise ValueError('Relac config is not set.')

        if self._relac_config.owner:
            owner_obj = self._owners.get(self._relac_config.owner)
            if not owner_obj:
                # TODO: Custom error
                raise ValueError(
                    f'Owner "{self._relac_config.owner}" doesn\'t exists'
                )
            self._relac_config.owner_obj = owner_obj

    def _get_labels(self, label_ids: list[str] | None) -> list[Label]:
        """Get a list of `Label` objects from their ID's."""
        rv: list[Label] = []
        for label_id in label_ids or []:
            label_obj = self._labels.get(label_id)
            if label_obj is None:
                raise ValueError(f'Label with id "{label_id}" doesn\'t exist')
            rv.append(label_obj)
        return rv

    def _converge_contributors(self) -> None:
        """Converge Contributors objects."""
        for contributor in self._contributors.values():
            contributor.label_objs = self._get_labels(contributor.labels)
            for label in contributor.label_objs:
                label.contributor_objs.append(contributor)

    def _converge_owners(self) -> None:
        """Converge Owners objects."""
        for contributor in self._owners.values():
            contributor.label_objs = self._get_labels(contributor.labels)
            for label in contributor.label_objs:
                label.owner_objs.append(contributor)

    def _converge_story_setting(
        self, obj: StorySetting, work_obj: Work
    ) -> None:
        """Converge StorySetting objects."""
        for location_id in obj.locations or []:
            location_obj = self._locations.get(location_id)
            if location_obj is None:
                raise ValueError(
                    f'Location with id "{location_id}" doesn\'t exist'
                )
            obj.location_objs.append(location_obj)
            if not any(
                related_work is work_obj
                for related_work in location_obj.work_objs
            ):
                location_obj.work_objs.append(work_obj)

    def _converge_work_character(
        self, obj: WorkCharacter, work_obj: Work
    ) -> None:
        """Converge a work-character relation."""
        character_obj = self._characters.get(obj.character)
        if character_obj is None:
            raise ValueError(
                f'Character with id "{obj.character}" doesn\'t exist'
            )
        obj.character_obj = character_obj
        obj.work_obj = work_obj
        if not any(
            work_character is obj
            for work_character in character_obj.work_character_objs
        ):
            character_obj.work_character_objs.append(obj)

    def _converge_quotes(self) -> None:
        """Converge Owners objects."""
        for quote in self._quotes.values():
            contributor_obj = self._contributors.get(quote.contributor)
            if contributor_obj is None:
                raise ValueError(
                    f'Contributor with id "{quote.contributor}" doesn\'t exist'
                )
            quote.contributor_obj = contributor_obj
            if not any(
                related_quote is quote
                for related_quote in contributor_obj.quote_objs
            ):
                contributor_obj.quote_objs.append(quote)

            if quote.character:
                character_obj = self._characters.get(quote.character)
                if character_obj is None:
                    raise ValueError(
                        f'Character with id "{quote.character}" doesn\'t exist'
                    )
                quote.character_obj = character_obj
                if not any(
                    related_quote is quote
                    for related_quote in character_obj.quote_objs
                ):
                    character_obj.quote_objs.append(quote)

            if quote.work:
                work_obj = self._works.get(quote.work)
                if work_obj is None:
                    raise ValueError(
                        f'Work with id "{quote.work}" doesn\'t exist'
                    )
                quote.work_obj = work_obj
                if work_obj.literary_analysis:
                    work_obj.literary_analysis.quote_objs.append(quote)

    def converge(self) -> None:
        """Converge all objects."""
        self._converge_relac_config()
        self._converge_works()
        self._converge_works_editions()
        self._converge_books()
        self._converge_book_collections()
        self._converge_reading_lists()
        self._converge_series()
        self._converge_reading_sessions()
        self._converge_contributors()
        self._converge_owners()
        self._converge_quotes()

    def add_contributor(self, id: str, obj: Contributor) -> None:
        """Add a contributor to the database."""
        self._add_object(id, obj, self._contributors)

    def get_contributors(self) -> Sequence[Contributor]:
        """Get all contributors in the database."""
        return list(self._contributors.values())

    def add_work(self, id: str, obj: Work) -> None:
        """Add a work to the database."""
        self._add_object(id, obj, self._works)

    def get_works(self) -> Sequence[Work]:
        """Get all works in the database."""
        return list(self._works.values())

    def add_work_edition(self, id: str, obj: WorkEdition) -> None:
        """Add a work edition to the database."""
        self._add_object(id, obj, self._work_editions)

    def get_work_editions(self) -> Sequence[WorkEdition]:
        """Get all work editions in the database."""
        return list(self._work_editions.values())

    def add_book(self, id: str, obj: Book) -> None:
        """Add a book to the database."""
        self._add_object(id, obj, self._books)

    def get_books(self) -> Sequence[Book]:
        """Get all books in the database."""
        return list(self._books.values())

    def add_book_publisher(self, id: str, obj: BookPublisher) -> None:
        """Add a book publisher to the database."""
        self._add_object(id, obj, self._book_publishers)

    def get_book_publishers(self) -> Sequence[BookPublisher]:
        """Get all book publishers in the database."""
        return list(self._book_publishers.values())

    def add_book_collections(self, id: str, obj: BookCollection) -> None:
        """Add a book collection to the database."""
        self._add_object(id, obj, self._book_collections)

    def get_book_collections(self) -> list[BookCollection]:
        """Get all book collections in the database."""
        return list(self._book_collections.values())

    def add_label(self, id: str, obj: Label) -> None:
        """Add a label to the database."""
        self._add_object(id, obj, self._labels)

    def get_labels(self) -> Sequence[Label]:
        """Get all label in the database."""
        return list(self._labels.values())

    def add_reading_list(self, id: str, obj: ReadingList) -> None:
        """Add a reading list to the database."""
        self._add_object(id, obj, self._reading_lists)

    def get_reading_lists(self) -> list[ReadingList]:
        """Get all reading lists in the database."""
        return list(self._reading_lists.values())

    def add_owner(self, id: str, obj: Owner) -> None:
        """Add a owner to the database."""
        self._add_object(id, obj, self._owners)

    def get_owners(self) -> list[Owner]:
        """Get all owners in the database."""
        return list(self._owners.values())

    def add_series(self, id: str, obj: Series) -> None:
        """Add a series to the database."""
        self._add_object(id, obj, self._series)

    def get_series(self) -> list[Series]:
        """Get all series in the database."""
        return list(self._series.values())

    def add_reading_session(self, id: str, obj: ReadingSession) -> None:
        """Add a reading session to the database."""
        self._add_object(id, obj, self._reading_sessions)

    def get_reading_sessions(self) -> list[ReadingSession]:
        """Get all reading sessiosn in the database."""
        return list(self._reading_sessions.values())

    def set_relac_config(self, config: RelacConfig) -> None:
        """Set the Relac config for the database."""
        self._relac_config = config

    def get_relac_config(self) -> RelacConfig:
        """Get the Relac config."""
        if self._relac_config is None:
            # TODO: Custom error
            raise ValueError('Relac config is not set.')
        return self._relac_config

    def add_location(self, id: str, obj: Location) -> None:
        """Add a location to the database."""
        self._add_object(id, obj, self._locations)

    def get_locations(self) -> list[Location]:
        """Get all locations in the database."""
        return list(self._locations.values())

    def add_character(self, id: str, obj: Character) -> None:
        """Add a character to the database."""
        self._add_object(id, obj, self._characters)

    def get_characters(self) -> list[Character]:
        """Get all characters in the database."""
        return list(self._characters.values())

    def add_quote(self, id: str, obj: Quote) -> None:
        """Add a quote to the database."""
        self._add_object(id, obj, self._quotes)

    def get_quotes(self) -> list[Quote]:
        """Get all quotes in the database."""
        return list(self._quotes.values())
