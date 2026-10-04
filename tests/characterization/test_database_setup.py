"""
Characterization tests for database/initialize.py and the metadata/config
functions (is_initialized, get_current_date, set_current_date).

IMPORTANT -- why this file does NOT use the shared `test_db` fixture:
`test_db` (in tests/conftest.py) already calls db.init() for you, because
every OTHER test file is testing things that happen AFTER initialization.
But init() itself is what we're testing here, so we can't rely on a
fixture that's already called it.

That means every test below builds its OWN throwaway database path using
pytest's `tmp_path` fixture, and NEVER touches the real library.db. If you
ever see a bare string like "library.db" passed to db.init()/db.exists()/
db.delete() in this file, that's a mistake -- stop and fix it. The whole
point of `tmp_path` is that pytest creates a brand-new, isolated temp
directory per test and cleans it up afterward, so there is no way for
these tests to reach your real project database.
"""
import csv
import sqlite3
from pathlib import Path

import pytest

import database as db

PROJECT_ROOT = Path(__file__).parent.parent.parent


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """
    A path to a database file that does not exist yet, inside pytest's
    private temp directory. We also chdir into the project root, because
    database/import_data.py reads 'data/book.csv' / 'data/borrower.csv'
    as paths relative to the current working directory -- it needs to
    find the real data/ folder, but the DATABASE FILE itself still only
    ever lives under tmp_path.
    """
    monkeypatch.chdir(PROJECT_ROOT)
    return tmp_path / "characterization_test.db"


def test_init_creates_a_database_file(db_path):
    assert not db_path.exists()
    assert db.init(str(db_path)) is True
    assert db_path.exists()


def test_init_creates_all_seven_tables(db_path):
    db.init(str(db_path))

    conn = sqlite3.connect(str(db_path))
    tables = {
        row[0] for row in
        conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    conn.close()

    # NOTE: the metadata table name constant is lowercase ('metadata'),
    # unlike every other table -- see database/names.py. Easy to trip over.
    expected = {"BOOK", "BOOK_AUTHORS", "AUTHORS", "BORROWER", "BOOK_LOANS", "FINES", "metadata"}
    assert expected.issubset(tables)


def test_init_loads_borrowers_with_correct_row_count(db_path):
    db.init(str(db_path))

    with open(PROJECT_ROOT / "data" / "borrower.csv", encoding="utf-8") as f:
        expected_borrower_rows = sum(1 for _ in csv.reader(f)) - 1  # minus header

    conn = sqlite3.connect(str(db_path))
    borrower_count = conn.execute("SELECT COUNT(*) FROM BORROWER").fetchone()[0]
    conn.close()

    assert borrower_count == expected_borrower_rows


def test_init_drops_the_first_book_due_to_a_double_header_strip_bug(db_path):
    """
    REAL BUG, verified -- not a mistake in this test.

    database/import_data.py's _read_books() already strips the CSV header
    (it iterates rows[1:]). But database/initialize.py's insert_books()
    then does ANOTHER [1:] slice on that already-header-free list:

        book_data = [tuple(row) for row in books[1:]]

    That silently drops the first real book record -- ISBN '0195153445',
    "Classical Mythology" -- every time the app is initialized. The same
    double-slice bug also exists in insert_book_authors() and
    insert_authors(), dropping the first author and its book linkage.
    insert_borrowers() is NOT affected: its row[1:] slices off the
    Card_id column from each row (correct), not the first row.

    This test locks in the CURRENT (buggy) behaviour -- one book short of
    the CSV's real count -- so Phase 3 either fixes this as an explicit,
    documented change, or we knowingly decide to preserve it.
    """
    db.init(str(db_path))

    with open(PROJECT_ROOT / "data" / "book.csv", encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    csv_data_row_count = len(rows) - 1  # minus header
    first_book_isbn = rows[1][0]  # first real ISBN in the CSV

    conn = sqlite3.connect(str(db_path))
    book_count = conn.execute("SELECT COUNT(*) FROM BOOK").fetchone()[0]
    first_book_in_db = conn.execute(
        "SELECT COUNT(*) FROM BOOK WHERE Isbn = ?", (first_book_isbn,)
    ).fetchone()[0]
    conn.close()

    assert book_count == csv_data_row_count - 1, (
        "If this test starts failing because book_count now equals "
        "csv_data_row_count (not -1), the bug has been fixed -- update "
        "this test to assert equality instead, and note the fix."
    )
    assert first_book_in_db == 0, "the first book in the CSV should be missing from BOOK"


def test_exists_is_false_before_init_and_true_after(db_path):
    assert db.exists(str(db_path)) is False
    db.init(str(db_path))
    assert db.exists(str(db_path)) is True


def test_delete_removes_the_database_file(db_path):
    db.init(str(db_path))
    assert db_path.exists()

    assert db.delete(str(db_path)) is True
    assert not db_path.exists()


def test_delete_returns_false_when_file_does_not_exist(db_path):
    assert not db_path.exists()
    assert db.delete(str(db_path)) is False


def test_is_initialized_false_before_set_true_after(db_path):
    db.init(str(db_path))
    # db.init() already calls set_initialized() internally -- confirm that:
    assert db.is_initialized() is True


def test_get_current_date_is_none_immediately_after_fresh_init(db_path):
    """
    This is the root cause behind the Loan.is_overdue crash documented in
    test_known_issues.py: init() never sets a current_date, so a fresh
    database has none until something explicitly calls set_current_date().
    """
    db.init(str(db_path))
    assert db.get_current_date() is None


def test_set_current_date_then_get_current_date_roundtrips(db_path):
    from datetime import date
    db.init(str(db_path))

    assert db.set_current_date(date(2025, 6, 15)) is True
    assert db.get_current_date() == date(2025, 6, 15)

def test_get_author_by_id_is_unused_dead_code_with_a_wrong_return_type(db_path):
    """
    REAL BUG, verified --not a test mistake.

    get_author_by_id() is annotated `-> Optional[Author]`, matching the
    pattern every get_*_by_* function in this codebase follows
    (parse the DB row into the matching Pydantic model). But unlike those,
    it returns query.get_one_or_none()'s result directly, which is a raw
    sqlite3.Row -- never wrapped in Author(...). So found.name raises
    AttributeError; only dict-style access (found["name"]) works.

    This had 0% test coverage before this test, and a repo-wide search confirms get_author_by_id()
    is not called anywhere in the codebase -- it's dead code today, which
    is why this type mismatch was never caught. In the next phase,
    we either delete it, or fix it to return the Optional[Author]
    contract it already declares.
    """
    db.init(str(db_path))
    conn = sqlite3.connect(str(db_path))
    row = conn.execute("SELECT Author_id, Name FROM AUTHORS LIMIT 1").fetchone()
    conn.close()
    author_id, name = row

    found = db.get_author_by_id(author_id)

    assert found is not None
    assert not hasattr(found, "name"), (
        "if this now fails, get_author_by_id() has been fixed to return"
        "a real Author -- update this test to assert found.name == name"
    )
    assert found["name"] == name

def test_get_author_by_id_returns_none_for_unknown_id(db_path):
    db.init(str(db_path))
    assert db.get_author_by_id(999999) is None
 
 
def test_reset_time_sets_current_date_to_today_and_runs_fine_update(db_path):
    from datetime import date
    db.init(str(db_path))
    db.set_current_date(date(2020, 1, 1))  # force a stale date first
 
    assert db.reset_time() is True
    assert db.get_current_date() == date.today()
    assert db.get_fines_last_updated() == date.today()
 