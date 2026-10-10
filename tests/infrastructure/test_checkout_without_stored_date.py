"""
Regression tests: checkout on a database with NO stored current date.

Why this file exists: the shared `test_db` fixture always sets a current date,
so no other test exercises a fresh database. The old `create_loan` fell back to
`date.today()`; the use-case wiring in the UI dropped that fallback and the
checkout button crashed with TypeError (None + timedelta).
"""
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pytest

import database as db  # import first: keeps module import order safe
from composition_root import build_checkout_book

PROJECT_ROOT = Path(__file__).parent.parent.parent


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.chdir(PROJECT_ROOT)
    path = tmp_path / "no_stored_date.db"
    assert db.init(str(path))
    yield path
    db.delete(str(path))


def _any_isbn(path) -> str:
    conn = sqlite3.connect(str(path))
    isbn = conn.execute("SELECT Isbn FROM BOOK LIMIT 1").fetchone()[0]
    conn.close()
    return isbn


def test_fresh_database_has_no_stored_date(fresh_db):
    assert db.get_current_date() is None


def test_checkout_succeeds_using_the_same_fallback_as_the_ui_handler(fresh_db):
    isbn = _any_isbn(fresh_db)
    today = date.today()

    # same expression the checkout button uses
    result = build_checkout_book().execute(isbn, 1, db.get_current_date() or today)

    assert result.status is True
    loans = db.get_loans_by_borrower_id(1)
    assert len(loans) == 1
    assert loans[0].due_date == today + timedelta(days=14)


def test_use_case_itself_still_requires_a_date(fresh_db):
    """The use case is deliberately strict; the caller supplies the date."""
    isbn = _any_isbn(fresh_db)
    with pytest.raises(TypeError):
        build_checkout_book().execute(isbn, 1, None)