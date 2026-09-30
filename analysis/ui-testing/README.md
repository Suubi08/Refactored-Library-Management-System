<<<<<<< HEAD
=======

The dependency rule is violated. Every screen and modal does import database as db and calls it directly instead of depending on abstraction. (book_detail, borrower_detail, create_borrower, settings, time_travel, init_prompt, home, book_search, borrower_search).The UI depends on the Database (SQLite).
>>>>>>> ad5cbe5 (summarize analysis)

The dependency rule is violated. Every screen and modal does import database as db and calls it directly (book_detail, borrower_detail, create_borrower, settings, time_travel, init_prompt, home, book_search, borrower_search).The UI depends on the Database (SQLite).

Single Responsibility violated: init.py re-exports everything with import*, so the UI depends on function names, renaming or changing any breaks the UI. Any rename change breaks the screens and modals.
home.py/settings.py: the UI decides on db.exists() / db.is_initialized() and performs init/delete/reset_time, so it handles infrastructure lifecycle. 

Business rules live in the data layer. Business rules are tied to the database, making rules depend on database. create_loan enforces the loan limit,"book already checked out," "pending fines block checkout," SSN/phone validation, duplicate-SSN check, and the $0.25/day fine calculation all live inside `database/query/*.py`, coupled to SQL execution. They cannot be unit-tested without a live SQLite database.
Some business logic also leaks into the UI itself: `book_detail.py` selects `get_loans_by_borrower_id(...)[0]` to find "the" active loan; `borrower_detail.py` computes overdue days from `db.get_current_date()`

Impact statement
Because the UI calls db, 9 of 11 UI files import `database` directly (`import database as db`) any change to the database interface breaks book_detail, borrower_detail, create_borrower, settings, time_travel, home, init_prompt, and both search screens at once, there is no service/repository layer between UI and SQL.



Suggested remedy

Introduce a service/use-case layer (LoanService, BorrowerService, FineService) that uses repository interfaces. Move rules like the loan limit, SSN and phone validation, and fine calculation into it. The UI then depends only on the services.


