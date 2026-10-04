# Data Mapping — How Database Rows Become Python Objects

**Studied:** `models/result.py` (`BookSearchResult`, `BorrowerSearchResult`, `FineSearchResult`, `OperationResult`), `database/query/book.py`, `borrower.py`, `fine.py` — plus `author.py` and `loan.py` for the flag and the worked example.

**Three words used below**
- **Row** — one line of data from the database (`sqlite3.Row`).
- **Entity** — an object that means something in library terms (a Loan, a Borrower) and knows nothing about the database or the screen.
- **Mapper** — a small function whose only job is to turn a row into an entity.

---

## 1. The short version

1. The code turns rows into objects in **8 places**, always with the same one-liner: `Model(**dict(row))`. There is **no mapper** — the models themselves know the database column names (`Card_id`, `Bname`, …).
2. Most of what the screens receive is a **display shape**, not an entity. These shapes carry display logic: the words "Available"/"Unavailable", `$2.50` formatting, authors joined with `&`.
3. **Only `Loan` and `Borrower` are ever built from a row.** `Book`, `Fine` and `BookAuthor` exist in `models/dtypes.py` but are never used.
4. `get_author_by_id()` returns a raw row instead of an `Author` (see section 4).

---

## 2. Where each row becomes an object today

| Entity | File → function (line) | What it becomes |
|---|---|---|
| **Book** | `book.py` → `search_books` (77) | `BookSearchResult` |
| **Borrower** | `borrower.py` → `_get_borrower` (83) | `Borrower` |
| **Borrower** (search list) | `borrower.py` → `search_borrowers` (55) | `BorrowerSearchResult` |
| **Fine** | `fine.py` → `get_all_fines` (39) and `get_fines_by_borrower_id` (66) | `FineSearchResult` |
| **Loan** *(worked example)* | `loan.py` → `search_loans` (63), `get_loans_by_borrower_id` (93), `get_loans_by_isbn` (120) | `Loan` |
| **Author** | **nowhere.** `author.py` → `get_author_by_id` (19) returns the raw row | — |

`get_book_by_isbn` (`book.py:79`) does no mapping of its own. It calls `search_books` and takes the first result.

---

## 3. Real entity, or display shape?

### 3a. The four types in `models/result.py`

| Type (line) | Built by | Verdict | What is riding along with the data |
|---|---|---|---|
| `BookSearchResult` (15) | `book.py` → `search_books` | **Display shape** | `status_display` (36-38) and `serialize_status` (44-46) turn true/false into "Available"/"Unavailable". `serialize_authors` (48-50) joins names with " & ". `process_authors` (22-34) also reshapes the database text "A, B" into a list. |
| `BorrowerSearchResult` (52) | `borrower.py` → `search_borrowers` | **Display shape** | `serialize_fines` (59-61) and `amt_dollars` (63-65) turn cents into "$123.45", and into **blank when the amount is 0**. |
| `FineSearchResult` (67) | `fine.py` → `get_all_fines`, `get_fines_by_borrower_id` | **Display shape** | `serialize_amt` (77-79) and `amt_dollars` (81-83) do the same dollar formatting. It is also used for **business decisions**: `pay_fines` reads its `date_in` and `loan_id`. |
| `OperationResult` (7) | Created in 18 places in `loan.py`, `borrower.py`, `fine.py` | **Neither** | It only carries "did it work?" plus a message for the screen. Its `data` field is never used anywhere. |

### 3b. The entity types in `models/dtypes.py`

| Type (line) | Verdict | Why |
|---|---|---|
| `Borrower` (22) | **Entity candidate** | Right fields, but named after database columns (`alias='Card_id'`, `'Bname'`). |
| `Loan` (29) | **Entity candidate** | Same, and `is_overdue` calls the database to get today's date. |
| `Book`, `Fine`, `BookAuthor` | **Unused** | Defined but never created. The screens only ever see the display shapes above. |

**Display logic hidden in the data, in plain words:**
- The data class decides the **words** ("Available"), the **money format** ("$2.50") and the **separator** (" & ").
- The screen builds its table from `model_dump()` (`ui/screens/search.py:106`), so the **order of fields in the class is the order of columns on screen**. Reordering a field would silently break the table.

**Business rules hidden in the database queries:**
- "Available" = no active loan (written 3 times in `book.py`: lines 25-28, 66/68, and 90-104).
- "Active loan count" and "unpaid fines" are worked out inside the SQL in `borrower.py` (lines 26-38).

---

## 4. Flag for the team: `get_author_by_id()`

`database/query/author.py`:

```python
def get_author_by_id(author_id: str) -> Optional[Author]:    # promises an Author
    ...
    return query.get_one_or_none(sql, [author_id])           # returns a raw sqlite3.Row
```

| What happens | Result |
|---|---|
| Return type | A raw row, **not** an `Author` |
| `result.name` | **Crashes** (`AttributeError`) |
| `result["Name"]` | Works, because it is a row |
| Who calls it | **Nobody** in `src/` — it is dead code |

**Why it matters:** every other lookup wraps its row in a model. This one skipped that step, and nothing noticed, because Python doesn't enforce return types and no single place is responsible for the conversion. That is exactly what a mapper function would fix.

Already recorded in `tests/characterization/test_database_setup.py::test_get_author_by_id_is_unused_dead_code_with_a_wrong_return_type`.

---

## 5. The target: row → mapper → entity

```
Today:   row ─────────────────────────────► Pydantic model shaped like the row
                                            (model knows column names)

Target:  row ──► mapper function ──► entity
                 (infrastructure)    (plain Python, no database,
                                      no Pydantic, no screen)
```

**Rules for the target**
1. The entity never sees a row or a column name.
2. One mapper per entity, in one place, outside the domain.
3. The mapper converts the values (text → date, 0/1 → true/false).
4. Display formatting ("$2.50", "Available") moves to the screen or a presenter, **not** the mapper and **not** the entity.
5. Display shapes stay separate from entities.

### Worked example: Loan

| Database column | Entity field | Conversion |
|---|---|---|
| `Loan_id` | `id` | none |
| `Isbn` | `isbn` | none |
| `Card_id` | `borrower_id` | none |
| `Title` | `title` | none |
| `Date_out` | `date_out` | text → date |
| `Due_date` | `due_date` | text → date |
| `Date_in` | `date_in` | text → date, or empty |

```python
# illustration only — NOT added to the repo in Phase 3
def loan_from_row(row):
    return Loan(
        id=row["Loan_id"],
        isbn=row["Isbn"],
        borrower_id=row["Card_id"],
        title=row["Title"],
        date_out=date.fromisoformat(row["Date_out"]),
        due_date=date.fromisoformat(row["Due_date"]),
        date_in=date.fromisoformat(row["Date_in"]) if row["Date_in"] else None,
    )
```

I tested this against real database rows and it gives **the same values as today's code**.

> **Next gap to fill:** `domain/entities/loan.py` has **no mapper yet**. Until `loan_from_row` exists, no code can produce the new `Loan` entity from the database.

---

## 6. What the team should do next

1. Write `loan_from_row`, then mappers for `Borrower`, `Fine` and `Book`.
2. Decide on `get_author_by_id`: delete it, or fix it through the new mapper.
3. Move the display formatting out of `models/result.py`.
4. Add tests for the display strings first. No current test checks `status_display`, `amt_dollars` or `model_dump()`, so a change there would not be caught.

*Note: the code studied had no `src/domain/` folder, so the Loan entity follows its design in `docs/domain-design.md` section 6. Line numbers are from that code and may shift after teammates' changes.*