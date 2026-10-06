"""
SQLite adapter for the LoanRepository port (application/ports/loan_repository.py).

Two of the three methods just wrap existing database functions. create_loan
is the one with real work: it runs the same INSERT that
database/query/loan.py::create_loan() uses, but with the dates it is GIVEN
(CheckoutBook already did the 14-day maths), and returns a plain domain Loan
instead of an OperationResult.

`import database` comes first on purpose. Importing `models` before
`database` triggers the circular-import crash (see Phase 1 findings).
"""
import os
import sqlite3
from datetime import date

import database as db
from database import config
from database.names import BOOK_LOANS_TABLE_NAME
from domain.entities.loan import Loan


class LoanCreationError(RuntimeError):
    """The loan could not be saved. (The port returns a Loan, so it has no way
    to say 'failed' -- raising is how this adapter reports it.)"""


class SqliteLoanRepository:
    def count_active_loans_for_borrower(self, borrower_id: int) -> int:
        return len(db.get_loans_by_borrower_id(borrower_id, returned=False))

    def is_book_available(self, isbn: str) -> bool:
        return db.book_available_with_isbn(isbn)

    def create_loan(self, isbn: str, borrower_id: int, title: str, date_out: date, due_date: date) -> Loan:
        # Don't let sqlite3 quietly create an empty database file by accident.
        if not os.path.isfile(config.db_name):
            raise LoanCreationError(f"database file not found: {config.db_name}")

        sql = f"""
        INSERT INTO {BOOK_LOANS_TABLE_NAME} (
            Isbn,
            Card_id,
            Date_out,
            Due_date,
            Date_in
        ) VALUES (?, ?, ?, ?, NULL)
        """

        conn = sqlite3.connect(config.db_name)

        try:
            cursor = conn.execute(sql, [isbn, borrower_id, date_out.isoformat(), due_date.isoformat()])
            conn.commit()
            loan_id = cursor.lastrowid          # the id SQLite just gave the new loan
        except sqlite3.Error as error:
            conn.rollback()
            raise LoanCreationError(f"could not create loan for ISBN {isbn}: {error}") from error
        finally:
            conn.close()

        return Loan(
            id=loan_id,
            isbn=isbn,
            borrower_id=borrower_id,
            title=title,
            date_out=date_out,
            due_date=due_date,
            date_in=None,
        )