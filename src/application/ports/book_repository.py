"""
Port: BookRepository.

This is an interface, not an implementation. CheckoutBook depends on
this Protocol, never on sqlite3 or the `database` package directly.
`infrastructure/sqlite/book_repository.py` Patricia provides a
concrete class that satisfies this shape, by wrapping the existing
`database/query/book.py` functions -- no SQL needs to be rewritten,
only adapted to this interface.

Using typing.Protocol (structural typing) rather than abc.ABC means a
class satisfies this interface just by having matching methods -- no
explicit inheritance required. This keeps the SQLite implementation
free to also be a thin wrapper around existing module-level functions
if that's more convenient than a from-scratch class.
"""
from typing import Optional, Protocol

from domain.entities.book import Book


class BookRepository(Protocol):
    def get_by_isbn(self, isbn: str) -> Optional[Book]:
        """Return the Book for this ISBN, or None if it doesn't exist."""
        ...
