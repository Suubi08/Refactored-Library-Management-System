"""
Port: BorrowerRepository. See book_repository.py for the general
explanation of why this is a Protocol, not a concrete class.
"""
from typing import Optional, Protocol

from domain.entities.borrower import Borrower


class BorrowerRepository(Protocol):
    def get_by_id(self, borrower_id: int) -> Optional[Borrower]:
        """Return the Borrower with this id, or None if they don't exist."""
        ...
