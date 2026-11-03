"""Module with the Database class."""

from collections.abc import Sequence

from relac.model import (
    Author,
    Book,
    BookCollection,
    BookPublisher,
    Label,
    Owner,
    ReadingList,
    ResourceBase,
    Series,
    Work,
    WorkEdition,
)


class Database:
    """Class for the database."""

    def __init__(self) -> None:
        """Create empty data."""
        self._authors: dict[str, Author] = {}
        self._works: dict[str, Work] = {}
        self._work_editions: dict[str, WorkEdition] = {}
        self._books: dict[str, Book] = {}
        self._book_publishers: dict[str, BookPublisher] = {}
        self._book_collections: dict[str, BookCollection] = {}
        self._labels: dict[str, Label] = {}
        self._reading_lists: dict[str, ReadingList] = {}
        self._owners: dict[str, Owner] = {}
        self._series: dict[str, Series] = {}

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

    def _converge_works(self) -> None:
        """Converge all works."""
        for obj in self._works.values():
            for author in obj.authors:
                author_obj = self._authors.get(author)
                if not author_obj:
                    # TODO: Custom error
                    raise ValueError(
                        f'Author with id "{author}" doesn\'t exist'
                    )
                obj.author_objs.append(author_obj)
                author_obj.work_objs.append(obj)

    def _converge_books(self) -> None:
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
                    for author in work_edition_obj.work_obj.author_objs:
                        if not any(
                            book_author.id == author.id
                            for book_author in obj.author_objs
                        ):
                            obj.author_objs.append(author)
                        if not any(
                            book.id == obj.id for book in author.book_objs
                        ):
                            author.book_objs.append(obj)

            for owner in obj.owners or []:
                owner_obj = self._owners.get(owner)
                if not owner_obj:
                    # TODO: Custom error
                    raise ValueError(f'Owner with id "{owner}" doesn\'t exist')
                obj.owner_objs.append(owner_obj)
                owner_obj.book_objs.append(obj)

    def _converge_book_collections(self) -> None:
        """Converge all book collections."""
        for obj in self._book_collections.values():
            for book in obj.books:
                book_obj = self._books.get(book)
                if book_obj is None:
                    raise ValueError(f'Book with id "{book}" doesn\'t exist')
                obj.book_objs.append(book_obj)
                book_obj.collection_objs.append(obj)

    def _converge_reading_lists(self) -> None:
        """Converge all book reading lists."""
        for obj in self._reading_lists.values():
            for work in obj.works:
                work_obj = self._works.get(work.work)
                if work_obj is None:
                    raise ValueError(f'Work with id "{work}" doesn\'t exist')
                work.work_obj = work_obj

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

    def converge(self) -> None:
        """Converge all objects."""
        self._converge_works()
        self._converge_works_editions()
        self._converge_books()
        self._converge_book_collections()
        self._converge_reading_lists()
        self._converge_series()

    def add_author(self, id: str, obj: Author) -> None:
        """Add a author to the database."""
        self._add_object(id, obj, self._authors)

    def get_authors(self) -> Sequence[Author]:
        """Get all authors in the database."""
        return list(self._authors.values())

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
