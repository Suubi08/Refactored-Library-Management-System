Where clean architecture is violated
The dependency rule is violated. Every screen and modal does import database as db and calls it directly (book_detail, borrower_detail, create_borrower, settings, time_travel, init_prompt, home, book_search, borrower_search).
From book_detail: Import database as db, calls db.get, db.create, db.checkin instead of depending on abstraction. There’s no service layer between the UI and data. The UI depends on the Database (SQLite).


Single Responsibility violated: init.py re-exports everything with import*, so the UI depends on function names, renaming or changing any breaks the UI.
For example: db.create_loan(isbn, id), db.checkin(loan.id), db.checkin_many( ), db.pay_fines( ) db.create_borrower and db.search_books( ). Any rename change breaks the screens and modals.
borrower_detail.py: computes days overdue (date_in or db.get_current_date() or date.today()) - due_date) inside a widget.
book_detail.py: uses db.get_loans_by_borrower_id(...)[0] to find a book's loan. This is fragile because it assumes ordering, and it is domain logic in the view.
home.py/settings.py: the UI decides on db.exists() / db.is_initialized() and performs init/delete/reset_time, so it handles infrastructure lifecycle.

Business rules live in the data layer. Business rules are tied to the database, making rules depend on database. create_loan enforces the loan limit, create_borrower validates SSN and phone and checks duplicates, and fines are computed in database/query
UI reaches into infrastructure config. Modals import database.config (config.db_name), and app.py calls db.config.set_db_name. Presentation code knows database file details.

Models are not independent. models/result.py mixes domain-like entities with UI-shaped DTOs (BookSearchResult, with pydantic aliases like Card_id and Author_names that mirror SQL column names). The core data structures are shaped by the DB schema rather than by the domain.

Circular/self-referencing coupling inside the data layer. Modules do import database as db and call each other (e.g. borrower.py → db.get_borrower_by_ssn), so there is no clean layering even within the database package.

Impact statement

Because the UI calls db.* in 9 files, any change to the database interface breaks book_detail, borrower_detail, create_borrower, settings, time_travel, home, init_prompt, and both search screens at once. The presentation layer is effectively a client of the SQL layer.

Suggested remedy (to close the section)

Introduce a service/use-case layer (LoanService, BorrowerService, FineService) that uses repository interfaces. Move rules like the loan limit, SSN and phone validation, and fine calculation into it. The UI then depends only on the services.

Testing note for Part B: the zip contains no test files and no pytest in pyproject.toml/requirements.txt, so the current test status is "no automated tests". The layering problems above are the reason: rules can't be tested without a real SQLite database.

