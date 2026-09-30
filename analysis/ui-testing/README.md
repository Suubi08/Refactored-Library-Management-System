<<<<<<< HEAD
=======

The dependency rule is violated. Every screen and modal does import database as db and calls it directly instead of depending on abstraction. (book_detail, borrower_detail, create_borrower, settings, time_travel, init_prompt, home, book_search, borrower_search).The UI depends on the Database (SQLite).
>>>>>>> ad5cbe5 (summarize analysis)

The dependency rule is violated. Every screen and modal does import database as db and calls it directly (book_detail, borrower_detail, create_borrower, settings, time_travel, init_prompt, home, book_search, borrower_search).The UI depends on the Database (SQLite).

Single Responsibility violated: init.py re-exports everything with import*, so the UI depends on function names, renaming or changing any breaks the UI. Any rename change breaks the screens and modals.
home.py/settings.py: the UI decides on db.exists() / db.is_initialized() and performs init/delete/reset_time, so it handles infrastructure lifecycle.

Business rules live in the data layer. Business rules are tied to the database, making rules depend on database. create_loan enforces the loan limit, create_borrower validates SSN and phone and checks duplicates, and fines are computed in database/query.

Models are not independent. models/result.py mixes domain-like entities with UI-shaped DTOs (BookSearchResult, with pydantic aliases like Card_id and Author_names that mirror SQL column names). The core data structures are shaped by the DB schema rather than by the domain.

Impact stateme
Because the UI calls db.* in 9 files, any change to the database interface breaks book_detail, borrower_detail, create_borrower, settings, time_travel, home, init_prompt, and both search screens at once. 

Suggested remedy

Introduce a service/use-case layer (LoanService, BorrowerService, FineService) that uses repository interfaces. Move rules like the loan limit, SSN and phone validation, and fine calculation into it. The UI then depends only on the services.


