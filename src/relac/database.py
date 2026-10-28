"""Module with the Database class."""

from relac.model import (
    Author,
    Book,
    BookCollection,
    BookPublisher,
    Label,
    ResourceBase,
    ResourceList,
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
        self._resource_lists: dict[str, ResourceList] = {}

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
                obj.authors_objs.append(author_obj)

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

    def _converge_book_collections(self) -> None:
        """Converge all book collections."""
        for obj in self._book_collections.values():
            for book in obj.books:
                book_obj = self._books.get(book)
                if book_obj is None:
                    raise ValueError(f'Book with id "{book}" doesn\'t exist')
                obj.book_objs.append(book_obj)
                book_obj.collection_objs.append(obj)

    def converge(self) -> None:
        """Converge all objects."""
        self._converge_works()
        self._converge_works_editions()
        self._converge_books()
        self._converge_book_collections()

    def add_author(self, id: str, obj: Author) -> None:
        """Add a author to the database."""
        self._add_object(id, obj, self._authors)

    def get_authors(self) -> dict[str, Author]:
        """Get all authors in the database."""
        return self._authors

    def add_work(self, id: str, obj: Work) -> None:
        """Add a work to the database."""
        self._add_object(id, obj, self._works)

    def get_works(self) -> dict[str, Work]:
        """Get all works in the database."""
        return self._works

    def add_work_edition(self, id: str, obj: WorkEdition) -> None:
        """Add a work edition to the database."""
        self._add_object(id, obj, self._work_editions)

    def get_work_editions(self) -> dict[str, WorkEdition]:
        """Get all work editions in the database."""
        return self._work_editions

    def add_book(self, id: str, obj: Book) -> None:
        """Add a book to the database."""
        self._add_object(id, obj, self._books)

    def get_books(self) -> dict[str, Book]:
        """Get all books in the database."""
        return self._books

    def add_book_publisher(self, id: str, obj: BookPublisher) -> None:
        """Add a book publisher to the database."""
        self._add_object(id, obj, self._book_publishers)

    def get_book_publishers(self) -> dict[str, BookPublisher]:
        """Get all book publishers in the database."""
        return self._book_publishers

    def add_book_collections(self, id: str, obj: BookCollection) -> None:
        """Add a book collection to the database."""
        self._add_object(id, obj, self._book_collections)

    def get_book_collections(self) -> dict[str, BookCollection]:
        """Get all book collections in the database."""
        return self._book_collections

    def add_label(self, id: str, obj: Label) -> None:
        """Add a label to the database."""
        self._add_object(id, obj, self._labels)

    def get_labels(self) -> dict[str, Label]:
        """Get all label in the database."""
        return self._labels

    def add_resource_list(self, id: str, obj: ResourceList) -> None:
        """Add a label to the database."""
        self._add_object(id, obj, self._resource_lists)

    def get_resource_lists(self) -> dict[str, ResourceList]:
        """Get all resource lists in the database."""
        return self._resource_lists
