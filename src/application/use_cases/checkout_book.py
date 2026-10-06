"""
Use case: CheckoutBook.

This is business ORCHESTRATION, not SQL. Every rule here, and the exact
message text, is a direct port of database/query/loan.py::create_loan(),
verified against business_rules.md and the characterization tests in
tests/characterization/test_loans.py. Nothing about the behaviour is
changing in this phase -- only where it lives.

This use case depends only on:
  - domain entities (Loan)
  - repository PORTS (interfaces), not any concrete implementation
  - models.result.OperationResult, reused deliberately as the output
    boundary type -- it already existed as a boundary/result shape
    before this refactor (see architecture_baseline.md section 5,
    "existing strengths"), and reusing it here keeps the UI integration
    change (Rose's part) small: the UI already knows how to read an
    OperationResult, so CheckoutBook.execute() being a drop-in
    replacement for db.create_loan() is exactly the point.

It imports NOTHING from `database` or `sqlite3`. That is the entire
architectural point of this file existing.
"""
from datetime import date, timedelta

from application.ports.book_repository import BookRepository
from application.ports.borrower_repository import BorrowerRepository
from application.ports.fine_repository import FineRepository
from application.ports.loan_repository import LoanRepository
from models.result import OperationResult

MAX_ACTIVE_LOANS = 3
LOAN_PERIOD_DAYS = 14


class CheckoutBook:
    def __init__(
        self,
        book_repository: BookRepository,
        borrower_repository: BorrowerRepository,
        loan_repository: LoanRepository,
        fine_repository: FineRepository,
    ):
        self._books = book_repository
        self._borrowers = borrower_repository
        self._loans = loan_repository
        self._fines = fine_repository

    def execute(self, isbn: str, borrower_id: int, current_date: date) -> OperationResult:
        borrower = self._borrowers.get_by_id(borrower_id)
        if borrower is None:
            return OperationResult(status=False, message="Borrower not found")

        active_loans = self._loans.count_active_loans_for_borrower(borrower_id)
        if active_loans >= MAX_ACTIVE_LOANS:
            return OperationResult(status=False, message="Too many checkouts")

        book = self._books.get_by_isbn(isbn)
        if book is None:
            return OperationResult(status=False, message="Book doesn't exist")

        if not self._loans.is_book_available(isbn):
            return OperationResult(status=False, message="Book already checked out.")

        if self._fines.has_unpaid_fines(borrower_id):
            return OperationResult(status=False, message="Borrower has pending fines.")

        due_date = current_date + timedelta(days=LOAN_PERIOD_DAYS)
        loan = self._loans.create_loan(
            isbn=isbn,
            borrower_id=borrower_id,
            title=book.title,
            date_out=current_date,
            due_date=due_date,
        )

        return OperationResult(status=True, message="Checkout successful", data=loan)
