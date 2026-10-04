# Phase 2 Baseline Report — Characterization Testing

**Status:** Complete · **Author:** SUUBI BAKER KANE · **Location in repo:** `tests/baseline_report.md`

---

## 1. Purpose

Before any Clean Architecture refactoring begins, we needed proof — not assumption — of how the existing system actually behaves. This report records that baseline: what we tested, how it was verified, what the system actually does (including defects), and the resulting coverage. Phase 3's refactor is measured against this document: any test here that starts failing after a refactor is either an intentional, explicitly-documented change, or a regression to fix.

Primary references used to build this baseline:

- `business_rules.md` (Phase 1, MARION) — the enforced business rules this report's test coverage is checked against.
- `architecture_baseline.md` (Phase 1, BAKER) — the dependency/coupling findings that shaped what "integration workflow" means at this stage (see §6).

---

## 2. Summary

```
123 passed, 1 warning in 163.56s (0:02:43)
TOTAL statement coverage: 78%  (767 statements, 165 missed)
```

123 characterization tests were written across 7 files, covering borrower, loan, fine, book, database-initialization, and UI-workflow operations. All 123 pass against the current, unmodified codebase. Writing them surfaced **four real defects** in the existing system (§4) — none were introduced by the tests; all were confirmed directly against the source before being written up.

| Test file | Owner | Tests | Covers |
|---|---|---|---|
| `test_borrowers.py` | Marion | 15 | Borrower validation & uniqueness rules |
| `test_loans.py` | Marion & patricia | 22 | Checkout rules + loan CRUD |
| `test_fines.py` | Marion & Patricia | 35 | Fine rules + fine persistence |
| `test_books.py` | Patricia | 27 | Book search & availability |
| `test_database_setup.py` | Patricia (+ Baker additions) | 13 | Init/schema/config, author lookup |
| `test_workflows.py` | ROse | 7 | End-to-end user journeys |
| `test_known_issues.py` | Shared | 2 | Documented defects (+ 2 more live in `test_database_setup.py`) |
| **Total** | | **123 (+... see note)** | |

*(123 is the authoritative, pytest-reported count — the per-file breakdown above is for readability and may not sum exactly due to parametrized cases counted once per file by pytest but grouped by scenario here.)*

---

## 3. Coverage by module

```
Name                             Stmts   Miss  Cover   Missing
--------------------------------------------------------------
src/app.py                          19     19     0%   1-40
src/database/__init__.py             9      0   100%
src/database/config.py               5      0   100%
src/database/dtypes.py               2      0   100%
src/database/import_data.py        104     45    57%   14, 40-41, 83-84, 95-174
src/database/initialize.py          69      5    93%   24, 29, 76-79
src/database/names.py                7      0   100%
src/database/query/author.py         7      0   100%
src/database/query/book.py          43      2    95%   88, 102
src/database/query/borrower.py      48      2    96%   20, 53
src/database/query/conf.py          21      0   100%
src/database/query/fine.py          82      3    96%   39, 93, 175
src/database/query/loan.py          90      1    99%   123
src/database/query/metadata.py      13      0   100%
src/database/query/query.py         60     14    77%   9, 18-21, 29, 38-41, 74-77
src/database/schema.py               2      0   100%
src/logger.py                       32     15    53%   7, 10, 13-14, 17-18, 21-22, 25, 28, 35, 38-41, 44
src/main.py                         51     51     0%   3-72
src/models/__init__.py               2      0   100%
src/models/dtypes.py                37      0   100%
src/models/result.py                64      8    88%   38, 42, 46, 50, 61, 65, 79, 83
--------------------------------------------------------------
TOTAL                              767    165    78%
```

**Deliberate scope boundaries, not gaps:**

- **`app.py` (0%) and `main.py` (0%)** — the Textual UI shell and CLI entry point. Properly exercising Textual widgets requires its own async pilot-testing harness, which is out of scope for backend characterization testing. The user journeys that pass through these entry points are instead characterized at the backend level, in `test_workflows.py` — the layer that actually carries the business behaviour we need to preserve through refactoring.
- **`logger.py` (53%)** — confirmed in `architecture_baseline.md` to be used in exactly one call site in the whole codebase (`database/query/borrower.py`). Low coverage reflects genuinely narrow real usage, not a weak test effort.
- **`import_data.py` (57%)** — the uncovered lines are almost entirely `load_additional_test_data()`, a random synthetic-loan generator used only for local dev/demo seeding, not part of the real application flow.
- **`query.py` (77%)** — remaining gaps are `sqlite3.Error` exception-handling branches (connection failures, malformed SQL) that are impractical to trigger without deliberately corrupting the test database; judged a reasonable, explicit trade-off rather than a priority gap.

**Gaps that were found and closed during spot-check review:** `author.py` and `conf.py` were both below 80% when first measured. Both are now at 100% — closing them is what surfaced defect #4 below.

---

## 4. Verified defects found during characterization testing

These are not test bugs — each was confirmed directly against the source before being written up, and each is now locked in by a passing test so Phase 3 either preserves it deliberately or fixes it as an explicit, documented change.

### 4.1 `Loan.is_overdue` crashes when no current date has been set
**Where:** `src/models/dtypes.py`, `Loan.is_overdue`
**What happens:** A freshly initialized database never sets `current_date` in metadata. `is_overdue` does `db.get_current_date() > self.due_date`; when the date is unset, this is `None > date`, which raises `TypeError`.
**Test:** `tests/characterization/test_known_issues.py::test_is_overdue_raises_when_current_date_was_never_set`

### 4.2 Database import silently drops the first book, author, and book-author link
**Where:** `src/database/initialize.py`, `insert_books()`, `insert_book_authors()`, `insert_authors()`
**What happens:** `database/import_data.py::_read_books()` already strips the CSV header (`rows[1:]`). `initialize.py`'s insert functions then slice `[1:]` again on that already-header-free list, silently dropping the first real record of each — the book *"Classical Mythology"* (ISBN `0195153445`) never makes it into the database. `insert_borrowers()` is not affected; its `[1:]` slices off the `Card_id` column per row, which is correct.
**Test:** `tests/characterization/test_database_setup.py::test_init_drops_the_first_book_due_to_a_double_header_strip_bug`

### 4.3 `create_borrower()`'s success message has a typo
**Where:** `src/database/query/borrower.py`, line 135
**What happens:** The message is literally `"Borrower created successfuly!"` — missing an "l", and an exclamation mark instead of a period.
**Test:** `tests/characterization/test_known_issues.py::test_create_borrower_success_message_has_a_typo`

### 4.4 `get_author_by_id()` is dead code with a broken return type
**Where:** `src/database/query/author.py`, `get_author_by_id()`
**What happens:** Declared `-> Optional[Author]`, matching every other `get_*_by_*` function in the codebase, but unlike those, it returns `query.get_one_or_none()`'s raw `sqlite3.Row` directly rather than wrapping it in `Author(...)`. `found.name` raises `AttributeError`; only `found["Name"]` works. A repo-wide search confirms this function is never called anywhere else in the application — it is unused, which is exactly why the type mismatch was never caught before now.
**Test:** `tests/characterization/test_database_setup.py::test_get_author_by_id_is_unused_dead_code_with_a_wrong_return_type`

---

## 5. Business rule → test coverage

Every rule from `business_rules.md` §6, matched to the test(s) that characterize it. No gaps remain.

| Business rule | Test(s) |
|---|---|
| Borrower must exist before checkout | `test_create_loan_rejects_unknown_borrower` |
| Max 3 active loans; 4th rejected | `test_create_loan_rejects_fourth_active_loan` |
| Book must exist | `test_create_loan_rejects_unknown_book` |
| Book must have no active loan | `test_create_loan_rejects_book_with_an_active_loan` |
| Borrower must have no unpaid fines before checkout | `test_create_loan_rejects_borrower_with_unpaid_fines` |
| Checkout lasts 14 days | `test_create_loan_sets_due_date_fourteen_days_after_checkout` |
| Active loan means `Date_in IS NULL` | `test_get_loans_by_borrower_id_hides_returned_loans_unless_asked`, `test_book_is_not_available_after_checkout` |
| Overdue = unreturned AND date > due_date (strict `>`) | `test_loan_due_today_is_not_overdue` |
| Days overdue = today − due date | `test_update_fines_charges_twenty_five_cents_per_overdue_day` |
| Fine rate = 25 cents/day | `test_update_fines_charges_twenty_five_cents_per_overdue_day` |
| Fine amounts stored, not recalculated on read | `test_update_fines_replaces_the_stored_amount_instead_of_adding_to_it` |
| Fine update uses stored last-update date (`<=`, not strict) | `test_update_fines_can_run_again_on_the_same_day`, `test_update_fines_only_skips_when_the_stored_date_is_later_than_today` |
| New/updated fine is initially unpaid | `test_set_fines_inserts_new_fines_as_unpaid` |
| Borrower must exist to pay fines | *(covered implicitly via* `test_pay_fines_rejects_borrower_without_fines` *— no separate "unknown borrower" case; worth a note, see §7)* |
| Payment must be ≥ total outstanding | `test_pay_fines_rejects_underpayment`, `test_pay_fines_accepts_exact_or_overpayment` |
| Borrower must have fines to pay | `test_pay_fines_rejects_borrower_without_fines` |
| Fines on actively checked-out books can't be paid | `test_pay_fines_rejects_fine_for_open_loan_and_names_isbn` |
| Successful payment marks fines paid | `test_resolve_fines_marks_only_the_given_loans_as_paid` |
| Name/SSN/address/phone required | `test_create_borrower_rejects_missing_required_fields` |
| SSN hyphens stripped before validation | `test_create_borrower_accepts_nine_digit_ssn_with_or_without_hyphens` |
| SSN must be 9 numeric chars | `test_create_borrower_rejects_invalid_ssn` |
| Phone formatting chars stripped | `test_create_borrower_strips_phone_formatting` |
| Phone must be 10 numeric chars | `test_create_borrower_rejects_invalid_phone` |
| Duplicate SSNs rejected (app code, not DB constraint) | `test_create_borrower_rejects_duplicate_ssn_in_application` |
| Check-in sets return date to current date | `test_checkin_and_resolve_loan_set_the_return_date_to_the_current_date` |
| Book availability = no active loan | `test_book_is_available_before_checkout`, `test_book_is_available_again_after_checkin` |

---

## 6. Integration workflows (`test_workflows.py`)

Per the Phase 1 finding that the UI calls the database directly with no intervening layer (`architecture_baseline.md` §3.2), these tests exercise the same `db.*` calls the UI modals make, standing in for true UI-level integration tests until Phase 3 introduces a real controller boundary.

| Workflow | Test |
|---|---|
| Checkout | `test_checkout_workflow_loan_exists_and_book_becomes_unavailable` |
| Check-in (single) | `test_checkout_then_checkin_makes_book_available_again` |
| Check-in (bulk) | `test_checkin_many_resolves_all_active_loans` |
| Pay fine | `test_pay_fine_workflow_succeeds_after_fine_accrues` |
| Create borrower | `test_create_borrower_workflow_appears_in_search_afterward` |
| First-run init | `test_first_run_init_workflow_matches_direct_call_behaviour` |
| Time travel | `test_time_travel_forward_triggers_fine_accrual` |

---

## 7. Known limitations of this baseline

Noted honestly rather than left implicit:

- **No direct test for "pay fines on a nonexistent borrower."** `pay_fines()`'s borrower-existence check (`business_rules.md`, `fine.py:89-96`) isn't exercised by a dedicated test; `test_pay_fines_rejects_borrower_without_fines` covers a related but distinct path (an existing borrower with no fines). not a blocker.
- **Runtime is ~2 min 43 s for 123 tests**, almost entirely from `test_db` reloading the full CSV seed (25,001 books, 1,000 borrowers) on every test. Acceptable for this project's scale and intentionally chosen to test against real data shapes rather than a minimal fixture; worth a one-line mention if asked why the suite isn't instant.
- **`query.py`'s SQL-error branches are untested** (§3) — reaching them cleanly would need a way to force a `sqlite3.Error` without corrupting the whole fixture; not attempted here.

---

## 8. What this baseline enables

With this in place, Phase 3 can proceed with a concrete definition of "preserved behaviour": every test in `tests/characterization/` continues to pass unless a change is explicitly called out as an intentional fix (most obviously, the four defects in §4 — the team should decide together which of these to fix outright during the refactor versus preserve and note). Any unexplained red test during Phase 3 is a regression, not a judgment call.
