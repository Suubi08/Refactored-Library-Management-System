"""
Fake (in-memory) repositories, satisfying the Protocols in
application/ports/. Used ONLY in tests -- these are not what ships in
the real app (that's infrastructure/sqlite/, Patricia's part).

This is the concrete demonstration the Phase 4 guide calls for:
"CheckoutBook -> Fake repositories -> Test business rules. Now you can
demonstrate that the use case can be tested without SQLite." These fakes
hold plain Python dicts/lists in memory -- no database, no tmp_path, no
CSV import, nothing but the objects the test itself put there.
"""
from datetime import date
from typing import Optional

from domain.entities.book import Book
from domain.entities.borrower import Borrower
from domain.entities.loan import Loan


class FakeBookRepository:
    def __init__(self, books: Optional[list[Book]] = None):
        self._books = {b.isbn: b for b in (books or [])}

    def get_by_isbn(self, isbn: str) -> Optional[Book]:
        return self._books.get(isbn)


class FakeBorrowerRepository:
    def __init__(self, borrowers: Optional[list[Borrower]] = None):
        self._borrowers = {b.id: b for b in (borrowers or [])}

    def get_by_id(self, borrower_id: int) -> Optional[Borrower]:
        return self._borrowers.get(borrower_id)


class FakeLoanRepository:
    def __init__(self, loans: Optional[list[Loan]] = None):
        self._loans: list[Loan] = list(loans or [])
        self._next_id = (max((l.id for l in self._loans), default=0)) + 1

    def count_active_loans_for_borrower(self, borrower_id: int) -> int:
        return sum(1 for l in self._loans if l.borrower_id == borrower_id and not l.is_returned)

    def is_book_available(self, isbn: str) -> bool:
        return not any(l.isbn == isbn and not l.is_returned for l in self._loans)

    def create_loan(self, isbn: str, borrower_id: int, title: str, date_out: date, due_date: date) -> Loan:
        loan = Loan(
            id=self._next_id, isbn=isbn, borrower_id=borrower_id, title=title,
            date_out=date_out, due_date=due_date, date_in=None,
        )
        self._loans.append(loan)
        self._next_id += 1
        return loan

    # test-only convenience, not part of the LoanRepository port
    def all_loans(self) -> list[Loan]:
        return list(self._loans)


class FakeFineRepository:
    def __init__(self, borrowers_with_unpaid_fines: Optional[set[int]] = None):
        self._borrowers_with_unpaid_fines = set(borrowers_with_unpaid_fines or set())

    def has_unpaid_fines(self, borrower_id: int) -> bool:
        return borrower_id in self._borrowers_with_unpaid_fines
