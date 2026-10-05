# Loan Rules Classification

## Purpose

This document classifies the responsibilities currently contained in `src/database/query/loan.py`. The purpose is to distinguish business rules from database persistence operations and boundary/presentation concerns before the code is refactored in Phase 4.

The classification covers:

- `create_loan()`
- `checkin()`
- `resolve_loan()`
- `checkin_many()`

# 1. `create_loan()`

File: `src/database/query/loan.py`

The `create_loan()` function currently combines database operations, library business rules, date calculations, and result-message construction.


| Code / Concept                                                | Classification                                 | Explanation                                                                                    |
| ------------------------------------------------------------- | ---------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `db.get_borrower_by_id(borrower_id)`                          | Persistence                                    | Retrieves the borrower from the database.                                                      |
| `if not borrower`                                             | Business rule                                  | Enforces the rule that a borrower must exist before a loan can be created.                     |
| `OperationResult(status=False, message="Borrower not found")` | Boundary/Presentation                          | Communicates the failed operation to the caller.                                               |
| `db.get_loans_by_borrower_id(borrower_id, returned=False)`    | Persistence                                    | Retrieves the borrower's active loans from the database.                                       |
| `len(checkouts) >= 3`                                         | Business rule                                  | Enforces the maximum of three active checkouts per borrower.                                   |
| `OperationResult(... "Too many checkouts")`                   | Boundary/Presentation                          | Communicates that the checkout limit was reached.                                              |
| `db.get_book_by_isbn(isbn)`                                   | Persistence                                    | Retrieves the requested book from the database.                                                |
| `if not book`                                                 | Business rule                                  | Enforces the rule that the book must exist before it can be checked out.                       |
| `OperationResult(... "Book doesn't exist")`                   | Boundary/Presentation                          | Communicates that the requested book does not exist.                                           |
| `db.book_available_with_isbn(isbn)`                           | Persistence                                    | Retrieves the book's availability information.                                                 |
| `if not book_available`                                       | Business rule                                  | Enforces the rule that an already checked-out book cannot be checked out again.                |
| `OperationResult(... "Book already checked out.")`            | Boundary/Presentation                          | Communicates the availability rule failure.                                                    |
| `db.get_fines_by_borrower_id(borrower_id)`                    | Persistence                                    | Retrieves the borrower's fines from the database.                                              |
| `len(borrowers_fines) > 0`                                    | Business rule                                  | Enforces the rule that a borrower with pending fines cannot check out another book.            |
| `OperationResult(... "Borrower has pending fines.")`          | Boundary/Presentation                          | Communicates the failed checkout to the caller.                                                |
| `INSERT INTO BOOK_LOANS`                                      | Persistence                                    | Inserts the new loan record into the database.                                                 |
| `db.get_current_date()`                                       | Persistence/dependency                         | Obtains the current date through the database layer.                                           |
| `date.today()`                                                | Time/system dependency                         | Provides the current system date when the database does not provide one.                       |
| `date_out = today.isoformat()`                                | Persistence/storage preparation                | Converts the checkout date into the string format used for storage.                            |
| `due_date = (today + timedelta(days=14)).isoformat()`         | Mixed: Business rule + Persistence preparation | The 14-day calculation is a business rule, while`isoformat()` converts it to a storage format. |
| `params = [...]`                                              | Persistence preparation                        | Prepares values for the SQL operation.                                                         |
| `query.try_execute_one(sql, params)`                          | Persistence                                    | Executes the database insert.                                                                  |
| `OperationResult(...)`                                        | Boundary/Presentation                          | Constructs the result returned to the caller.                                                  |

## Mixed Responsibilities in `create_loan()`

### 1. Checkout count

```python
checkouts = db.get_loans_by_borrower_id(borrower_id, returned=False)

if checkouts and len(checkouts) >= 3:
```

The first statement retrieves data from the database, while the second applies the business rule to that data. The persistence operation and business decision are therefore closely coupled.

### 2. Book availability

```python
book_available = db.book_available_with_isbn(isbn)

if not book_available:
```

The availability value comes from persistence, while the decision that the book cannot be checked out is a business rule.

### 3. Pending fines

```python
borrowers_fines = db.get_fines_by_borrower_id(borrower_id)

if borrowers_fines and len(borrowers_fines) > 0:
```

The database supplies the fines, while the decision that pending fines prevent checkout is business logic.

### 4. Due-date calculation and storage formatting

```python
due_date = (today + timedelta(days=14)).isoformat()
```

This line performs two jobs: calculating the 14-day due date (business rule) and converting the result into a database storage format (persistence preparation).

### 5. Final result

```python
return OperationResult(
    status=query.try_execute_one(sql, params),
    message="Book successfully checked out!"
)
```

This combines persistence (`query.try_execute_one`) with boundary/presentation (`OperationResult` and its message).

# 2. `checkin()`

File: `src/database/query/loan.py`

```python
def checkin(loan_id: int) -> OperationResult:
    return db.resolve_loan(loan_id)
```


| Code / Concept             | Classification                                       | Explanation                                                                                     |
| -------------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `db.resolve_loan(loan_id)` | Persistence                                          | Delegates the loan check-in operation to the database layer.                                    |
| Returned`OperationResult`  | Boundary/Presentation inherited from`resolve_loan()` | The result is returned to the caller, although`checkin()` itself does not construct the result. |

### Observation

`checkin()` contains no explicit business-rule check. It primarily acts as a wrapper around `resolve_loan()`.

# 3. `resolve_loan()`

File: `src/database/query/loan.py`


| Code / Concept                                 | Classification                  | Explanation                                               |
| ---------------------------------------------- | ------------------------------- | --------------------------------------------------------- |
| `UPDATE BOOK_LOANS`                            | Persistence                     | Updates the loan record in the database.                  |
| `SET Date_in = ?`                              | Persistence                     | Stores the check-in date in the database.                 |
| `WHERE Loan_id = ?`                            | Persistence                     | Identifies the loan record to update.                     |
| `db.get_current_date()`                        | Persistence/dependency          | Obtains the current date through the database layer.      |
| `date.today()`                                 | Time/system dependency          | Provides a fallback current date.                         |
| `date_in = today.isoformat()`                  | Persistence/storage preparation | Converts the return date into the storage format.         |
| `params = [date_in, loan_id]`                  | Persistence preparation         | Prepares values for the SQL update.                       |
| `query.try_execute_one(sql, params)`           | Persistence                     | Executes the database update.                             |
| `OperationResult(status=success, message=...)` | Boundary/Presentation           | Constructs the result and message returned to the caller. |

### Observation

`resolve_loan()` contains persistence and boundary/presentation responsibilities. It does not contain an explicit business-rule decision comparable to the three-checkout or 14-day rules in `create_loan()`.

# 4. `checkin_many()`

File: `src/database/query/loan.py`

```python
def checkin_many(loans: list[Loan]) -> OperationResult:
```


| Code / Concept                     | Classification             | Explanation                                                        |
| ---------------------------------- | -------------------------- | ------------------------------------------------------------------ |
| `for loan in loans`                | Boundary/result processing | Iterates over the supplied loans for processing.                   |
| `db.checkin(loan.id)`              | Persistence                | Initiates the check-in operation for each loan.                    |
| `.status`                          | Boundary/result handling   | Reads the status returned by the check-in operation.               |
| `if not success`                   | Boundary/result handling   | Determines whether an individual check-in failed.                  |
| `isbns.append(loan.isbn)`          | Boundary/result handling   | Records the ISBN of a failed check-in.                             |
| `not isbns`                        | Boundary/result handling   | Determines the overall success status from the individual results. |
| `"Books checked in successfully."` | Boundary/Presentation      | Creates the success message.                                       |
| `"Failed to check in: ..."`        | Boundary/Presentation      | Creates the failure message containing failed ISBNs.               |
| `OperationResult(...)`             | Boundary/Presentation      | Constructs the final result returned to the caller.                |

### Mixed Responsibility in `checkin_many()`

The main mixed area is:

```python
success = db.checkin(loan.id).status
```

This statement initiates a database-backed check-in operation and immediately consumes its result status.

The function therefore coordinates persistence while also handling and aggregating the results for presentation.

# Summary of the Current Responsibilities


| Function         |            Business Rule | Persistence | Boundary/Presentation |
| ---------------- | -----------------------: | ----------: | --------------------: |
| `create_loan()`  |                      Yes |         Yes |                   Yes |
| `checkin()`      |         No explicit rule |         Yes |        Returns result |
| `resolve_loan()` |         No explicit rule |         Yes |                   Yes |
| `checkin_many()` | No explicit library rule |         Yes |                   Yes |

`create_loan()` contains the largest mixture of responsibilities. It combines borrower lookup, checkout-limit validation, book lookup, availability checking, fine checking, date calculation, database insertion, and result-message construction.

# Key Findings for Phase 4

The main business rules identified in `create_loan()` are:

1. A borrower must exist before a loan is created.
2. A borrower may have at most three active checkouts.
3. The requested book must exist.
4. The requested book must be available.
5. A borrower with pending fines cannot check out a book.
6. A loan's due date is 14 days after the checkout date.

The wider loan/domain logic also contains the overdue rule:

7. A loan is overdue when it has not been returned and the current date is after its due date.

The fine rule identified earlier is:

8. An overdue fine is calculated as the number of overdue days multiplied by 25.

These rules are currently coupled to database operations in different parts of the system.

## Architectural Implication

The classification provides a map for Phase 4. Business rules should eventually be separated from persistence operations so that domain logic can operate independently of SQLite.
