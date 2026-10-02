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


# =====================================================================
#  FINE PERSISTENCE TESTS  (second half of this file)
# =====================================================================
import sqlite3
from contextlib import closing
from datetime import date
 
 
def _isbns(test_db, count):
	"""The first `count` books that are free to borrow."""
	isbns = []
	for book in test_db.search_books("a"):
		if book.isbn not in isbns and test_db.book_available_with_isbn(book.isbn):
			isbns.append(book.isbn)
			if len(isbns) == count:
				break
 
	assert len(isbns) == count
	return isbns
 
 
def _closed_loans(test_db, borrower_id, count):
	"""Borrow `count` books and return them all, so every loan is closed
	(a fine on a closed loan can be paid). Returned sorted by loan id so the
	order is always the same. Max 3: that is the borrower's loan limit."""
	for isbn in _isbns(test_db, count):
		assert test_db.create_loan(isbn, borrower_id).status is True
 
	loans = sorted(test_db.get_loans_by_borrower_id(borrower_id), key=lambda loan: loan.id)
	for loan in loans:
		assert test_db.checkin(loan.id).status is True
 
	return loans
 
 
def _fine_rows(test_db):
	"""The FINES table exactly as stored: {loan_id: (amount_in_cents, paid_flag)}.
	Read straight from the file, so we see what is really saved."""
	with closing(sqlite3.connect(test_db.config.db_name)) as conn:
		rows = conn.execute("SELECT Loan_id, Fine_amt, Paid FROM FINES").fetchall()
 
	return {loan_id: (amount, paid) for loan_id, amount, paid in rows}
 
 
def _overdue_loan(test_db, days_overdue, ssn="999900021"):
	"""A borrower with an ACTIVE loan, with the app's clock moved to
	`days_overdue` days after its due date. Returns (borrower, loan)."""
	borrower = _create_borrower(test_db, ssn)
	isbn = _isbns(test_db, 1)[0]
	assert test_db.create_loan(isbn, borrower.id).status is True
	loan = test_db.get_loans_by_borrower_id(borrower.id)[0]
	test_db.set_current_date(loan.due_date + timedelta(days=days_overdue))
 
	return borrower, loan
 
 
# =====================================================================
# set_fines(fines)  -  a list of (loan_id, amount) pairs
# =====================================================================
def test_set_fines_inserts_new_fines_as_unpaid(test_db):
	borrower = _create_borrower(test_db)
	first, second = _closed_loans(test_db, borrower.id, 2)
 
	assert test_db.set_fines([(first.id, 100), (second.id, 250)]) is True
 
	assert _fine_rows(test_db) == {first.id: (100, 0), second.id: (250, 0)}
 
 
def test_set_fines_replaces_the_existing_fine_for_the_same_loan(test_db):
	borrower = _create_borrower(test_db)
	loan = _closed_loans(test_db, borrower.id, 1)[0]
	test_db.set_fines([(loan.id, 100)])
 
	assert test_db.set_fines([(loan.id, 175)]) is True
 
	assert _fine_rows(test_db) == {loan.id: (175, 0)}          # one row, new amount
 
 
def test_set_fines_replacing_one_fine_leaves_the_others_alone(test_db):
	borrower = _create_borrower(test_db)
	first, second = _closed_loans(test_db, borrower.id, 2)
	test_db.set_fines([(first.id, 100), (second.id, 250)])
 
	test_db.set_fines([(first.id, 400)])
 
	assert _fine_rows(test_db) == {first.id: (400, 0), second.id: (250, 0)}
 
 
def test_set_fines_with_an_empty_list_is_a_safe_no_op(test_db):
	borrower = _create_borrower(test_db)
	loan = _closed_loans(test_db, borrower.id, 1)[0]
 
	assert test_db.set_fines([]) is True                        # nothing to do, no error
	assert _fine_rows(test_db) == {}                            # and nothing was written
 
	test_db.set_fines([(loan.id, 100)])
	assert test_db.set_fines([]) is True
	assert _fine_rows(test_db) == {loan.id: (100, 0)}           # existing fines untouched
 
 
def test_set_fines_that_fails_changes_nothing_at_all(test_db):
	# One bad row (no amount) makes the whole batch fail and roll back,
	# including the good rows that came before it.
	borrower = _create_borrower(test_db)
	first, second = _closed_loans(test_db, borrower.id, 2)
	test_db.set_fines([(first.id, 100)])
 
	result = test_db.set_fines([(first.id, 999), (second.id, None)])
 
	assert result is False
	assert _fine_rows(test_db) == {first.id: (100, 0)}          # 999 was NOT saved
 
 
# =====================================================================
# resolve_fines(loan_ids)  -  marks fines as paid (Paid = 1)
# =====================================================================
def _three_fined_loans(test_db, borrower):
	"""Three closed loans with unpaid fines of 100, 250 and 75 cents."""
	first, second, third = _closed_loans(test_db, borrower.id, 3)
	test_db.set_fines([(first.id, 100), (second.id, 250), (third.id, 75)])
	return first, second, third
 
 
def test_resolve_fines_marks_only_the_given_loans_as_paid(test_db):
	borrower = _create_borrower(test_db)
	first, second, third = _three_fined_loans(test_db, borrower)
 
	assert test_db.resolve_fines([first.id, second.id]) is True
 
	assert _fine_rows(test_db) == {
		first.id: (100, 1),            # paid, amount unchanged
		second.id: (250, 1),           # paid, amount unchanged
		third.id: (75, 0),             # not in the list -> still unpaid
	}
 
 
def test_resolve_fines_does_not_touch_another_borrowers_fines(test_db):
	first_borrower = _create_borrower(test_db, "999900011")
	second_borrower = _create_borrower(test_db, "999900012")
	first_loan = _closed_loans(test_db, first_borrower.id, 1)[0]
	second_loan = _closed_loans(test_db, second_borrower.id, 1)[0]
	test_db.set_fines([(first_loan.id, 100), (second_loan.id, 250)])
 
	test_db.resolve_fines([first_loan.id])
 
	assert _fine_rows(test_db) == {first_loan.id: (100, 1), second_loan.id: (250, 0)}
 
 
def test_paid_fines_leave_the_unpaid_list_but_stay_in_the_full_list(test_db):
	borrower = _create_borrower(test_db)
	first, second, third = _three_fined_loans(test_db, borrower)
	test_db.resolve_fines([first.id, second.id])
 
	unpaid = test_db.get_fines_by_borrower_id(borrower.id)
	everything = test_db.get_fines_by_borrower_id(borrower.id, paid=True)
 
	assert [fine.loan_id for fine in unpaid] == [third.id]
	# paid=True means "paid AND unpaid", not "paid only"
	assert {fine.loan_id for fine in everything} == {first.id, second.id, third.id}
	assert {fine.loan_id: fine.paid for fine in everything} == {
		first.id: True, second.id: True, third.id: False}
 
 
def test_resolve_fines_twice_keeps_the_fine_paid(test_db):
	borrower = _create_borrower(test_db)
	loan = _closed_loans(test_db, borrower.id, 1)[0]
	test_db.set_fines([(loan.id, 100)])
 
	assert test_db.resolve_fines([loan.id]) is True
	assert test_db.resolve_fines([loan.id]) is True
 
	assert _fine_rows(test_db) == {loan.id: (100, 1)}
 
 
def test_resolve_fines_with_an_empty_list_is_a_safe_no_op(test_db):
	borrower = _create_borrower(test_db)
	loan = _closed_loans(test_db, borrower.id, 1)[0]
	test_db.set_fines([(loan.id, 100)])
 
	assert test_db.resolve_fines([]) is True
 
	assert _fine_rows(test_db) == {loan.id: (100, 0)}
 
 
# =====================================================================
# get_total_fines_by_borrower_id(borrower_id, paid=False)
# =====================================================================
def test_total_fines_for_a_single_fine(test_db):
	borrower, _ = _create_closed_loan_with_fine(test_db, amount=250)
 
	assert test_db.get_total_fines_by_borrower_id(borrower.id) == 250
 
 
def test_total_fines_adds_up_every_unpaid_fine(test_db):
	borrower = _create_borrower(test_db)
	_three_fined_loans(test_db, borrower)
 
	assert test_db.get_total_fines_by_borrower_id(borrower.id) == 100 + 250 + 75
 
 
def test_total_fines_is_zero_when_the_borrower_has_no_fines(test_db):
	borrower = _create_borrower(test_db)
 
	assert test_db.get_total_fines_by_borrower_id(borrower.id) == 0
 
 
def test_total_fines_is_zero_for_a_borrower_that_does_not_exist(test_db):
	assert test_db.get_total_fines_by_borrower_id(999999) == 0
 
 
def test_total_fines_counts_only_that_borrowers_fines(test_db):
	first_borrower = _create_borrower(test_db, "999900011")
	second_borrower = _create_borrower(test_db, "999900012")
	first_loan = _closed_loans(test_db, first_borrower.id, 1)[0]
	second_loan = _closed_loans(test_db, second_borrower.id, 1)[0]
	test_db.set_fines([(first_loan.id, 100), (second_loan.id, 250)])
 
	assert test_db.get_total_fines_by_borrower_id(first_borrower.id) == 100
	assert test_db.get_total_fines_by_borrower_id(second_borrower.id) == 250
 
 
def test_total_fines_leaves_out_paid_fines_by_default(test_db):
	borrower = _create_borrower(test_db)
	first, _, _ = _three_fined_loans(test_db, borrower)
 
	test_db.resolve_fines([first.id])                           # the 100-cent fine is paid
 
	assert test_db.get_total_fines_by_borrower_id(borrower.id) == 250 + 75
 
 
def test_total_fines_with_paid_true_counts_paid_and_unpaid_together(test_db):
	borrower = _create_borrower(test_db)
	first, _, _ = _three_fined_loans(test_db, borrower)
	test_db.resolve_fines([first.id])
 
	assert test_db.get_total_fines_by_borrower_id(borrower.id, paid=True) == 100 + 250 + 75
 
 
def test_total_fines_is_zero_once_every_fine_is_paid(test_db):
	borrower = _create_borrower(test_db)
	first, second, third = _three_fined_loans(test_db, borrower)
 
	test_db.resolve_fines([first.id, second.id, third.id])
 
	assert test_db.get_total_fines_by_borrower_id(borrower.id) == 0
 
 
# =====================================================================
# update_fines()  and the stored "last updated" date
# The date lives in the metadata table under 'last_updated_fines' and is read
# with get_fines_last_updated() / written with set_fines_updated().
# =====================================================================
def test_the_fines_last_updated_date_starts_empty(test_db):
	assert test_db.get_fines_last_updated() is None
 
 
def test_update_fines_stores_the_fine_and_todays_date(test_db):
	borrower, loan = _overdue_loan(test_db, days_overdue=4)
	today = test_db.get_current_date()
 
	assert test_db.update_fines() is True
 
	assert _fine_rows(test_db) == {loan.id: (4 * 25, 0)}
	assert test_db.get_fines_last_updated() == today
 
 
def test_update_fines_with_nothing_overdue_still_records_todays_date(test_db):
	today = test_db.get_current_date()
 
	assert test_db.update_fines() is True
 
	assert _fine_rows(test_db) == {}                            # no fines written
	assert test_db.get_fines_last_updated() == today            # but the date IS recorded
 
 
def test_update_fines_replaces_the_stored_amount_instead_of_adding_to_it(test_db):
	_, loan = _overdue_loan(test_db, days_overdue=4)
	test_db.update_fines()
	assert _fine_rows(test_db) == {loan.id: (100, 0)}
 
	test_db.set_current_date(loan.due_date + timedelta(days=9))
	test_db.update_fines()
 
	assert _fine_rows(test_db) == {loan.id: (225, 0)}           # 9 days x 25, not 100 + 225
 
 
def test_update_fines_recalculates_when_the_stored_date_is_earlier_than_today(test_db):
	_, loan = _overdue_loan(test_db, days_overdue=4)
	today = test_db.get_current_date()
	test_db.set_fines_updated(today - timedelta(days=1))        # last run was yesterday
	test_db.set_fines([(loan.id, 9999)])                        # a wrong amount, to see if it gets fixed
 
	assert test_db.update_fines() is True
 
	assert _fine_rows(test_db) == {loan.id: (100, 0)}           # recalculated
	assert test_db.get_fines_last_updated() == today
 
 
def test_update_fines_can_run_again_on_the_same_day(test_db):
	# The guard in update_fines() is  `last_update <= today`  (not  `<`).
	# So when last_update IS today the check still passes and the fines are
	# recalculated again. It is NOT a once-per-day guard. Documented as-is.
	_, loan = _overdue_loan(test_db, days_overdue=4)
	today = test_db.get_current_date()
	assert test_db.update_fines() is True
	assert test_db.get_fines_last_updated() == today            # stored date is now exactly today
 
	test_db.set_fines([(loan.id, 9999)])                        # tamper with the stored amount
	second_run = test_db.update_fines()                         # same day, second call
 
	assert second_run is True
	assert _fine_rows(test_db) == {loan.id: (100, 0)}           # tamper undone: it DID run again
	assert test_db.get_fines_last_updated() == today
 
 
def test_update_fines_only_skips_when_the_stored_date_is_later_than_today(test_db):
	# The one situation the guard blocks: the stored date is in the FUTURE
	# (for example the app's clock was moved backwards).
	_, loan = _overdue_loan(test_db, days_overdue=4)
	future = test_db.get_current_date() + timedelta(days=10)
	test_db.set_fines_updated(future)
	test_db.set_fines([(loan.id, 9999)])
 
	result = test_db.update_fines()
 
	assert result is True                                       # reports success...
	assert _fine_rows(test_db) == {loan.id: (9999, 0)}          # ...but did nothing
	assert test_db.get_fines_last_updated() == future           # stored date unchanged
 
 
def test_update_fines_returns_false_and_writes_nothing_without_a_current_date(test_db):
	_overdue_loan(test_db, days_overdue=4)
	test_db.set_value("current_date", "")                       # an empty value reads back as "no date"
	assert test_db.get_current_date() is None
 
	assert test_db.update_fines() is False
 
	assert _fine_rows(test_db) == {}
	assert test_db.get_fines_last_updated() is None
 
 
# =====================================================================
# KNOWN QUIRKS - odd behaviour pinned on purpose. Phase 3 must keep each
# one or change it knowingly.
# =====================================================================
def test_quirk_set_fines_on_a_paid_fine_turns_it_back_into_unpaid(test_db):
	# set_fines uses INSERT OR REPLACE and always writes Paid = 0, so replacing
	# a fine wipes its "paid" status.
	borrower = _create_borrower(test_db)
	loan = _closed_loans(test_db, borrower.id, 1)[0]
	test_db.set_fines([(loan.id, 100)])
	test_db.resolve_fines([loan.id])
	assert _fine_rows(test_db) == {loan.id: (100, 1)}
 
	test_db.set_fines([(loan.id, 100)])
 
	assert _fine_rows(test_db) == {loan.id: (100, 0)}
 
 
def test_quirk_set_fines_accepts_a_loan_id_that_does_not_exist(test_db):
	# The FINES table declares a foreign key to BOOK_LOANS, but SQLite does not
	# enforce it here. The orphan row is saved yet never shows up in any read,
	# because the read queries JOIN to the loan.
	borrower = _create_borrower(test_db)
 
	assert test_db.set_fines([(999999, 500)]) is True
 
	assert _fine_rows(test_db) == {999999: (500, 0)}
	assert test_db.get_fines_by_borrower_id(borrower.id, paid=True) == []
	assert test_db.get_all_fines(paid=True) == []
 
 
def test_quirk_resolve_fines_reports_success_for_loan_ids_that_do_not_exist(test_db):
	borrower = _create_borrower(test_db)
	loan = _closed_loans(test_db, borrower.id, 1)[0]
	test_db.set_fines([(loan.id, 100)])
 
	assert test_db.resolve_fines([999999]) is True              # nothing matched, still "success"
 
	assert _fine_rows(test_db) == {loan.id: (100, 0)}
 
 
def test_quirk_rerunning_update_fines_unpays_a_paid_fine_on_a_still_overdue_loan(test_db):
	# pay_fines() refuses to pay a fine on an active loan, so this only happens
	# if resolve_fines() is called directly. update_fines() then rewrites the
	# fine through set_fines(), which resets Paid to 0.
	_, loan = _overdue_loan(test_db, days_overdue=4)
	test_db.update_fines()
	test_db.resolve_fines([loan.id])
	assert _fine_rows(test_db) == {loan.id: (100, 1)}
 
	test_db.update_fines()
 
	assert _fine_rows(test_db) == {loan.id: (100, 0)}
 
