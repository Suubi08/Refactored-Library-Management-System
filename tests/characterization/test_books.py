"""
Characterization tests for search_books(term, filters)  -  src/database/query/book.py

Every test gets `test_db` from conftest.py: a fresh database with the real
seed data (25,000 books, 1,000 borrowers, no loans yet).
"""
import pytest

# ---- Real rows from data/book.csv (they never change, so tests are predictable)
BOOK_ISBN = "0002005018"
BOOK_TITLE = "Clara Callan: A Novel"
BOOK_AUTHOR = "Richard Bruce Wright"

OTHER_ISBN = "0195153448"      # a different book: "Classical Mythology"
BORROWER_ID = 1                # borrower #1 exists in the seed data


# ---- Two tiny helpers
def isbns(results):
    """Turn a list of search results into a set of ISBNs, easy to compare."""
    return {r.isbn for r in results}


def check_out(db, isbn):
    """Make a book 'checked out'. create_loan takes (isbn, borrower_id) in that order."""
    assert db.create_loan(isbn, BORROWER_ID).status is True


# =====================================================================
# PART 1 - matching: ISBN, title, author (case-insensitive), empty term
# =====================================================================
def test_search_by_isbn_finds_the_book(test_db):
    results = test_db.search_books(BOOK_ISBN)

    assert len(results) == 1
    assert results[0].isbn == BOOK_ISBN
    assert results[0].title == BOOK_TITLE


@pytest.mark.parametrize("term", [BOOK_TITLE, BOOK_TITLE.upper(), BOOK_TITLE.lower()])
def test_search_by_title_is_case_insensitive(test_db, term):
    assert BOOK_ISBN in isbns(test_db.search_books(term))


@pytest.mark.parametrize("term", [BOOK_AUTHOR, BOOK_AUTHOR.upper(), BOOK_AUTHOR.lower()])
def test_search_by_author_is_case_insensitive(test_db, term):
    assert BOOK_ISBN in isbns(test_db.search_books(term))


def test_search_with_no_match_returns_empty_list(test_db):
    assert test_db.search_books("zzqqxx_no_such_book") == []


def test_search_with_empty_term_returns_empty_list(test_db):
    assert test_db.search_books("") == []


# =====================================================================
# PART 2 - the availability filter really filters
# =====================================================================
def test_availability_available_hides_a_checked_out_book(test_db):
    check_out(test_db, BOOK_ISBN)

    hits = test_db.search_books(BOOK_ISBN, {"availability": "Available"})

    assert hits == []


def test_availability_available_still_shows_a_free_book(test_db):
    check_out(test_db, BOOK_ISBN)            # a DIFFERENT book is out

    hits = test_db.search_books(OTHER_ISBN, {"availability": "Available"})

    assert isbns(hits) == {OTHER_ISBN}


def test_availability_unavailable_shows_only_checked_out_books(test_db):
    check_out(test_db, BOOK_ISBN)

    # "Clara " matches several books, but only one of them is checked out
    hits = test_db.search_books("Clara ", {"availability": "Unavailable"})

    assert isbns(hits) == {BOOK_ISBN}


def test_availability_all_does_not_filter_anything(test_db):
    check_out(test_db, BOOK_ISBN)

    with_all = test_db.search_books("Clara ", {"availability": "All"})
    no_filter = test_db.search_books("Clara ")

    assert isbns(with_all) == isbns(no_filter)
    assert BOOK_ISBN in isbns(no_filter)     # the checked-out book is still listed


# =====================================================================
# PART 3 - the columns filter restricts which fields are searched
# A columns filter is a list of (column name, switched on?) pairs.
# =====================================================================
def columns(isbn=False, title=False, authors=False):
    return {"columns": [("ISBN", isbn), ("Title", title), ("Authors", authors)]}


def test_columns_isbn_only_finds_by_isbn_but_not_by_title(test_db):
    assert BOOK_ISBN in isbns(test_db.search_books(BOOK_ISBN, columns(isbn=True)))
    assert test_db.search_books(BOOK_TITLE, columns(isbn=True)) == []


def test_columns_title_only_finds_by_title_but_not_by_isbn(test_db):
    assert BOOK_ISBN in isbns(test_db.search_books(BOOK_TITLE, columns(title=True)))
    assert test_db.search_books(BOOK_ISBN, columns(title=True)) == []


def test_columns_authors_only_finds_by_author_but_not_by_title(test_db):
    assert BOOK_ISBN in isbns(test_db.search_books(BOOK_AUTHOR, columns(authors=True)))
    assert test_db.search_books(BOOK_TITLE, columns(authors=True)) == []

# =====================================================================
# get_book_by_isbn(isbn)  -  None for an unknown ISBN, the right book otherwise
# =====================================================================
def test_get_book_by_isbn_returns_the_correct_book(test_db):
    book = test_db.get_book_by_isbn(BOOK_ISBN)
 
    assert book is not None
    assert book.isbn == BOOK_ISBN
    assert book.title == BOOK_TITLE
    assert book.authors == [BOOK_AUTHOR]
 
 
def test_get_book_by_isbn_does_not_return_a_different_book(test_db):
    assert test_db.get_book_by_isbn(OTHER_ISBN).isbn == OTHER_ISBN
    assert test_db.get_book_by_isbn(OTHER_ISBN).title != BOOK_TITLE
 
 
@pytest.mark.parametrize("unknown_isbn", ["NOT-A-REAL-ISBN", "9999999999", ""])
def test_get_book_by_isbn_returns_none_for_unknown_isbn(test_db, unknown_isbn):
    assert test_db.get_book_by_isbn(unknown_isbn) is None
 
 
# KNOWN QUIRK: get_book_by_isbn just reuses search_books (a substring search),
# so a PARTIAL isbn also finds a book. Pinned so Phase 3 changes it on purpose.
def test_quirk_get_book_by_isbn_accepts_a_partial_isbn(test_db):
    book = test_db.get_book_by_isbn(BOOK_ISBN[:-1])      # "000200501"
 
    assert book is not None
    assert book.isbn == BOOK_ISBN

# =====================================================================
# book_available_with_isbn(isbn)  -  True before checkout, False after,
#                                    True again after check-in
# =====================================================================
def check_in(db):
    """Return borrower 1's book. checkin() needs the LOAN id, so look it up first."""
    loan = db.get_loans_by_borrower_id(BORROWER_ID)[0]
    assert db.checkin(loan.id).status is True
 
 
def test_book_is_available_before_checkout(test_db):
    assert test_db.book_available_with_isbn(BOOK_ISBN) is True
 
 
def test_book_is_not_available_after_checkout(test_db):
    check_out(test_db, BOOK_ISBN)
 
    assert test_db.book_available_with_isbn(BOOK_ISBN) is False
 
 
def test_book_is_available_again_after_checkin(test_db):
    check_out(test_db, BOOK_ISBN)
    check_in(test_db)
 
    assert test_db.book_available_with_isbn(BOOK_ISBN) is True
 
 
def test_checking_out_one_book_does_not_affect_another(test_db):
    check_out(test_db, BOOK_ISBN)
 
    assert test_db.book_available_with_isbn(BOOK_ISBN) is False
    assert test_db.book_available_with_isbn(OTHER_ISBN) is True
 
 
# KNOWN QUIRK: the function only counts ACTIVE LOANS. A book that does not
# exist has no loans, so it is reported as available.
def test_quirk_unknown_isbn_is_reported_as_available(test_db):
    assert test_db.book_available_with_isbn("NOT-A-REAL-ISBN") is True
 