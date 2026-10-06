"""
Domain entity: Loan.

This is intentionally a plain dataclass, not a Pydantic BaseModel. It has
ZERO imports from this project other than the standard library. It does
not know SQLite exists. It does not know the `database` package exists.
It does not know Textual exists. That is the whole point of this file.

Compare to src/models/dtypes.py::Loan, which is still the version the
rest of the app uses today -- that version imports `database` so it can
ask for "today's date" inside is_overdue. This version instead RECEIVES
the current date as an argument, which is what lets it live in an inner,
dependency-free ring.

This file does not replace models/dtypes.py::Loan yet, and nothing else
in the app imports this file yet. Phase 3's job is to get this one entity
right and prove the pattern; wiring the rest of the app to use it is
Phase 4+ work.
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Loan:
    id: int
    isbn: str
    borrower_id: int
    title: str
    date_out: date
    due_date: date
    date_in: Optional[date] = None

    def is_overdue(self, current_date: date) -> bool:
        """
        A loan is overdue when it hasn't been returned AND the given
        current_date is strictly after the due date.

        NOTE: this intentionally preserves the exact behaviour
        business_rules.md documented -- including the quirk that a loan
        due exactly today is NOT overdue (the comparison is '>', not
        '>='). This is a direct port of models/dtypes.py::Loan.is_overdue,
        with db.get_current_date() replaced by a parameter. Preserving
        behaviour exactly is the point of this phase -- if that quirk
        ever needs to change, that's a Phase 4+ decision, made on
        purpose, not a side effect of refactoring.
        """
        not_returned = self.date_in is None
        past_due = current_date > self.due_date

        return not_returned and past_due

    @property
    def is_returned(self) -> bool:
        return self.date_in is not None
