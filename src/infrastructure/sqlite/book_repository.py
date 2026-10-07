"""
SQLite adapter for the BookRepository port (application/ports/book_repository.py).

It does no SQL of its own. It asks the existing database.get_book_by_isbn()
and reshapes the answer into a plain domain Book.

Note: `import database` comes first on purpose. Importing `models` before
`database` triggers the circular-import crash (see Phase 1 findings).
"""
from typing import Optional

import database as db
from domain.entities.book import Book


class SqliteBookRepository:
    def get_by_isbn(self, isbn: str) -> Optional[Book]:
        result = db.get_book_by_isbn(isbn)      # a BookSearchResult, or None

        if result is None:
            return None

        return Book(isbn=result.isbn, title=result.title)