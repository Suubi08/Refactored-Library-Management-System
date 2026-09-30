# Business Rules — Library Management System

## Purpose and scope

This document records the business rules that are actually expressed/enforced by the supplied source code. It does **not** redesign the system or move any code.

Primary files inspected:

- `src/database/query/loan.py`
- `src/database/query/fine.py`
- `src/database/query/borrower.py`
- `src/database/query/book.py`
- `src/models/dtypes.py`

`src/database/schema.py` was checked only to answer the specific question of whether duplicate SSNs are prevented by a database constraint. It is not treated as a source of additional business rules below.

---

## 1. Checkout rules — full checkout flow

### Checkout entry point

`checkout(isbn, borrower_id)` in `src/database/query/loan.py:122-123` does not perform the checks itself. It delegates directly to:

```text
create_loan(isbn, borrower_id)
```

The complete enforced sequence is therefore in `create_loan()`.

### Step 1 — Borrower must exist

**Rule:** A book cannot be checked out unless the specified borrower exists.

**Enforced at:** `src/database/query/loan.py:125-133`, function `create_loan()`.

The function calls `db.get_borrower_by_id(borrower_id)` at line 126 and rejects the checkout when the result is false at lines 128-133 with `Borrower not found`.

**Classification:** Application / domain.

---

### Step 2 — Borrower may have at most 2 active loans before a new checkout

**Rule:** A borrower cannot create a new checkout when they already have 3 or more active (unreturned) loans. Therefore the maximum number of active loans after a successful checkout is **3**.

**Enforced at:** `src/database/query/loan.py:134-140`, function `create_loan()`.

`get_loans_by_borrower_id(borrower_id, returned=False)` is called at line 134. Because `returned=False` causes the query at `loan.py:83-84` to add `Date_in IS NULL`, it returns active/unreturned loans. The condition at lines 136-140 rejects the transaction when `len(checkouts) >= 3`.

**Important clue:** The code's rejection threshold is **3 existing active loans**, not `> 3`. Thus a borrower may have 3 active loans, but cannot check out a fourth.

**Classification:** Application / domain.

---

### Step 3 — Book must exist

**Rule:** A checkout cannot be created for a book that cannot be found by ISBN.

**Enforced at:** `src/database/query/loan.py:142-148`, function `create_loan()`.

The function calls `db.get_book_by_isbn(isbn)` at line 142 and rejects the transaction at lines 144-148 if no book is returned.

`get_book_by_isbn()` in `src/database/query/book.py:79-85` obtains its result through `search_books(isbn)`, returning the first matching result.

**Classification:** Application / infrastructure boundary.

---

### Step 4 — Book must be available

**Rule:** A book is considered unavailable when it has an active loan (a loan whose `Date_in` is `NULL`). A checkout cannot be created while the book has such a loan.

**Enforced at:**

- `src/database/query/loan.py:150-156`, function `create_loan()` — rejects unavailable books.
- `src/database/query/book.py:90-104`, function `book_available_with_isbn()` — determines availability.

`book_available_with_isbn()` counts rows in `BOOK_LOANS` for the ISBN where `Date_in IS NULL` (`book.py:91-97`). It returns `True` only when the query result has zero active checkouts (`book.py:101-104`).

**Classification:** Application / domain rule, with the current enforcement implemented through database querying (infrastructure).

---

### Step 5 — Borrower must not have outstanding fines

**Rule:** A borrower with one or more unpaid fines cannot check out another book.

**Enforced at:** `src/database/query/loan.py:158-164`, function `create_loan()`.

`db.get_fines_by_borrower_id(borrower_id)` is called without `paid=True`. In `src/database/query/fine.py:41-66`, the default `paid=False` adds `AND f.Paid = 0` to the query at line 55. If any unpaid fine is returned, `create_loan()` rejects the checkout at lines 160-164.

**Classification:** Application / domain.

---

### Step 6 — Successful checkout creates a 14-day loan

**Rule:** When all checkout checks pass, the loan's `Date_out` is the system's current date and its `Due_date` is exactly 14 days after that date.

**Enforced at:** `src/database/query/loan.py:166-185`, function `create_loan()`.

The current date is obtained at line 176. `date_out` is set to that date at line 178, while `due_date` is calculated at line 179 as:

```text
 today + timedelta(days=14)
```

The values are then inserted at lines 166-184 with `Date_in = NULL` (line 173), making the new loan active/unreturned.

**Classification:** Domain / application.

---

## 2. Fine rules

### Rule — A loan is overdue only when it is unreturned and past its due date

**Rule:** A loan is overdue if and only if:

1. `date_in` is `None` (the book has not been returned), and
2. the current system date is later than `due_date`.

**Enforced at:** `src/models/dtypes.py:38-43`, property `Loan.is_overdue`.

**Important consequence:** A loan whose due date is exactly today is **not** overdue according to this code, because the comparison is `>` rather than `>=`.

**Classification:** Domain.

---

### Rule — Days overdue are calculated from today minus the due date

**Rule:** The number of days overdue is calculated as the difference between the current date and the loan's due date.

**Enforced at:** `src/database/query/fine.py:161-165`, function `update_fines()`.

At line 163:

```text
 days_overdue = (today - loan.due_date).days
```

**Classification:** Domain / application.

---

### Rule — Fine rate is 25 cents per day overdue

**Rule:** The fine amount is calculated at **25 cents per day overdue**.

**Enforced at:** `src/database/query/fine.py:163-167`, function `update_fines()`.

The exact calculation at line 165 is:

```text
 fine_amt = days_overdue * 25
```

**Type:** Variable total fine, based on number of days overdue; the per-day rate itself does not change in this code.

**Classification:** Domain.

---

### Rule — Fine amounts are stored in the database rather than calculated every time fines are read

**Rule:** Fine amounts are persisted in the `FINES` table and read from `Fine_amt`; the amount is not recomputed by `get_all_fines()` or `get_fines_by_borrower_id()`.

**Enforced/implemented at:**

- `src/database/query/fine.py:16-39`, `get_all_fines()` — reads `f.Fine_amt`.
- `src/database/query/fine.py:41-66`, `get_fines_by_borrower_id()` — reads `f.Fine_amt`.
- `src/database/query/fine.py:141-175`, `update_fines()` — calculates and updates the stored amounts.
- `src/database/query/fine.py:177-195`, `set_fines()` — writes the amounts to the `FINES` table.

The actual write occurs through `INSERT OR REPLACE` at lines 179-187, with `Fine_amt` supplied from the calculated values.

**Conclusion:** Fine calculation is **stored/recomputed by `update_fines()`**, not calculated on every read.

**Classification:** Application / infrastructure for the current enforcement; the fine calculation itself is a domain rule.

---

### Rule — Fine updates use the current date and a stored last-update date

**Rule:** `update_fines()` checks the stored `last_updated_fines` date before deciding whether to perform the fine update.

**Enforced at:** `src/database/query/fine.py:78-87` and `141-175`.

`set_fines_updated()` stores the update date under `last_updated_fines` (lines 78-79). `get_fines_last_updated()` reads it (lines 81-87). `update_fines()` compares it with today's date at lines 142-150.

**Implementation detail:** The condition is `last_update <= today` (line 148). Therefore, if `last_update` is today's date, `should_update` is still true and the function can recompute/update fines again on another call the same day. The code does not enforce a strict "once per day" rule; it permits updates whenever the stored date is missing or is less than/equal to today.

**Classification:** Application / infrastructure.

---

### Rule — Fine records are created/updated as unpaid

**Rule:** When `set_fines()` writes a fine record, its `Paid` value is set to `0`.

**Enforced at:** `src/database/query/fine.py:177-195`, function `set_fines()`.

The SQL at lines 179-187 explicitly inserts `Paid = 0`.

**Classification:** Domain / application.

---

### Rule — A borrower must exist before fines can be paid

**Rule:** A fine payment cannot be processed for a borrower who does not exist.

**Enforced at:** `src/database/query/fine.py:89-96`, function `pay_fines()`.

The borrower is looked up at line 90 and the operation is rejected at lines 92-96 if no borrower is found.

**Classification:** Application / domain.

---

### Rule — A borrower must pay at least the total outstanding fine amount

**Rule:** A fine payment is rejected when the supplied amount is less than the borrower's total outstanding fines.

**Enforced at:** `src/database/query/fine.py:98-104`, function `pay_fines()`.

`total_fines` is obtained at line 98. The condition at line 100 rejects the payment when `amt < total_fines`.

**Important observation:** The code does not reject an amount greater than the total; it only requires the payment to be **at least** the total.

**Classification:** Domain / application.

---

### Rule — There must be fines attached to the borrower before payment is processed

**Rule:** Payment is rejected when the borrower has no fine records.

**Enforced at:** `src/database/query/fine.py:106-112`, function `pay_fines()`.

**Classification:** Application / domain.

---

### Rule — Fines on actively checked-out books cannot be paid

**Rule:** A fine cannot be paid while the associated book is still actively checked out (`date_in == None`).

**Enforced at:** `src/database/query/fine.py:114-121`, function `pay_fines()`.

The code builds `isbn_of_fines_with_active_checkouts` from fines whose `date_in == None` at line 114. If the list is non-empty, payment is rejected at lines 117-121.

**Classification:** Domain / application.

---

### Rule — Successful fine payment marks the borrower's fine records as paid

**Rule:** After payment validation succeeds, all collected fine loan IDs are passed to `resolve_fines()`, which sets `Paid = 1`.

**Enforced at:**

- `src/database/query/fine.py:123-128`, `pay_fines()`.
- `src/database/query/fine.py:130-139`, `resolve_fines()`.

The SQL at lines 131-135 updates `Paid` to `1` for each supplied `Loan_id`.

**Classification:** Application / infrastructure.

---

## 3. Borrower rules

### Rule — Name, SSN, address, and phone are required

**Rule:** A borrower cannot be created unless all four fields are non-empty:

- Name
- SSN
- Address
- Phone

**Enforced at:** `src/database/query/borrower.py:85-96`, function `create_borrower()`.

The condition at line 86 checks `if not (name and ssn and address and phone)`. Missing fields are collected and reported at lines 87-92.

**Classification:** Domain / application.

**Database constraint note:** The schema also declares these columns `NOT NULL`, but the code-level business validation happens first in `create_borrower()`.

---

### Rule — SSN is normalized by removing hyphens before validation/storage

**Rule:** Hyphens are removed from the supplied SSN before its format is validated and before it is stored.

**Enforced at:** `src/database/query/borrower.py:98`, function `create_borrower()`.

```text
ssn = ssn.replace('-', '')
```

**Classification:** Application / domain.

---

### Rule — SSN must contain exactly 9 numeric characters after hyphen removal

**Rule:** After hyphens are removed, the SSN must consist only of numeric characters and must have exactly 9 characters.

**Enforced at:** `src/database/query/borrower.py:100-104`, function `create_borrower()`.

The condition is:

```text
not ssn.isnumeric() or len(ssn) != 9
```


**Not enforced:** The code does not validate an SSN against a more specific pattern than numeric + length 9.

**Classification:** Domain / application.

---

### Rule — Phone number is normalized by removing formatting characters

**Rule:** Before validation, the phone number has the following characters removed:

- `(`
- `)`
- `-`
- spaces

**Enforced at:** `src/database/query/borrower.py:106`, function `create_borrower()`.

**Classification:** Application / domain.

---

### Rule — Phone number must contain exactly 10 numeric characters after normalization

**Rule:** After the listed formatting characters are removed, the phone number must contain only numeric characters and must have exactly 10 characters.

**Enforced at:** `src/database/query/borrower.py:108-112`, function `create_borrower()`.

The condition is:

```text
not phone.isnumeric() or len(phone) != 10
```

**Classification:** Domain / application.

---

### Rule — Borrower SSN must be unique

**Rule:** A new borrower is rejected if an existing borrower has the same normalized SSN.

**Enforced at:** `src/database/query/borrower.py:114-120`, function `create_borrower()`.

The code calls `db.get_borrower_by_ssn(ssn)` at line 114 and rejects creation if a borrower is returned at lines 116-120.

**Classification:** Application / domain.

 Therefore duplicate-SSN prevention is currently implemented in **application code**, not by a database uniqueness constraint.

---

## 4. Book-related business rules found in the specified files

### Rule — A book is available when it has no active loan

**Rule:** Availability is determined by whether there are zero rows for the book's ISBN with `Date_in IS NULL`.

**Enforced at:** `src/database/query/book.py:90-104`, function `book_available_with_isbn()`.

**Classification:** Domain / application, currently implemented through a database query.

---

### Rule — A book with an active loan is unavailable

**Rule:** If at least one loan for the ISBN has `Date_in IS NULL`, the book is considered unavailable.

**Enforced at:** `src/database/query/book.py:91-104`, function `book_available_with_isbn()`.

This is the inverse side of the availability rule and is also relied upon by `create_loan()` at `loan.py:150-156`.

**Classification:** Domain / application.

---

### Rule — Book search availability labels are based on active-loan status

**Rule:** In book search results, a book is represented as unavailable when an active loan exists and available otherwise.

**Enforced at:** `src/database/query/book.py:25-29`, `search_books()`.

The SQL maps an active loan to `Status = 0` and no active loan to `Status = 1`. Availability filters at lines 63-70 then use those values.

**Classification:** Application / presentation-supporting logic.

---

## 5. Loan/check-in rules found in the specified files

### Rule — An active loan is a loan with no return date

**Rule:** A loan is considered active/unreturned when `Date_in IS NULL`.

**Enforced/used at:**

- `src/database/query/loan.py:35-36`, `search_loans()`.
- `src/database/query/loan.py:83-84`, `get_loans_by_borrower_id()`.
- `src/database/query/loan.py:110-111`, `get_loans_by_isbn()`.
- `src/models/dtypes.py:40`, `Loan.is_overdue`.
- `src/database/query/book.py:94-97`, `book_available_with_isbn()`.

**Classification:** Domain.

---

### Rule — Checking in a loan records the current date as the return date

**Rule:** When a loan is checked in successfully, `Date_in` is set to the system's current date.

**Enforced at:** `src/database/query/loan.py:202-221`, functions `checkin()` and `resolve_loan()`.

`resolve_loan()` obtains the current date at line 212, converts it to ISO format at line 213, and writes it to `Date_in` at lines 206-215.

**Classification:** Domain / application.

---

## 6. Consolidated classification table


| Business rule                                            | Currently located / enforced                                                                | Proposed classification                         |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| Borrower must exist before checkout                      | `database/query/loan.py:create_loan()` lines 125-133                                        | Application / domain                            |
| Maximum of 3 active loans; fourth checkout rejected      | `database/query/loan.py:create_loan()` lines 134-140                                        | Application / domain                            |
| Book must exist                                          | `database/query/loan.py:create_loan()` lines 142-148; `book.py:get_book_by_isbn()`          | Application / domain                            |
| Book must have no active loan                            | `database/query/loan.py:create_loan()` 150-156; `book.py:book_available_with_isbn()` 90-104 | Domain / application                            |
| Borrower must have no unpaid fines before checkout       | `database/query/loan.py:create_loan()` 158-164; `fine.py:get_fines_by_borrower_id()` 41-66  | Application / domain                            |
| Checkout lasts 14 days                                   | `database/query/loan.py:create_loan()` 176-181                                              | Domain / application                            |
| Active loan means`Date_in IS NULL`                       | `loan.py`, `book.py`, `models/dtypes.py`                                                    | Domain                                          |
| Overdue means unreturned and current date > due date     | `models/dtypes.py:Loan.is_overdue()` 38-43                                                  | Domain                                          |
| Days overdue = today - due date                          | `database/query/fine.py:update_fines()` 161-165                                             | Domain                                          |
| Fine rate = 25 cents per overdue day                     | `database/query/fine.py:update_fines()` 163-167                                             | Domain                                          |
| Fine amounts are stored, not calculated on every read    | `fine.py:update_fines()` 141-175; `set_fines()` 177-195                                     | Domain calculation + infrastructure persistence |
| Fine update uses stored last-update date                 | `fine.py:set_fines_updated()`, `get_fines_last_updated()`, `update_fines()` 78-87, 141-175  | Application / infrastructure                    |
| New/updated fine is initially unpaid                     | `database/query/fine.py:set_fines()` 177-195                                                | Domain / application                            |
| Borrower must exist to pay fines                         | `database/query/fine.py:pay_fines()` 89-96                                                  | Application / domain                            |
| Payment must be at least total outstanding fines         | `database/query/fine.py:pay_fines()` 98-104                                                 | Domain / application                            |
| Borrower must have fines to make payment                 | `database/query/fine.py:pay_fines()` 106-112                                                | Application / domain                            |
| Fines on actively checked-out books cannot be paid       | `database/query/fine.py:pay_fines()` 114-121                                                | Domain / application                            |
| Successful payment marks fines paid                      | `database/query/fine.py:resolve_fines()` 130-139                                            | Application / infrastructure                    |
| Name, SSN, address, phone are required                   | `database/query/borrower.py:create_borrower()` 85-96                                        | Domain / application                            |
| Hyphens are removed from SSN                             | `database/query/borrower.py:create_borrower()` 98                                           | Application / domain                            |
| SSN must be 9 numeric characters after normalization     | `database/query/borrower.py:create_borrower()` 100-104                                      | Domain / application                            |
| Phone formatting characters are removed                  | `database/query/borrower.py:create_borrower()` 106                                          | Application / domain                            |
| Phone must be 10 numeric characters after normalization  | `database/query/borrower.py:create_borrower()` 108-112                                      | Domain / application                            |
| Duplicate SSNs are rejected                              | `database/query/borrower.py:create_borrower()` 114-120                                      | Application / domain                            |
| Duplicate SSNs are not protected by DB UNIQUE constraint | `database/schema.py:43-50` (verification)                                                   | Infrastructure observation                      |
| Check-in sets return date to current date                | `database/query/loan.py:resolve_loan()` 205-221                                             | Domain / application                            |

---

## 7. Key findings for the architecture discussion

The most important finding is that the project **does have identifiable business rules**, but many of them currently live inside modules named `database/query/...` rather than being isolated from database access.

The clearest examples are:

1. **Checkout eligibility rules** — `database/query/loan.py:create_loan()`.
2. **Fine calculation rules** — `database/query/fine.py:update_fines()`.
3. **Fine-payment eligibility rules** — `database/query/fine.py:pay_fines()`.
4. **Borrower validation and uniqueness rules** — `database/query/borrower.py:create_borrower()`.
5. **Overdue determination** — `models/dtypes.py:Loan.is_overdue()`.
6. **Book availability determination** — `database/query/book.py:book_available_with_isbn()`.

This means the codebase does not have a single obvious location for business rules. Rules are distributed between the database-query modules and the model layer, with database access and business decisions often mixed in the same functions.

The proposed classifications above are a **first-pass classification only**. They should be confirmed by the team before Phase 2, as requested by the assignment.
