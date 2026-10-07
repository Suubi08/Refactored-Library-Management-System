"""
Unit tests for application.use_cases.checkout_book.CheckoutBook.

Same spirit as tests/domain/test_loan_entity.py: no test_db, no SQLite,
no CSV import. Every repository here is a Fake (tests/application/fakes.py)
holding plain Python objects in memory. This is the proof that the use
case's business rules can be tested in isolation from persistence --
exactly the Clean Architecture demonstration the Phase 4 guide calls for.

Every rule and exact message string here is a direct port of the
existing characterization tests in tests/characterization/test_loans.py
-- same behaviour, same messages, different test speed and different
dependencies (none, here).
"""
from datetime import date, timedelta

from application.use_cases.checkout_book import CheckoutBook
from domain.entities.book import Book
from domain.entities.borrower import Borrower
from domain.entities.loan import Loan
from fake import (
    FakeBookRepository,
    FakeBorrowerRepository,
    FakeFineRepository,
    FakeLoanRepository,
)

TODAY = date(2025, 6, 15)


def make_checkout(books=None, borrowers=None, loans=None, unpaid_fine_borrowers=None):
    return CheckoutBook(
        book_repository=FakeBookRepository(books),
        borrower_repository=FakeBorrowerRepository(borrowers),
        loan_repository=FakeLoanRepository(loans),
        fine_repository=FakeFineRepository(unpaid_fine_borrowers),
    )


def test_successful_checkout_creates_a_loan_due_in_fourteen_days():
    checkout = make_checkout(
        books=[Book(isbn="111", title="Clean Architecture")],
        borrowers=[Borrower(id=1, ssn="123456789", name="Test", address="1 St", phone="1234567890")],
    )

    result = checkout.execute(isbn="111", borrower_id=1, current_date=TODAY)

    assert result.status is True
    assert result.message == "Checkout successful"
    assert result.data.due_date == TODAY + timedelta(days=14)
    assert result.data.date_in is None


def test_rejects_unknown_borrower():
    checkout = make_checkout(books=[Book(isbn="111", title="Clean Architecture")])

    result = checkout.execute(isbn="111", borrower_id=999, current_date=TODAY)

    assert result.status is False
    assert result.message == "Borrower not found"


def test_rejects_a_fourth_active_loan():
    borrower = Borrower(id=1, ssn="123456789", name="Test", address="1 St", phone="1234567890")
    existing_loans = [
        Loan(id=i, isbn=f"00{i}", borrower_id=1, title="Book", date_out=TODAY, due_date=TODAY + timedelta(days=14))
        for i in range(1, 4)  # 3 already-active loans
    ]
    checkout = make_checkout(
        books=[Book(isbn="999", title="Fourth Book")],
        borrowers=[borrower],
        loans=existing_loans,
    )

    result = checkout.execute(isbn="999", borrower_id=1, current_date=TODAY)

    assert result.status is False
    assert result.message == "Too many checkouts"


def test_rejects_unknown_book():
    checkout = make_checkout(
        borrowers=[Borrower(id=1, ssn="123456789", name="Test", address="1 St", phone="1234567890")],
    )

    result = checkout.execute(isbn="does-not-exist", borrower_id=1, current_date=TODAY)

    assert result.status is False
    assert result.message == "Book doesn't exist"


def test_rejects_a_book_that_is_already_checked_out():
    borrower = Borrower(id=1, ssn="123456789", name="Test", address="1 St", phone="1234567890")
    other_borrower_loan = Loan(
        id=1, isbn="111", borrower_id=2, title="Clean Architecture",
        date_out=TODAY, due_date=TODAY + timedelta(days=14),
    )
    checkout = make_checkout(
        books=[Book(isbn="111", title="Clean Architecture")],
        borrowers=[borrower],
        loans=[other_borrower_loan],
    )

    result = checkout.execute(isbn="111", borrower_id=1, current_date=TODAY)

    assert result.status is False
    assert result.message == "Book already checked out."


def test_rejects_a_borrower_with_unpaid_fines():
    checkout = make_checkout(
        books=[Book(isbn="111", title="Clean Architecture")],
        borrowers=[Borrower(id=1, ssn="123456789", name="Test", address="1 St", phone="1234567890")],
        unpaid_fine_borrowers={1},
    )

    result = checkout.execute(isbn="111", borrower_id=1, current_date=TODAY)

    assert result.status is False
    assert result.message == "Borrower has pending fines."


def test_a_returned_book_can_be_checked_out_again():
    borrower = Borrower(id=1, ssn="123456789", name="Test", address="1 St", phone="1234567890")
    returned_loan = Loan(
        id=1, isbn="111", borrower_id=2, title="Clean Architecture",
        date_out=TODAY - timedelta(days=20), due_date=TODAY - timedelta(days=6),
        date_in=TODAY - timedelta(days=5),  # already returned
    )
    checkout = make_checkout(
        books=[Book(isbn="111", title="Clean Architecture")],
        borrowers=[borrower],
        loans=[returned_loan],
    )

    result = checkout.execute(isbn="111", borrower_id=1, current_date=TODAY)

    assert result.status is True
