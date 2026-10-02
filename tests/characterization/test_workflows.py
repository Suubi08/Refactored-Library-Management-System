import itertools
from datetime import date, timedelta
import pytest
import database as db

ISBN_A = "0425176428"

_ssn_counter = itertools.count(1)

@pytest.fixture
def borrower(test_db):
    """A borrower created inside the test database. Depends on test_db,
    so pytest guarantees the temp database is already set up before
    this runs."""
    ssn = f"900-00-{next(_ssn_counter):04d}"[:11]
    result = db.create_borrower("Test Borrower", ssn, "1 Test St", "1234567890")
    assert result.status, f"setup failed creating borrower: {result.message}"

    return db.get_borrower_by_ssn(ssn.replace("-", ""))

##Checkout
def test_checkout_workflow_loan_exists_and_book_becomes_unavailable(borrower):
    assert db.book_available_with_isbn(ISBN_A) is True

    result = db.create_loan(ISBN_A, borrower.id)
    assert result.status is True

    loans = db.get_loans_by_borrower_id(borrower.id, returned=False)
    assert len(loans) == 1
    assert loans[0].isbn == ISBN_A
    assert loans[0].date_in is None

    assert db.book_available_with_isbn(ISBN_A) is False 

##Check-in (single)
def test_checkout_then_checkin_makes_book_available_again(borrower):
    checkout_result = db.create_loan(ISBN_A, borrower.id)
    assert checkout_result.status is True

    loan = db.get_loans_by_borrower_id(borrower.id, returned=False)[0]

    checkin_result = db.checkin(loan.id)
    assert checkin_result.status is True

    assert db.book_available_with_isbn(ISBN_A) is True

    [resolved_loan] = [
        l for l in db.get_loans_by_borrower_id(borrower.id, returned=True)
        if l.id == loan.id
    ]
    assert resolved_loan.date_in is not None

##Check-in(bulk) 
other_isbn = "0060973129"  
 
def test_checkin_many_resolves_all_active_loans(borrower):
    r1 = db.create_loan(ISBN_A, borrower.id)
    r2 = db.create_loan(other_isbn, borrower.id)
    assert r1.status and r2.status

    active_loans = db.get_loans_by_borrower_id(borrower.id, returned=False)
    assert len(active_loans) == 2

    result = db.checkin_many(active_loans)
    assert result.status is True

    remaining_active = db.get_loans_by_borrower_id(borrower.id, returned=False)
    assert remaining_active == []


##Pay fine: BorrowerDetailModal -> db.pay_fines
def test_pay_fine_workflow_succeeds_after_fine_accrues(borrower):
    checkout_result = db.create_loan(ISBN_A, borrower.id)
    assert checkout_result.status is True

    loan = db.get_loans_by_borrower_id(borrower.id, returned=False)[0]

    # Move time forward past the due date so a fine accrues.
    future = loan.due_date + timedelta(days=4)
    db.set_current_date(future)
    db.update_fines()

    total_owed = db.get_total_fines_by_borrower_id(borrower.id)
    assert total_owed > 0



       ## Can't pay while the loan is still open.
    blocked = db.pay_fines(borrower.id, total_owed)
    assert blocked.status is False
    assert ISBN_A in blocked.message

    ##Can't pay while the loan is still open.
    blocked = db.pay_fines(borrower.id, total_owed)
    assert blocked.status is False
    assert ISBN_A in blocked.message

    ##Check the book back in, then payment should succeed.
    db.checkin(loan.id)

    paid = db.pay_fines(borrower.id, total_owed)
    assert paid.status is True

    assert db.get_total_fines_by_borrower_id(borrower.id) == 0

##Create borrower: CreateBorrowerModal -> db.create_borrower()

def test_create_borrower_workflow_appears_in_search_afterward(test_db):
    unique_name = "AAAA Workflow Borrower"

    result = db.create_borrower(unique_name, "900-00-9999", "1 Test St", "1234567890")
    assert result.status is True

    found = db.search_borrowers(unique_name)
    assert len(found) == 1
    assert found[0].name == unique_name 


## Firstrun init: InitPromptModal/SettingsModal →db.init()

def test_first_run_init_workflow_matches_direct_call_behaviour(tmp_path, monkeypatch):
    from pathlib import Path

    # db.init() reads data/book.csv and data/borrower.csv as paths
    # relative to the current working directory, so chdir into the
    # project root first, same reason test_db does this in conftest.py.
    project_root = Path(__file__).parent.parent.parent
    monkeypatch.chdir(project_root)

    db_path = str(tmp_path / "fresh_library.db")

    assert db.exists(db_path) is False

    success = db.init(db_path)
    assert success is True

    assert db.exists(db_path) is True
    assert db.is_initialized() is True
    # Known issue: current_date is unset right after a fresh init().
    assert db.get_current_date() is None


##Timetravel: TimeTravelModal →db.set_current_date() +db.update_fines()

def test_time_travel_forward_triggers_fine_accrual(borrower):
    checkout_result = db.create_loan(ISBN_A, borrower.id)
    assert checkout_result.status is True

    loan = db.get_loans_by_borrower_id(borrower.id, returned=False)[0]

    assert db.get_total_fines_by_borrower_id(borrower.id) == 0

    days_overdue = 6
    db.set_current_date(loan.due_date + timedelta(days=days_overdue))
    db.update_fines()

    expected_fine_cents = days_overdue * 25
    assert db.get_total_fines_by_borrower_id(borrower.id) == expected_fine_cents

