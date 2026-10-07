"""
SQLite adapter for the FineRepository port (application/ports/fine_repository.py).

database.get_fines_by_borrower_id() returns UNPAID fines by default, so an
empty list means "no unpaid fines".
"""
import database as db


class SqliteFineRepository:
    def has_unpaid_fines(self, borrower_id: int) -> bool:
        return bool(db.get_fines_by_borrower_id(borrower_id))