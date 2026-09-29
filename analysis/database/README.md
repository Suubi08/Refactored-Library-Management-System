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
