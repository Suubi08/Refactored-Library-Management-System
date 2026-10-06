from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

class Author(BaseModel):
    id: int = Field(alias='Author_id')
    name: str = Field(alias='Name')

    model_config = ConfigDict(populate_by_name=True)

class Book(BaseModel):
    isbn: str = Field(alias='Isbn')
    title: str = Field(alias='Title')

class BookAuthor(BaseModel):
    author_id: int = Field(alias='Author_id')
    isbn: str = Field(alias='Isbn')

class Borrower(BaseModel):
    id: int = Field(alias='Card_id')
    ssn: str = Field(alias='Ssn')
    name: str = Field(alias='Bname')
    address: str = Field(alias='Address')
    phone: str = Field(alias='Phone')

class Loan(BaseModel):
    id: int = Field(alias='Loan_id')
    isbn: str = Field(alias='Isbn')
    borrower_id: int = Field(alias='Card_id')
    title: str = Field(alias='Title')
    date_out: date = Field(alias='Date_out')
    due_date: date = Field(alias='Due_date')
    date_in: Optional[date] = Field(alias='Date_in')

    @property
    def is_overdue(self) -> bool:
        """
        NOTE (Phase 4): `import database as db` used to sit at the top of
        this file. That created the models<->database circular import
        documented in architecture_baseline.md (P1/P2) and reproduced in
        tests/characterization/test_known_issues.py. It worked only
        because `database` always happened to be imported before
        `models` elsewhere in the app -- importing `models` first crashed.
        Moving the import here (deferred, used only when this property is
        actually accessed) breaks the module-load-time cycle without
        changing this property's behaviour at all. It does NOT fix the
        underlying architectural problem -- it's the same workaround
        shape as before, just scoped smaller -- but it stops this file
        from silently depending on import order, which is what let a new,
        completely database-free application/ layer (see
        application/use_cases/checkout_book.py) get broken by this file
        merely existing in the same process. Loan.is_overdue is being
        fully replaced by domain.entities.loan.Loan.is_overdue(current_date)
        regardless; this class stays only until the rest of the app is
        migrated off it.
        """
        not_returned = (self.date_in is None)
        import database as db  # deferred: see note below
        past_due = (db.get_current_date() > self.due_date)

        return not_returned and past_due

class Fine(BaseModel):
    loan_id: int = Field(alias='Loan_id')
    amt: int = Field(alias='Fine_amt') # in cents
    paid: bool = Field(alias='Paid')
