"""
SQLite adapter for the BorrowerRepository port
(application/ports/borrower_repository.py).

Wraps database.get_borrower_by_id() and reshapes the old Pydantic Borrower
into the plain domain Borrower.
"""
from typing import Optional

import database as db
from domain.entities.borrower import Borrower


class SqliteBorrowerRepository:
    def get_by_id(self, borrower_id: int) -> Optional[Borrower]:
        result = db.get_borrower_by_id(borrower_id)     # a models.Borrower, or None

        if result is None:
            return None

        return Borrower(
            id=result.id,
            ssn=result.ssn,
            name=result.name,
            address=result.address,
            phone=result.phone,
        )