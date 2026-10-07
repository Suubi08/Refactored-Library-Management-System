"""
Smoke tests for src/infrastructure/sqlite/ (the four SQLite repositories).

Each class is built against a REAL temporary database (the shared `test_db`
fixture, loaded with the real seed data) and each of its methods is called.
The point: prove the four classes really satisfy the ports and really talk to
SQLite, so the app can be wired to them.

(This folder has no __init__.py on purpose: tests/ and src/ must not share a
package name, or pytest imports the wrong one. See the Phase 4 notes.)
"""
import inspect
from datetime import date

import pytest

import database  # noqa: F401  -- must be imported before `models` (circular import)

from application.ports.book_repository import BookRepository
from application.ports.borrower_repository import BorrowerRepository
from application.ports.fine_repository import FineRepository
from application.ports.loan_repository import LoanRepository
from application.use_cases.checkout_book import CheckoutBook
from domain.entities.book import Book
from domain.entities.borrower import Borrower
from domain.entities.loan import Loan
from infrastructure.sqlite.book_repository import SqliteBookRepository
from infrastructure.sqlite.borrower_repository import SqliteBorrowerRepository
from infrastructure.sqlite.fine_repository import SqliteFineRepository
from infrastructure.sqlite.loan_repository import LoanCreationError, SqliteLoanRepository

# real rows from the seed data (data/book.csv and data/borrower.csv)
ISBN = "0002005018"
TITLE = "Clara Callan: A Novel"
OTHER_ISBN = "0195153448"
JUNE_15 = date(2025, 6, 15)
JUNE_29 = date(2025, 6, 29)


# ---------------------------------------------------------------------------
# Do the classes match the ports? (names and parameter names must be exact,
# because CheckoutBook calls them by name.)  No database needed.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("implementation, port", [
    (SqliteBookRepository, BookRepository),
    (SqliteBorrowerRepository, BorrowerRepository),
    (SqliteLoanRepository, LoanRepository),
    (SqliteFineRepository, FineRepository),
])
def test_each_class_has_every_method_its_port_declares_with_the_same_parameters(implementation, port):
    declared = [name for name, member in vars(port).items()
                if inspect.isfunction(member) and not name.startswith("_")]

    assert declared                                              # the port really declares something
    for name in declared:
        assert hasattr(implementation, name), f"{implementation.__name__} is missing {name}()"
        ours = list(inspect.signature(getattr(implementation, name)).parameters)
        theirs = list(inspect.signature(getattr(port, name)).parameters)
        assert ours == theirs, f"{name}(): {ours} does not match the port's {theirs}"


# ---------------------------------------------------------------------------
# One smoke test per class, against a real temp database
# ---------------------------------------------------------------------------
def test_book_repository_returns_a_domain_book_or_none(test_db):
    repository = SqliteBookRepository()

    assert repository.get_by_isbn(ISBN) == Book(isbn=ISBN, title=TITLE)
    assert repository.get_by_isbn("not-a-real-isbn") is None


def test_borrower_repository_returns_a_domain_borrower_or_none(test_db):
    repository = SqliteBorrowerRepository()

    assert repository.get_by_id(1) == Borrower(
        id=1,
        ssn="850-47-3740",
        name="Mark Morgan",
        address="5677 Coolidge Street, Plano, TX",
        phone="(469) 904-1438",
    )
    assert repository.get_by_id(999999) is None


def test_fine_repository_reports_unpaid_fines_only(test_db):
    repository = SqliteFineRepository()
    assert repository.has_unpaid_fines(1) is False               # nothing owed yet

    test_db.create_loan(ISBN, 1)
    loan = test_db.get_loans_by_borrower_id(1)[0]
    test_db.checkin(loan.id)
    test_db.set_fines([(loan.id, 25)])

    assert repository.has_unpaid_fines(1) is True                # owes money
    assert repository.has_unpaid_fines(2) is False               # a different borrower does not

    test_db.resolve_fines([loan.id])

    assert repository.has_unpaid_fines(1) is False               # paid -> no longer unpaid


def test_loan_repository_counts_checks_and_creates(test_db):
    repository = SqliteLoanRepository()
    assert repository.count_active_loans_for_borrower(1) == 0
    assert repository.is_book_available(ISBN) is True

    # a due date that is NOT 14 days out, to prove the repository uses the dates it is GIVEN
    given_due_date = date(2025, 7, 30)
    loan = repository.create_loan(ISBN, 1, TITLE, JUNE_15, given_due_date)

    # create_loan hands back a plain domain Loan
    assert type(loan) is Loan
    assert (loan.isbn, loan.borrower_id, loan.title) == (ISBN, 1, TITLE)
    assert (loan.date_out, loan.due_date, loan.date_in) == (JUNE_15, given_due_date, None)
    # ...and it was really SAVED with those values: the old API reads the same row back
    saved = test_db.get_loans_by_borrower_id(1)
    assert [(s.id, s.isbn, s.date_out, s.due_date, s.date_in) for s in saved] == [
        (loan.id, ISBN, JUNE_15, given_due_date, None)]
    # the other two questions now give different answers
    assert repository.count_active_loans_for_borrower(1) == 1
    assert repository.is_book_available(ISBN) is False
    assert repository.is_book_available(OTHER_ISBN) is True

    # a returned loan stops counting as active, and the book is free again
    test_db.checkin(loan.id)
    assert repository.count_active_loans_for_borrower(1) == 0
    assert repository.is_book_available(ISBN) is True

    # a save that the database rejects raises, instead of returning a half-made Loan
    with pytest.raises(LoanCreationError):
        repository.create_loan(None, 1, TITLE, JUNE_15, JUNE_29)


# ---------------------------------------------------------------------------
# All four together, driven by the real CheckoutBook use case
# ---------------------------------------------------------------------------
def test_checkout_book_works_end_to_end_on_the_sqlite_repositories(test_db):
    checkout = CheckoutBook(
        book_repository=SqliteBookRepository(),
        borrower_repository=SqliteBorrowerRepository(),
        loan_repository=SqliteLoanRepository(),
        fine_repository=SqliteFineRepository(),
    )

    result = checkout.execute(ISBN, 1, JUNE_15)

    assert result.status is True
    assert type(result.data) is Loan
    assert result.data.due_date == JUNE_29                       # 14 days after checkout
    assert [loan.id for loan in test_db.get_loans_by_borrower_id(1)] == [result.data.id]

    # and a rule still fires through the real database: the book is now out
    again = checkout.execute(ISBN, 2, JUNE_15)
    assert (again.status, again.message) == (False, "Book already checked out.")