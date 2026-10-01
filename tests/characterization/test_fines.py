from datetime import timedelta

import pytest


def _create_borrower(test_db, ssn="999900011"):
	result = test_db.create_borrower("Test Borrower", ssn, "1 Test St", "1234567890")
	assert result.status is True
	borrower = test_db.get_borrower_by_ssn(ssn)
	assert borrower is not None
	return borrower


def _create_closed_loan_with_fine(test_db, ssn="999900011", amount=250):
	borrower = _create_borrower(test_db, ssn)
	book = next(
		book for book in test_db.search_books("a")
		if test_db.book_available_with_isbn(book.isbn)
	)

	loan_result = test_db.create_loan(book.isbn, borrower.id)
	assert loan_result.status is True
	loan = test_db.get_loans_by_borrower_id(borrower.id)[0]
	assert test_db.checkin(loan.id).status is True
	assert test_db.set_fines([(loan.id, amount)]) is True
	return borrower, loan


def test_loan_due_today_is_not_overdue(test_db):
	borrower = _create_borrower(test_db)
	book = next(
		book for book in test_db.search_books("a")
		if test_db.book_available_with_isbn(book.isbn)
	)

	result = test_db.create_loan(book.isbn, borrower.id)
	assert result.status is True
	loan = test_db.get_loans_by_borrower_id(borrower.id)[0]
	test_db.set_current_date(loan.due_date)

	assert loan.is_overdue is False


def test_update_fines_charges_twenty_five_cents_per_overdue_day(test_db):
	borrower = _create_borrower(test_db)
	book = next(
		book for book in test_db.search_books("a")
		if test_db.book_available_with_isbn(book.isbn)
	)

	result = test_db.create_loan(book.isbn, borrower.id)
	assert result.status is True
	loan = test_db.get_loans_by_borrower_id(borrower.id)[0]
	days_overdue = 4
	test_db.set_current_date(loan.due_date + timedelta(days=days_overdue))

	assert test_db.update_fines() is True
	fines = test_db.get_fines_by_borrower_id(borrower.id)
	assert len(fines) == 1
	assert fines[0].amt == days_overdue * 25


def test_pay_fines_rejects_underpayment(test_db):
	borrower, _ = _create_closed_loan_with_fine(test_db)

	result = test_db.pay_fines(borrower.id, 249)

	assert result.status is False
	assert result.message == "Borrower didn't pay enough fine."


@pytest.mark.parametrize("amount", [250, 300])
def test_pay_fines_accepts_exact_or_overpayment(test_db, amount):
	borrower, _ = _create_closed_loan_with_fine(test_db)

	result = test_db.pay_fines(borrower.id, amount)

	assert result.status is True
	assert result.message == "Fines paid successfully!"


def test_pay_fines_rejects_borrower_without_fines(test_db):
	borrower = _create_borrower(test_db)

	result = test_db.pay_fines(borrower.id, 0)

	assert result.status is False
	assert result.message == "No fines attached to borrower."


def test_pay_fines_rejects_fine_for_open_loan_and_names_isbn(test_db):
	borrower = _create_borrower(test_db)
	book = next(
		book for book in test_db.search_books("a")
		if test_db.book_available_with_isbn(book.isbn)
	)

	loan_result = test_db.create_loan(book.isbn, borrower.id)
	assert loan_result.status is True
	loan = test_db.get_loans_by_borrower_id(borrower.id)[0]
	assert test_db.set_fines([(loan.id, 250)]) is True

	result = test_db.pay_fines(borrower.id, 250)

	assert result.status is False
	assert result.message == (
		"Cannot make payment on books that are actively checked out: "
		f"{book.isbn}"
	)
