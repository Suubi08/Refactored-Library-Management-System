import sys
from datetime import date
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SRC = PROJECT_ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import database as db

@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """
    A fresh, fully-initialized library database for a single test.
    
    - Uses the REAL data/book.csv and data/borrower.csv (same seed data the real app uses), so tests reflect real data shapes.
    - Chdir's into the project root because database/import_data.py reads 'data/book.csv' as a path relative to the current working directory.
    - Sets a fixed 'current date' immediately after init, because a fresh database has NO current_date in metadata, and several functions (e.g. Loan.is_overdue) break if current_date is unset. See tests/characterization/test_known_issues.py.
    """
    monkeypatch.chdir(PROJECT_ROOT)

    db_path = tmp_path / "test_library.db"
    assert db.init(str(db_path)), "db.init() failed to create the test database"

    db.set_current_date(date(2025, 6, 15))

    yield db

    db.delete(str(db_path))

    @pytest.fixture
    def today():
        """The fixed 'current date' test_db sets, so tests don't hardcode it twice"""
        return date(2025, 6, 15)




    # def test_something(test_db, today):
    #     result = test_db.create_borrower("Name", "123456789", "Address", "5551234567")
    #     assert result.status is True