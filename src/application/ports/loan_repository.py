"""
Port: LoanRepository. See book_repository.py for the general explanation
of why this is a Protocol, not a concrete class.

Note where "is this book available" lives: on this port, not on
BookRepository. Availability is a question about active LOANS for an
ISBN, not a property of the Book itself (see docs/domain-design.md
section 3.2, which flagged this as an open design question) -- this is
the team's answer to that question, made concrete here so CheckoutBook
can actually be built. Worth confirming with Marion that this is the
agreed resolution, not a unilateral call that stands unquestioned.
"""
from datetime import date
from typing import Protocol

from domain.entities.loan import Loan


class LoanRepository(Protocol):
    def count_active_loans_for_borrower(self, borrower_id: int) -> int:
        """How many currently-unreturned loans this borrower has."""
        ...

    def is_book_available(self, isbn: str) -> bool:
        """True if this ISBN has no currently-unreturned loan against it."""
        ...

    def create_loan(self, isbn: str, borrower_id: int, title: str, date_out: date, due_date: date) -> Loan:
        """Persist a new loan and return the created domain Loan."""
        ...
