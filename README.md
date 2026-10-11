# Library Management System (refactored)

A terminal library-management application (books, borrowers, loans, fines) built with Python, Textual and SQLite. This repository is a refactoring of a supplied baseline for **CSC 3115 Advanced Programming**. The checkout workflow was moved toward Clean Architecture (R. C. Martin) without changing behaviour, then reviewed with automated tools.

- Repository: https://github.com/Suubi08/Refactored-Library-Management-System
- Baseline commit: 17c0b7c
- Final commit: `<FINAL_COMMIT>`
- Group members: SUUBI BAKER KANE 24/U/26049/EVE
                 NABAGGALA MARION 24/U/24336/PS
                 NANSWA PATRICIA  24/U/27188/EVE
                 NAKITTO ROSEMARY 24/U/26589/EVE

## What changed

Only the **checkout workflow** was migrated to a use case (plus two small extractions into `domain/`: the fine calculation, which the database layer now calls, and Borrower validation, which is tested but not yet called by borrower creation); the rest of the system still runs on the original code. The aim was a small, verifiable slice rather than a rewrite.

```
src/
  domain/            Framework-free business rules. Imports nothing internal.
                     entities/: Loan (is_overdue), Book, Borrower (validate)
                     services/: fine_calculator (used by database/query/fine.py)
  application/       Use cases and ports (CheckoutBook, repository Protocols).
  infrastructure/    SQLite adapters that wrap the existing database functions.
  composition_root.py  Builds the use case with its adapters.
  database/          Original persistence code (schema, queries, CSV import).
  models/            Original Pydantic types and result types.
  ui/ , app.py, main.py   Textual user interface and entry point.
tests/
  characterization/  123 tests pinning the baseline behaviour.
  domain/            6 tests: Loan, Borrower validation, fine calculation (no database).
  application/       7 use case tests with in-memory fakes.
  infrastructure/    12 tests: SQLite adapters and checkout regression tests.
```

Dependencies point inward: `ui -> composition_root -> infrastructure/application -> domain`. Two known exceptions remain and are listed under *Known limitations*.

## Requirements

- Python 3.12
- Dependencies in `requirements.txt` (`textual`, `textual-dev`, `pydantic`); `pyproject.toml` and `uv.lock` are included.
- Test and review tools: `pytest`, `pytest-cov`, `ruff`, `bandit`, `pip-audit`.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-cov ruff bandit pip-audit
```

## Run the application

```bash
uv run python src\main.py (on windows)
uv run textual serve src/app.py (on ubuntu linux)
```

On first start, use the settings screen to initialise the database. The data is seeded from `data/book.csv` and `data/borrower.csv`. A fresh database has no stored "current date"; checkout falls back to today's date, as the original code did.

## Run the tests

```bash
pytest -q                                          # 148 tests
pytest --cov=src --cov-report=term-missing         # coverage
```

`pyproject.toml` already sets `testpaths = ["tests"]` and `pythonpath = ["src"]`. The suite uses temporary databases and does not touch `library.db`.

## Reproduce the review evidence

```bash
python dependency_check.py src        # package dependency edges, cycles, UI -> database calls
ruff check src --statistics           # code quality
bandit -r src                         # security
pip-audit -r requirements.txt         # dependency vulnerabilities
```

Outputs from the final runs are stored in `evidence/`.

| Check | Result on the final run |
|---|---|
| Tests | 148 passed |
| Coverage | 83% (887 statements, 154 missed) |
| bandit | 0 High, 20 Medium (B608, reviewed: constant table names only), 6 Low (B311, demo-data randomness) |
| pip-audit | No known vulnerabilities |
| ruff | 130 findings before fixes (see the report for the fixed subset and the re-run) |

## Known limitations

- `application` still imports `models.result.OperationResult` (shown by `dependency_check.py` as `application -> models`).
- `models` reaches `database` through a deferred import, so the `database <-> models` cycle no longer breaks at import time but remains a dependency.
- The UI still calls `database` directly 35 times; only checkout goes through a use case.
- The UI has no automated tests.
- Two baseline defects are characterized by tests but not changed: `Loan.is_overdue` on a database with no stored date, and the double header strip that drops the first book on initialisation.

## Documentation

- Final report: see the submitted PDF document.
- Architecture notes and the domain design are in the repository's documentation files.

## Acknowledgements and AI-use declaration

Architecture follows R. C. Martin, *Clean Architecture*. The group used Claude as an AI assistant for guidance, drafting and interpreting results; the group members ran, reviewed and verified all code and results.