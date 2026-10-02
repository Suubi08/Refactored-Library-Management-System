from datetime import timedelta


def _create_borrower(test_db, ssn="999900001"):
    result = test_db.create_borrower(
        "Test Borrower",
        ssn,
        "1 Test St",
        "1234567890"
    )

    assert result.status is True

    borrower = test_db.get_borrower_by_ssn(ssn)

    assert borrower is not None

    return borrower


def _available_isbns(test_db, count):
    isbns = []

    for book in test_db.search_books("a"):
        if (
            book.isbn not in isbns
            and test_db.book_available_with_isbn(book.isbn)
        ):
            isbns.append(book.isbn)

            if len(isbns) == count:
                break

    assert len(isbns) == count

    return isbns


# =========================================================
# BUSINESS RULE CHARACTERIZATION TESTS
# =========================================================


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

    result = test_db.create_loan(
        isbns[3],
        borrower.id
    )

    assert result.status is False
    assert result.message == "Too many checkouts"


def test_create_loan_rejects_unknown_book(test_db):
    borrower = _create_borrower(test_db)

    result = test_db.create_loan(
        "not-a-real-isbn",
        borrower.id
    )

    assert result.status is False
    assert result.message == "Book doesn't exist"


def test_create_loan_rejects_book_with_an_active_loan(test_db):
    first_borrower = _create_borrower(
        test_db,
        "999900001"
    )

    second_borrower = _create_borrower(
        test_db,
        "999900002"
    )

    isbn = _available_isbns(test_db, 1)[0]

    first_result = test_db.create_loan(
        isbn,
        first_borrower.id
    )

    assert first_result.status is True

    result = test_db.create_loan(
        isbn,
        second_borrower.id
    )

    assert result.status is False
    assert result.message == "Book already checked out."


def test_create_loan_rejects_borrower_with_unpaid_fines(test_db):
    borrower = _create_borrower(test_db)

    first_isbn, second_isbn = _available_isbns(
        test_db,
        2
    )

    loan_result = test_db.create_loan(
        first_isbn,
        borrower.id
    )

    assert loan_result.status is True

    loan = test_db.get_loans_by_borrower_id(
        borrower.id
    )[0]

    assert test_db.set_fines(
        [(loan.id, 25)]
    ) is True

    result = test_db.create_loan(
        second_isbn,
        borrower.id
    )

    assert result.status is False
    assert result.message == "Borrower has pending fines."


def test_create_loan_sets_due_date_fourteen_days_after_checkout(test_db):
    borrower = _create_borrower(test_db)

    isbn = _available_isbns(
        test_db,
        1
    )[0]

    result = test_db.create_loan(
        isbn,
        borrower.id
    )

    assert result.status is True
    assert result.message == "Book successfully checked out!"

    loan = test_db.get_loans_by_borrower_id(
        borrower.id
    )[0]

    assert loan.due_date == (
        loan.date_out + timedelta(days=14)
    )


# =========================================================
# CRUD / QUERY CHARACTERIZATION TESTS
# =========================================================


from datetime import date

JUNE_15 = date(2025, 6, 15)        # the fixed "today" that test_db sets
JUNE_16 = date(2025, 6, 16)
JUNE_17 = date(2025, 6, 17)
JUNE_18 = date(2025, 6, 18)
JUNE_20 = date(2025, 6, 20)
JUNE_25 = date(2025, 6, 25)


def _check_out(test_db, isbn, borrower_id, on=None):
    """Create a loan, optionally on a chosen day, and return the new Loan.
    (create_loan always uses 'the current date', so to get loans on different
    days we move the app's clock first with set_current_date.)"""
    if on is not None:
        test_db.set_current_date(on)

    result = test_db.create_loan(isbn, borrower_id)
    assert result.status is True, f"setup failed: {result.message}"

    return next(loan for loan in test_db.get_loans_by_borrower_id(borrower_id)
                if loan.isbn == isbn)


def _four_active_loans(test_db):
    """Four active loans for four REAL seed borrowers, one per day:
        borrower  1 'Mark Morgan'    out June 15
        borrower  2 'Eric Warren'    out June 16
        borrower 10 'Daniel Fisher'  out June 17
        borrower 11 'Stephen Fields' out June 18
    Returns {borrower_id: Loan}. Ids 1, 10 and 11 all contain the digit 1,
    which one of the quirk tests below needs."""
    isbns = _available_isbns(test_db, 4)
    plan = [(1, JUNE_15), (2, JUNE_16), (10, JUNE_17), (11, JUNE_18)]

    return {borrower_id: _check_out(test_db, isbn, borrower_id, on=day)
            for isbn, (borrower_id, day) in zip(isbns, plan)}


def _borrower_ids(loans):
    return [loan.borrower_id for loan in loans]


def _loan_ids(loans):
    return [loan.id for loan in loans]


# =====================================================================
# get_loans_by_borrower_id(borrower_id, returned=False)
# =====================================================================
def test_get_loans_by_borrower_id_returns_correct_rows(test_db):
    first = _create_borrower(test_db, "999900001")
    second = _create_borrower(test_db, "999900002")
    no_loans = _create_borrower(test_db, "999900003")
    isbn_old, isbn_new, isbn_other = _available_isbns(test_db, 3)
    old = _check_out(test_db, isbn_old, first.id, on=JUNE_15)
    new = _check_out(test_db, isbn_new, first.id, on=JUNE_17)
    _check_out(test_db, isbn_other, second.id, on=JUNE_17)

    loans = test_db.get_loans_by_borrower_id(first.id)

    # only the first borrower's loans, newest checkout first
    assert _loan_ids(loans) == [new.id, old.id]
    # every field of a row
    assert loans[1].isbn == isbn_old
    assert loans[1].borrower_id == first.id
    assert loans[1].title == test_db.get_book_by_isbn(isbn_old).title    # title comes from BOOK
    assert loans[1].date_out == JUNE_15
    assert loans[1].due_date == date(2025, 6, 29)
    assert loans[1].date_in is None                                      # still out
    # a borrower with no loans, and one who does not exist, both give an empty list
    assert test_db.get_loans_by_borrower_id(no_loans.id) == []
    assert test_db.get_loans_by_borrower_id(999999) == []


def test_get_loans_by_borrower_id_hides_returned_loans_unless_asked(test_db):
    borrower = _create_borrower(test_db)
    isbn_returned, isbn_still_out = _available_isbns(test_db, 2)
    returned_loan = _check_out(test_db, isbn_returned, borrower.id)
    still_out_loan = _check_out(test_db, isbn_still_out, borrower.id)
    test_db.checkin(returned_loan.id)

    default = test_db.get_loans_by_borrower_id(borrower.id)
    explicit_false = test_db.get_loans_by_borrower_id(borrower.id, returned=False)
    with_returned = test_db.get_loans_by_borrower_id(borrower.id, returned=True)

    assert _loan_ids(default) == [still_out_loan.id]
    assert _loan_ids(explicit_false) == [still_out_loan.id]
    # returned=True means "active AND returned", not "returned only"
    assert set(_loan_ids(with_returned)) == {returned_loan.id, still_out_loan.id}


# =====================================================================
# get_loans_by_isbn(isbn, returned=False)
# =====================================================================
def test_get_loans_by_isbn_returns_correct_rows(test_db):
    borrower = _create_borrower(test_db)
    isbn_a, isbn_b, never_loaned = _available_isbns(test_db, 3)
    loan_a = _check_out(test_db, isbn_a, borrower.id)
    _check_out(test_db, isbn_b, borrower.id)

    loans = test_db.get_loans_by_isbn(isbn_a)

    assert _loan_ids(loans) == [loan_a.id]                      # only that book's loan
    assert loans[0].borrower_id == borrower.id
    assert loans[0].title == test_db.get_book_by_isbn(isbn_a).title
    assert test_db.get_loans_by_isbn(never_loaned) == []        # book never loaned
    assert test_db.get_loans_by_isbn("not-a-real-isbn") == []   # book that does not exist


def test_get_loans_by_isbn_hides_returned_loans_unless_asked(test_db):
    # One book, two borrowers, one after the other: a book's loan HISTORY.
    first = _create_borrower(test_db, "999900001")
    second = _create_borrower(test_db, "999900002")
    isbn = _available_isbns(test_db, 1)[0]
    old_loan = _check_out(test_db, isbn, first.id, on=JUNE_15)
    test_db.set_current_date(JUNE_16)
    test_db.checkin(old_loan.id)
    new_loan = _check_out(test_db, isbn, second.id, on=JUNE_17)

    default = test_db.get_loans_by_isbn(isbn)
    with_returned = test_db.get_loans_by_isbn(isbn, returned=True)

    assert _loan_ids(default) == [new_loan.id]
    assert _loan_ids(with_returned) == [new_loan.id, old_loan.id]    # newest first
    assert with_returned[0].date_in is None
    assert with_returned[1].date_in == JUNE_16


# =====================================================================
# search_loans(isbn, borrower_id, name, returned=False)
# =====================================================================
def test_search_loans_lists_all_active_loans_newest_first(test_db):
    assert test_db.search_loans() == []                         # nothing borrowed yet
    loans = _four_active_loans(test_db)

    results = test_db.search_loans()

    assert _borrower_ids(results) == [11, 10, 2, 1]             # newest checkout first
    assert _loan_ids(results) == [loans[b].id for b in (11, 10, 2, 1)]
    row = next(r for r in results if r.borrower_id == 2)        # check one row's fields
    assert row.title == test_db.get_book_by_isbn(loans[2].isbn).title
    assert row.date_out == JUNE_16
    assert row.due_date == date(2025, 6, 30)
    assert row.date_in is None


def test_search_loans_filters_by_isbn_name_and_borrower_id(test_db):
    loans = _four_active_loans(test_db)
    isbn = loans[2].isbn

    # ISBN: whole, UPPER case, or just the start of it
    assert _borrower_ids(test_db.search_loans(isbn=isbn)) == [2]
    assert _borrower_ids(test_db.search_loans(isbn=isbn.upper())) == [2]
    assert _borrower_ids(test_db.search_loans(isbn=isbn[:6])) == [2]
    # borrower name: any case, part of the name is enough
    assert _borrower_ids(test_db.search_loans(name="Mark Morgan")) == [1]
    assert _borrower_ids(test_db.search_loans(name="mark")) == [1]
    assert _borrower_ids(test_db.search_loans(name="ERIC WARREN")) == [2]
    # borrower id: as text or as a number
    assert _borrower_ids(test_db.search_loans(borrower_id="2")) == [2]
    assert _borrower_ids(test_db.search_loans(borrower_id=2)) == [2]
    # nothing matches
    assert test_db.search_loans(name="no such person") == []


def test_search_loans_returned_false_hides_checked_in_loans_and_true_shows_them(test_db):
    loans = _four_active_loans(test_db)
    test_db.set_current_date(JUNE_20)
    test_db.checkin(loans[2].id)                                # Eric Warren returns his book

    # default: hidden, even when a filter matches him
    assert 2 not in _borrower_ids(test_db.search_loans())
    assert test_db.search_loans(name="Eric") == []

    # returned=True: the returned loan AND the three still-active ones
    everything = test_db.search_loans(returned=True)
    filtered = test_db.search_loans(name="Eric", returned=True)
    assert sorted(_borrower_ids(everything)) == [1, 2, 10, 11]
    assert _borrower_ids(filtered) == [2]
    assert filtered[0].date_in == JUNE_20


# =====================================================================
# checkin(loan_id)  /  resolve_loan(loan_id)
# =====================================================================
def test_checkin_and_resolve_loan_set_the_return_date_to_the_current_date(test_db):
    # checkin() is a one-line wrapper around resolve_loan(), where the real
    # UPDATE lives, so close one loan with each and check both.
    borrower = _create_borrower(test_db)
    isbn_a, isbn_b = _available_isbns(test_db, 2)
    via_checkin = _check_out(test_db, isbn_a, borrower.id, on=JUNE_15)
    via_resolve = _check_out(test_db, isbn_b, borrower.id, on=JUNE_15)
    test_db.set_current_date(JUNE_20)                           # five days later

    checkin_result = test_db.checkin(via_checkin.id)
    resolve_result = test_db.resolve_loan(via_resolve.id)

    for result in (checkin_result, resolve_result):
        assert result.status is True
        assert result.message == "Book check in successfully."
    returned = {loan.id: loan for loan in
                test_db.get_loans_by_borrower_id(borrower.id, returned=True)}
    for loan_id in (via_checkin.id, via_resolve.id):
        assert returned[loan_id].date_in == JUNE_20             # return date = the current date
        assert returned[loan_id].date_out == JUNE_15            # other dates untouched
        assert returned[loan_id].due_date == date(2025, 6, 29)


def test_checked_in_loan_drops_out_of_active_queries_and_only_that_loan_closes(test_db):
    borrower = _create_borrower(test_db)
    isbn_a, isbn_b = _available_isbns(test_db, 2)
    loan_a = _check_out(test_db, isbn_a, borrower.id)
    loan_b = _check_out(test_db, isbn_b, borrower.id)

    test_db.checkin(loan_a.id)

    # gone from every active-loans query; the other loan is still there, still out
    still_active = test_db.get_loans_by_borrower_id(borrower.id)
    assert _loan_ids(still_active) == [loan_b.id]
    assert still_active[0].date_in is None
    assert test_db.get_loans_by_isbn(isbn_a) == []
    assert _loan_ids(test_db.search_loans()) == [loan_b.id]
    # ...but the history is kept when you ask for returned loans
    assert loan_a.id in _loan_ids(test_db.get_loans_by_borrower_id(borrower.id, returned=True))
    assert _loan_ids(test_db.get_loans_by_isbn(isbn_a, returned=True)) == [loan_a.id]
    assert loan_a.id in _loan_ids(test_db.search_loans(returned=True))


# =====================================================================
# checkin_many(loans)
# =====================================================================
def _make_checkin_fail_for(monkeypatch, test_db, *failing_loan_ids):
    """Make test_db.checkin() report a failure for the chosen loan ids and work
    normally for every other loan.

    Why fake it? The real checkin() only fails if the database itself breaks,
    which we can't cause safely. monkeypatch swaps the function for this
    stand-in for ONE test and puts the original back afterwards."""
    from models.result import OperationResult
    real_checkin = test_db.checkin

    def flaky_checkin(loan_id):
        if loan_id in failing_loan_ids:
            return OperationResult(status=False, message="simulated failure")
        return real_checkin(loan_id)

    monkeypatch.setattr(test_db, "checkin", flaky_checkin)


def test_checkin_many_returns_true_when_every_checkin_succeeds(test_db):
    loans = _four_active_loans(test_db)
    test_db.set_current_date(JUNE_20)

    result = test_db.checkin_many(list(loans.values()))

    assert result.status is True
    assert result.message == "Books checked in successfully."
    assert test_db.search_loans() == []                          # nothing left out
    returned = test_db.search_loans(returned=True)
    assert len(returned) == 4
    assert {loan.date_in for loan in returned} == {JUNE_20}
    # an empty list also counts as success
    assert test_db.checkin_many([]).status is True


def test_checkin_many_reports_false_and_names_the_failed_isbn(test_db, monkeypatch):
    loans = _four_active_loans(test_db)
    failing = loans[2]
    _make_checkin_fail_for(monkeypatch, test_db, failing.id)

    result = test_db.checkin_many(list(loans.values()))

    assert result.status is False
    assert failing.isbn in result.message
    for other in (loans[1], loans[10], loans[11]):
        assert other.isbn not in result.message                 # only the failed one is named
    # no all-or-nothing rollback: the three that worked ARE checked in
    assert _borrower_ids(test_db.search_loans()) == [2]


def test_checkin_many_names_every_failed_isbn_in_order(test_db, monkeypatch):
    loans = _four_active_loans(test_db)
    first_failure, second_failure = loans[1], loans[10]
    _make_checkin_fail_for(monkeypatch, test_db, first_failure.id, second_failure.id)

    result = test_db.checkin_many([loans[1], loans[2], loans[10], loans[11]])

    assert result.status is False
    assert f"{first_failure.isbn}, {second_failure.isbn}" in result.message
    assert loans[2].isbn not in result.message
    assert loans[11].isbn not in result.message


def test_quirk_get_loans_by_isbn_needs_the_whole_isbn_unlike_search_loans(test_db):
    borrower = _create_borrower(test_db)
    isbn = _available_isbns(test_db, 1)[0]
    _check_out(test_db, isbn, borrower.id)

    assert test_db.get_loans_by_isbn(isbn[:6]) == []            # part of an ISBN finds nothing here
    assert len(test_db.search_loans(isbn=isbn[:6])) == 1        # but search_loans accepts part of one


def test_quirk_search_loans_matching_is_loose(test_db):
    loans = _four_active_loans(test_db)

    # 1) borrower_id matches PART of the number: "1" is found inside 1, 10 and 11
    assert sorted(_borrower_ids(test_db.search_loans(borrower_id="1"))) == [1, 10, 11]

    # 2) two filters are joined with OR, not AND: a loan matching EITHER is returned.
    #    The isbn belongs to borrower 1's loan, the id "2" to borrower 2's loan.
    #    (AND would give []). The OR is written in two places in the source,
    #    one for returned=False and one for returned=True, so check both.
    assert sorted(_borrower_ids(
        test_db.search_loans(isbn=loans[1].isbn, borrower_id="2"))) == [1, 2]
    assert sorted(_borrower_ids(
        test_db.search_loans(isbn=loans[1].isbn, borrower_id="2", returned=True))) == [1, 2]


def test_quirk_checkin_reports_success_even_when_it_changed_nothing_useful(test_db):
    # (a) A loan id that does not exist: the UPDATE matches zero rows, which is
    #     not a database error, so the function says "success".
    assert test_db.checkin(999999).status is True

    # (b) Checking in an already-returned loan succeeds and OVERWRITES the date.
    borrower = _create_borrower(test_db)
    isbn = _available_isbns(test_db, 1)[0]
    loan = _check_out(test_db, isbn, borrower.id)
    test_db.set_current_date(JUNE_20)
    test_db.checkin(loan.id)
    test_db.set_current_date(JUNE_25)

    second = test_db.checkin(loan.id)                           # already returned!

    assert second.status is True                                # no complaint...
    returned = test_db.get_loans_by_borrower_id(borrower.id, returned=True)[0]
    assert returned.date_in == JUNE_25                          # ...and the date moved


def test_quirk_checkin_many_failure_message_ends_with_a_stray_bracket(test_db, monkeypatch):
    # The source builds  f"Failed to check in: {', '.join(isbns)}.]"  - the
    # trailing "]" has no matching "[". Pinned exactly so a Phase 3 clean-up
    # of the message is a deliberate change.
    loans = _four_active_loans(test_db)
    _make_checkin_fail_for(monkeypatch, test_db, loans[1].id, loans[2].id)

    result = test_db.checkin_many([loans[1], loans[2]])

    assert result.message == f"Failed to check in: {loans[1].isbn}, {loans[2].isbn}.]"