 ## Phase 3 Regression Report

## 1. Before / After

| | Tests passed | Tests failed | Coverage | Statements | Missed |
|---|---|---|---|---|---|
| Phase 2 baseline | 123 | 0 | 78% | n/a | n/a |
| Before Phase 3 (measured) | 123 | 0 | 78% | 767 | 165 |
| After Phase 3 | ___ | ___ | ___% | ___ | ___ |
| **Change** | +___ | ___ | ___ points | +___ | ___ |

## 2. Environment

| Item | Value |
|---|---|
| Python | 3.12.10 |
| pytest | 9.1.1 |
| pytest-cov | 7.1.0 |
| Platform | Windows, run with `uv run` |
| Tests collected | 123 (all under tests/characterization/) |
| Warnings | 1 (existing before Phase 3): Pydantic deprecation in `src/models/result.py:7`, class-based `config` should become `ConfigDict`. Does not affect results. |
| Run time (start of phase) | 287 s with `-v`, 144 s with coverage |

## 3. Characterization tests

| Test file | Passed at start | Passed at end |
|---|---|---|
| test_books.py | Yes | ___ |
| test_borrowers.py | Yes | ___ |
| test_database_setup.py | Yes | ___ |
| test_fines.py | Yes | ___ |
| test_known_issues.py | Yes | ___ |
| test_loans.py | Yes | ___ |
| test_workflows.py | Yes | ___ |
| **Total** | **123 of 123** | **___ of 123** |

## 4. Coverage at start of Phase 3

| File | Stmts | Miss | Cover | Missing lines |
|---|---|---|---|---|
| src/app.py | 19 | 19 | 0% | 1-40 |
| src/database/\_\_init\_\_.py | 9 | 0 | 100% | |
| src/database/config.py | 5 | 0 | 100% | |
| src/database/dtypes.py | 2 | 0 | 100% | |
| src/database/import_data.py | 104 | 45 | 57% | 14, 40-41, 83-84, 95-174 |
| src/database/initialize.py | 69 | 5 | 93% | 24, 29, 76-79 |
| src/database/names.py | 7 | 0 | 100% | |
| src/database/query/author.py | 7 | 0 | 100% | |
| src/database/query/book.py | 43 | 2 | 95% | 88, 102 |
| src/database/query/borrower.py | 48 | 2 | 96% | 20, 53 |
| src/database/query/conf.py | 21 | 0 | 100% | |
| src/database/query/fine.py | 82 | 3 | 96% | 39, 93, 175 |
| src/database/query/loan.py | 90 | 1 | 99% | 123 |
| src/database/query/metadata.py | 13 | 0 | 100% | |
| src/database/query/query.py | 60 | 14 | 77% | 9, 18-21, 29, 38-41, 74-77 |
| src/database/schema.py | 2 | 0 | 100% | |
| src/logger.py | 32 | 15 | 53% | 7, 10, 13-14, 17-18, 21-22, 25, 28, 35, 38-41, 44 |
| src/main.py | 51 | 51 | 0% | 3-72 |
| src/models/\_\_init\_\_.py | 2 | 0 | 100% | |
| src/models/dtypes.py | 37 | 0 | 100% | |
| src/models/result.py | 64 | 8 | 88% | 38, 42, 46, 50, 61, 65, 79, 83 |
| **TOTAL** | **767** | **165** | **78%** | |

`src/app.py` and `src/main.py` are entry points not exercised by the
characterization suite. Together they account for 70 of the 165 missed statements.

## 5. Evidence

| File | Contents | Taken |
|---|---|---|
| docs/phase3-before-pytest.txt | Full `pytest -v` output | Start of Phase 3 |
| docs/phase3-before-coverage.txt | Coverage report with missing lines | Start of Phase 3 |

## 6. Commands used

| Purpose | Command |
|---|---|
| Full suite | `uv run pytest -v` |
| Suite with coverage | `uv run pytest --cov=src --cov-report=term-missing` |
| Domain tests only | `uv run pytest tests/domain -v` |
| Check characterization tests unchanged | `git diff main -- tests/characterization/` |

Tests passed Coverage
Before Phase 3 123 78%
After Phase 3 (pending) no files added



			
