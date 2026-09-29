## TASK 1: Database Schema Description 
This library management system employs the use of SQLite to maintain its database. 
Within this database, there are seven core tables which store data on books, authors, borrowers, loans, fines, and application metadata.
## Database Tables 
1. BOOK - This table holds data on library books. 
- The primary key (PK) of this table is Isbn. 
- This table also includes Title, which stores the title of each book. 
- All of the above columns are NOT NULL.

2. AUTHORS
  - Stores information about book authors.
  - `Author_id` is the Primary Key (PK).
  - `Name` stores the author's name.
  - Both fields are `NOT NULL`.

3. BOOK_AUTHORS
  - Links books to their authors.
  - Uses a composite Primary Key: `(Author_id, Isbn)`.
  - `Author_id` is a Foreign Key (FK) referencing `AUTHORS`.
  - `Isbn` is a Foreign Key (FK) referencing `BOOK`.
  - Supports a **many-to-many relationship** between books and authors.

4. BORROWER
  - Stores library borrower information.
  - `Card_id` is the Primary Key and is automatically generated.
  - `Ssn` stores the borrower's identification number.
  - `Bname` stores the borrower's name.
  - `Address` stores the borrower's address.
  - `Phone` stores the borrower's phone number.
  - `Ssn`, `Bname`, `Address`, and `Phone` are `NOT NULL`.

5. BOOK_LOANS
  - Stores book borrowing transactions.
  - `Loan_id` is the Primary Key and is automatically generated.
  - `Isbn` is a Foreign Key referencing `BOOK`.
  - `Card_id` is a Foreign Key referencing `BORROWER`.
  - `Date_out` records when the book was borrowed.
  - `Due_date` records when the book should be returned.
  - `Date_in` records when the book was returned and can be `NULL` for an active loan.

6. FINES
  - Stores fines associated with loans.
  - `Loan_id` is both the Primary Key and a Foreign Key referencing `BOOK_LOANS`.
  - `Fine_amt` stores the fine amount.
  - `Paid` records whether the fine has been paid.
  - A loan can have **zero or one fine record**.

7. metadata
  - Stores application-level key-value information.
  - `key` is the Primary Key.
  - `value` stores the corresponding value.
  - It has no Foreign Key relationships with the other tables.


Relationships
- AUTHOR → BOOK_AUTHORS: One-to-Many
- BOOK → BOOK_AUTHORS: One-to-Many
- AUTHOR ↔ BOOK: Many-to-Many through `BOOK_AUTHORS`
- BOOK → BOOK_LOANS: One-to-Many
- BORROWER → BOOK_LOANS: One-to-Many
- BOOK_LOANS → FINES: One-to-Zero-or-One
- metadata: Independent table with no relationships to the library entities.

## Database Constraints
- Primary Key (PK): Uniquely identifies each record.
- Foreign Key (FK): Connects a record to a related record in another table.
- NOT NULL: Prevents a field from containing SQL `NULL`.
- AUTOINCREMENT: Automatically generates numeric IDs for borrowers and loans.
- Composite Primary Key:`BOOK_AUTHORS` uses `(Author_id, Isbn)` to uniquely identify each author-book combination.
- Nullable `Date_in`: Allows a loan to exist without a return date when the book has not yet been returned.

## Business Rules Not Enforced by the Schema
The database schema does not directly enforce some rules. These are handled by application code, including:

- Maximum number of active loans per borrower.
- Loan duration.
- Fine calculation.
- Preventing borrowers with outstanding fines from borrowing.
- SSN validation and duplicate SSN checking.
- Phone number validation.

## TASK 2 Query responsibilities
The `database/query/` directory contains modules responsible for retrieving,
storing, and modifying database-related data. However, some modules also
contain application and business logic.

| File | Main Responsibility |
|---|---|
| `book.py` | Book data retrieval and availability checking |
| `borrower.py` | Borrower retrieval, searching, creation, and validation |
| `loan.py` | Loan retrieval and checkout/check-in operations with embedded business logic |
| `fine.py` | Fine retrieval and payment/update operations with embedded business logic |
| `author.py` | Author retrieval by ID |
| `conf.py` | Application date and initialization state management, including triggering fine updates |
| `metadata.py` | Key-value application metadata retrieval and storage |
| `query.py` | Low-level SQLite query execution, connection handling, commits, and rollbacks |

### Key Observation

The query modules are not purely persistence-focused.

Several modules contain business or application logic in addition to database
access. In particular:

- `borrower.py` performs SSN and phone validation and duplicate SSN checking.
- `loan.py` contains loan operation rules.
- `fine.py` contains fine calculation and payment-related rules.
- `conf.py` triggers fine updates when the application date is reset.

This creates coupling between **business rules and database access**, which is
important for the later Clean Architecture refactoring.

## TASK 3

Before classifying each function, it is important to understand the difference
between **Database Access** and **Business Logic**.

**Database Access** means a function is mainly responsible for talking to the
database. In simple terms, it is responsible for getting information from the
database, saving new information, or updating existing information.

For example, asking the database, *"Give me the borrower with this ID"* is
Database Access.

**Business Logic** means a function contains the rules or decisions that make
the Library Management System behave according to its requirements.

For example, the rule *"a borrower cannot have more than three active loans"*
is Business Logic. It is a rule about how the library operates, not simply
about storing information.

**Both** means a function performs Database Access while also applying
Business Logic. For example, a function may check whether a borrower is
allowed to borrow a book and then save the loan into the database.

The purpose of this classification is to identify where database persistence
and business rules are currently mixed together. This is important for the
Clean Architecture refactoring because business rules should not be tightly
coupled to database details.

### Classification Key

- **Database Access** — Mainly communicates with the database.
- **Business Logic** — Mainly applies rules, decisions, or calculations.
- **Both** — Performs database access and also applies business logic.


## 3.1 `database/query/book.py`

| Function | Classification | Reason |
|---|---|---|
| `search_books()` | Database Access | Searches and retrieves book records from the database. |
| `get_book_by_isbn()` | Database Access | Retrieves a book using its ISBN. |
| `book_exists_with_isbn()` | Database Access | Checks whether a book exists in the database. |
| `book_available_with_isbn()` | Both | Accesses loan information and interprets it to determine whether the book is available. |

**Finding:** Most functions in `book.py` are concerned with database retrieval. `book_available_with_isbn()` also contains application-level interpretation of book availability.

---

## 3.2 `database/query/author.py`

| Function | Classification | Reason |
|---|---|---|
| `get_author_by_id()` | Database Access | Retrieves an author from the database using the author ID. |

**Finding:** This function is concerned with database retrieval and does not contain significant business rules.

---

## 3.3 `database/query/borrower.py`

| Function | Classification | Reason |
|---|---|---|
| `search_borrowers()` | Database Access | Searches and retrieves borrower records. |
| `get_borrower_by_ssn()` | Database Access | Retrieves a borrower using the SSN. |
| `get_borrower_by_id()` | Database Access | Retrieves a borrower using the card ID. |
| `_get_borrower()` | Database Access | Internal helper used to retrieve borrower information. |
| `create_borrower()` | Both | Validates borrower information, checks for duplicate SSN, and then inserts the borrower into the database. |

**Finding:** `create_borrower()` mixes database persistence with borrower validation rules.

---

## 3.4 `database/query/loan.py`

| Function | Classification | Reason |
|---|---|---|
| `search_loans()` | Database Access | Searches and retrieves loan records. |
| `get_all_loans()` | Both | Retrieves loans and applies overdue interpretation. |
| `get_loans_by_borrower_id()` | Database Access | Retrieves loans belonging to a borrower. |
| `get_loans_by_isbn()` | Database Access | Retrieves loans associated with a book. |
| `checkout()` | Both | Participates in the checkout operation and loan creation process. |
| `checkin()` | Both | Processes book returns and related application decisions. |
| `create_loan()` | Both | Checks borrowing rules, determines the due date, and creates the loan record in the database. |

**Finding:** `loan.py` contains significant business logic within the persistence layer. `create_loan()` is particularly important because it combines borrowing rules with database persistence.

---

## 3.5 `database/query/fine.py`

| Function | Classification | Reason |
|---|---|---|
| `get_all_fines()` | Database Access | Retrieves fine records from the database. |
| `get_fines_by_borrower_id()` | Database Access | Retrieves fines belonging to a borrower. |
| `get_total_fines_by_borrower_id()` | Both | Retrieves fine records and calculates their total. |
| `set_fines_updated()` | Database Access | Stores information about when fines were updated. |
| `get_fines_last_updated()` | Database Access | Retrieves the last fine-update information. |
| `pay_fines()` | Both | Checks payment conditions and updates fine records. |
| `set_fines()` | Database Access | Stores fine information in the database. |
| `update_fines()` | Both | Calculates overdue fines and stores the resulting fine information. |

**Finding:** `pay_fines()` and `update_fines()` combine business rules with database persistence. `get_total_fines_by_borrower_id()` also performs a calculation after retrieving database data.

---

## 3.6 `database/query/conf.py`

| Function | Classification | Reason |
|---|---|---|
| `get_current_date()` | Database Access | Retrieves the stored application date. |
| `set_current_date()` | Database Access | Stores the application date. |
| `reset_time()` | Both | Changes application state and triggers fine updating. |
| `is_initialized()` | Database Access | Retrieves the application initialization state. |
| `set_initialized()` | Database Access | Stores the application initialization state. |

**Finding:** Most functions in `conf.py` handle application configuration stored in the database. `reset_time()` also coordinates application behaviour and therefore is classified as Both.

---

## 3.7 `database/query/metadata.py`

| Function | Classification | Reason |
|---|---|---|
| `get_value()` | Database Access | Retrieves a metadata value from the database. |
| `set_value()` | Database Access | Stores a metadata value in the database. |

**Finding:** These functions are primarily concerned with database persistence.

---

## 3.8 `database/query/query.py`

| Function | Classification | Reason |
|---|---|---|
| `get_one_or_none()` | Database Access | Executes a database query and retrieves one result. |
| `get_all_or_none()` | Database Access | Executes a database query and retrieves multiple results. |
| `try_execute_many()` | Database Access | Executes database operations involving multiple parameter sets. |
| `try_execute_one()` | Database Access | Executes a database operation involving one parameter set. |

**Finding:** `query.py` is the lowest-level database access module. Its functions deal directly with database connections, SQL execution, commits, rollbacks, and retrieving results. No significant business rules were identified here.

---

## 3.9 Overall Finding

The analysis shows that the `database/query/` package is **not purely a
persistence layer**.

Most functions perform Database Access only. However, several functions
combine Database Access with Business Logic.

The main mixed-responsibility functions are:

- `book_available_with_isbn()`
- `create_borrower()`
- `get_all_loans()`
- `checkout()`
- `checkin()`
- `create_loan()`
- `get_total_fines_by_borrower_id()`
- `pay_fines()`
- `update_fines()`
- `reset_time()`

The most significant examples are `create_loan()`, `pay_fines()`, and
`update_fines()` because they combine library rules or calculations with
database persistence.

This indicates that the current system has coupling between **business rules**
and the **SQLite persistence mechanism**. These mixed responsibilities are
important candidates for separation during the Clean Architecture
refactoring.
