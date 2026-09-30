# Current Architecture State

## Purpose

This document records the current state of the Library Management System as understood from the codebase. It focuses on concrete violations of Clean Architecture principles and the risks those violations create. It is a baseline for discussion and future refactoring, not a claim that the application must immediately be rewritten.

## Executive Summary

The repository describes the application as a layered architecture with presentation, data model, and persistence layers. In practice, the boundaries between those layers are porous:

- Textual screens and modals import the top-level `database` package and call persistence operations directly.
- Database query modules construct Pydantic objects and return presentation-oriented result types.
- Database query modules also contain input validation, business rules, and user-facing messages.
- Pydantic domain-like models depend on the database package and global database configuration.
- The database package exposes most of its implementation through wildcard imports, making the dependency graph implicit.
- Application startup and database initialization use process-wide mutable state and perform side effects during command handling and UI startup.

The result is a codebase that is functional but tightly coupled to Textual, SQLite, module-level configuration, and the current wording of UI messages. The main architectural cost is testability: business behavior cannot be exercised cleanly without involving the database layer, and UI code cannot be changed independently of persistence details.

## Observed Dependency Direction

The effective dependency direction is currently closer to:

```text
Textual screens/modals -> database facade -> query modules -> SQLite
         |                       |
         +-> models/result.py    +-> models/dtypes.py
                                      |
                                      +-> database.config
```

This differs from Clean Architecture, where frameworks and persistence details should depend on application use cases and domain rules, rather than the other way around.

## Concrete Violations

### 1. Presentation depends directly on persistence

Examples:

- `src/ui/screens/book_search.py` defines a search callback that calls `db.search_books()`.
- `src/ui/modals/create_borrower.py` calls `db.create_borrower()` directly after reading widget values.
- `src/ui/modals/book_detail.py` calls `db.get_borrower_by_id()`, `db.get_loans_by_isbn()`, `db.create_loan()`, and `db.checkin()`.

This makes UI classes responsible for knowing that the application uses the database facade and which persistence operations exist. A Textual event handler is therefore also an integration point with SQLite.

**Clean Architecture issue:** the outer presentation layer reaches across the application boundary instead of invoking an application use case through a stable interface.

**Impact:** UI tests require database setup, persistence changes ripple into widgets, and another interface such as a web API would have to duplicate the same orchestration.

### 2. Business rules live in query/persistence modules

`src/database/query/borrower.py` validates required fields, normalizes SSN and phone values, checks duplicate borrowers, builds user-facing messages, and performs the insert in `create_borrower()`.

Loan and fine operations in the query package similarly combine validation, business decisions, SQL construction, and result formatting. The query package is therefore acting as repository, service, validator, and controller at once.

**Clean Architecture issue:** application rules are coupled to the database adapter and SQL implementation.

**Impact:** rules are difficult to reuse outside SQLite and difficult to test without opening a database connection. Changes to validation or business policy require editing persistence code.

### 3. Persistence returns presentation-oriented models

`src/database/query/book.py` returns `BookSearchResult`, and `src/database/query/borrower.py` returns `BorrowerSearchResult`. These types live in `src/models/result.py` and include display serializers such as `"Available"`, dollar formatting, and table-oriented aggregate fields.

**Clean Architecture issue:** a persistence adapter chooses objects shaped for the current screen instead of returning domain entities or application output models through a defined port.

**Impact:** database queries are coupled to the current UI representation. A different consumer would inherit fields and formatting decisions intended for the Textual tables.

### 4. Domain-like models depend on infrastructure

`src/models/dtypes.py` imports `database as db`. The `Loan.is_overdue` property calls `db.get_current_date()` to obtain the current date.

**Clean Architecture issue:** an inner model depends on an outer database/configuration module. The domain object cannot determine overdue status from its own state and an explicit clock or date value.

**Impact:** model tests need database state, simulated time is hidden, and the domain rule is not deterministic from the method inputs. It also creates a circular architectural dependency between models and persistence.

### 5. User-interface concerns leak into lower layers

`OperationResult` carries free-form user messages, and database functions return messages such as `"Borrower created successfuly!"`. The UI displays those values directly through `notify()`.

**Clean Architecture issue:** persistence/application code knows the wording and presentation mechanism expected by the Textual UI.

**Impact:** localization, consistent error handling, accessibility improvements, and alternate clients become harder. A lower layer cannot report structured failure reasons independently of UI copy.

### 6. Global mutable configuration controls infrastructure

`src/database/config.py` stores `db_name` as a module-level global. `set_db_name()` mutates that value, and query helper functions open connections using it implicitly.

`src/app.py` and `src/main.py` both configure and use the database through this global state. Importing `app` also creates the global `LibraryApp` instance.

**Clean Architecture issue:** infrastructure dependencies are hidden rather than injected at the composition root.

**Impact:** multiple databases cannot be used safely in the same process, tests can interfere with each other, and call behavior depends on operation order and prior initialization.

### 7. The database facade hides the real dependency graph

`src/database/__init__.py` uses wildcard imports from initialization and every query module. Callers can access a large implicit API through `import database as db`, while ownership of functions and dependencies is unclear.

**Clean Architecture issue:** module boundaries and ports are not explicit.

**Impact:** accidental coupling is easy, static navigation is less precise, and refactoring a query function can have non-obvious consumers.

### 8. Startup and infrastructure side effects are mixed with application bootstrapping

`LibraryApp.on_mount()` checks database state and updates fines before pushing the first screen. `main.py` handles argument parsing, database selection, initialization, deletion, test-data loading, and application startup in one procedure.

**Clean Architecture issue:** composition, infrastructure setup, and application behavior are not separated into distinct use cases or adapters.

**Impact:** startup behavior is difficult to test in isolation and the UI lifecycle is coupled to database maintenance operations.

## Additional Code-Quality Signals

These are not all Clean Architecture violations by themselves, but they reinforce the same coupling:

- Database helpers catch SQLite errors, print them, and return `None` or `False`, which loses structured failure information.
- Database connections are opened and closed inside each helper, so transaction boundaries are controlled by low-level functions rather than an application use case.
- SQL query modules import `database as db` in places where direct imports or an injected repository would make dependencies clearer.
- The repository structure shown in the project metadata contains no test suite, so the architectural seams are not currently protected by automated tests.
- The README describes intended behavior and layering, but the implementation does not define explicit application/use-case or repository interfaces.

## Current Strengths

The codebase already has useful pieces that can support a gradual improvement:

- Database access is at least grouped under `src/database` rather than scattered raw SQLite calls throughout every widget.
- Pydantic models provide a consistent place for data validation and serialization behavior.
- `OperationResult` expresses a basic success/failure contract.
- Query helper functions centralize connection creation and common SQLite operations.
- UI composition is separated into screens, modals, and reusable components.

These are useful seams, but they currently serve as conventions rather than enforced architectural boundaries.

## Recommended Target Direction

A pragmatic Clean Architecture transition would introduce explicit boundaries in this order:

1. Define application use cases for operations such as search books, create borrower, check out, check in, and pay fines.
2. Move business validation and rules into those use cases or domain services, using structured error codes rather than UI strings.
3. Define repository protocols in an inner application/domain package.
4. Adapt the current SQLite query functions behind repository implementations.
5. Pass repositories, a clock, and configuration into use cases instead of reading module globals.
6. Keep Textual event handlers responsible for translating widget input to use-case requests and translating responses to UI state/messages.
7. Replace wildcard exports with explicit module APIs as the boundaries become stable.
8. Add focused tests for domain rules and use cases before changing UI behavior.

The first small refactoring should be the borrower creation flow because it contains all the main problems in one path: UI input handling, validation, duplicate checking, user-facing messages, SQL persistence, and global database access.

## Scope and Assumptions

This assessment is based on the current source tree and README. It describes static dependencies and visible control flow; it does not claim that every runtime path has been exercised. The document intentionally does not classify raw SQL or the use of SQLite itself as an architectural violation. Those are implementation choices that can remain behind a persistence boundary.