from datetime import timedelta


def _create_borrower(test_db, ssn="999900001"):
	result = test_db.create_borrower("Test Borrower", ssn, "1 Test St", "1234567890")
	assert result.status is True
	borrower = test_db.get_borrower_by_ssn(ssn)
	assert borrower is not None
	return borrower


def _available_isbns(test_db, count):
	isbns = []
	for book in test_db.search_books("a"):
		if book.isbn not in isbns and test_db.book_available_with_isbn(book.isbn):
			isbns.append(book.isbn)
			if len(isbns) == count:
				break

	assert len(isbns) == count
	return isbns


def test_create_loan_rejects_unknown_borrower(test_db):
	isbn = _available_isbns(test_db, 1)[0]

	result = test_db.create_loan(isbn, 999999)

	assert result.status is False
	assert result.message == "Borrower not found"


def test_create_loan_rejects_fourth_active_loan(test_db):
	borrower = _create_borrower(test_db)
	isbns = _available_isbns(test_db, 4)

	for isbn in isbns[:3]:
		result = test_db.create_loan(isbn, borrower.id)
		assert result.status is True

	result = test_db.create_loan(isbns[3], borrower.id)

	assert result.status is False
	assert result.message == "Too many checkouts"


def test_create_loan_rejects_unknown_book(test_db):
	borrower = _create_borrower(test_db)

	result = test_db.create_loan("not-a-real-isbn", borrower.id)

	assert result.status is False
	assert result.message == "Book doesn't exist"


def test_create_loan_rejects_book_with_an_active_loan(test_db):
	first_borrower = _create_borrower(test_db, "999900001")
	second_borrower = _create_borrower(test_db, "999900002")
	isbn = _available_isbns(test_db, 1)[0]

	first_result = test_db.create_loan(isbn, first_borrower.id)
	assert first_result.status is True

	result = test_db.create_loan(isbn, second_borrower.id)

	assert result.status is False
	assert result.message == "Book already checked out."


def test_create_loan_rejects_borrower_with_unpaid_fines(test_db):
	borrower = _create_borrower(test_db)
	first_isbn, second_isbn = _available_isbns(test_db, 2)

	loan_result = test_db.create_loan(first_isbn, borrower.id)
	assert loan_result.status is True
	loan = test_db.get_loans_by_borrower_id(borrower.id)[0]
	assert test_db.set_fines([(loan.id, 25)]) is True

	result = test_db.create_loan(second_isbn, borrower.id)

	assert result.status is False
	assert result.message == "Borrower has pending fines."


def test_create_loan_sets_due_date_fourteen_days_after_checkout(test_db):
	borrower = _create_borrower(test_db)
	isbn = _available_isbns(test_db, 1)[0]

	result = test_db.create_loan(isbn, borrower.id)

	assert result.status is True
	assert result.message == "Book successfully checked out!"
	loan = test_db.get_loans_by_borrower_id(borrower.id)[0]
	assert loan.due_date == loan.date_out + timedelta(days=14)
