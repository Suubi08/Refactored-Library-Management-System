"""
Characterization tests for behaviour that looks like a BUG in the current
system. We are not  fixing these -- we are proving, on record, that this is how the
system behaves today, so that the refactor phase either preserves it 
deliberately or fixes it as an explicit, documented change
"""
import pytest
import database as db

def test_is_overdue_raises_when_current_date_was_never_set(tmp_path, monkeypatch):
    from pathlib import Path
    monkeypatch.chdir(Path(__file__).parent.parent.parent)

    db_path = tmp_path / "no_date_set.db"
    assert db.init(str(db_path))

    db.create_borrower("Bug Finder", "999999999", "1 St", "1112223333")
    borrower = db.get_borrower_by_ssn("999999999")
    books = db.search_books("a")
    isbn = books[0].isbn

    # create_loan() itself tolerates a missing current_date (falls back to
    # date.today() initially) -- so the loan is created successfully.

    result = db.create_loan(borrower.id, isbn)
    assert result.status is True

    loan = db.get_loans_by_borrower_id(borrower.id)[0]

    with pytest.raises(TypeError):
        _ = loan.is_overdue()  # this is the bug: it raises TypeError because current_date is None