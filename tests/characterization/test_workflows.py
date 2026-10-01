import itertools
from datetime import date, timedelta

import database as db
import pytest
ISBN_A = "0425176428"

_ssn_counter = itertools.count(1)

def make_borrower(name="Test Borrower", address="1 Test St", phone="1234567890"):
    ssn = f"900-00-{next(_ssn_counter):04d}"[:11]
    result = db.create_borrower(name, ssn, address, phone)
    assert result.status, f"setup failed creating borrower: {result.message}"

    borrower = db.get_borrower_by_ssn(ssn.replace("-", ""))
    assert borrower is not None

    return borrower
##Checkout
def test_checkout_workflow_loan_exists_and_book_becomes_unavailable(test_db):
    borrower = make_borrower()
 
    assert db.book_available_with_isbn(ISBN_A) is True
 
    result = db.create_loan(ISBN_A, borrower.id)
    assert result.status is True
 
    loans = db.get_loans_by_borrower_id(borrower.id, returned=False)
    assert len(loans) == 1
    assert loans[0].isbn == ISBN_A
    assert loans[0].date_in is None
 
    assert db.book_available_with_isbn(ISBN_A) is False  

##Check-in (single)
def test_checkout_then_checkin_makes_book_available_again(test_db):
    borrower = make_borrower()
 
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
        