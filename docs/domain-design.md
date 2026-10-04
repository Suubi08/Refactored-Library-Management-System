# Domain Design — Library Management System

**Author:** Member 1 (Domain Architecture) · **Phase:** 3 — Isolate the Domain
**Status:** Design document. One entity (`Loan`) is already implemented and tested against this design — see §6. The others are design only this phase, per the scope boundary agreed for Phase 3.

---

## 1. The architectural decision

> **Domain entities must not import or directly depend on the `database` package, `sqlite3`, Pydantic, Textual, or any other infrastructure/framework concern.**

Concretely, for this codebase: a domain entity may depend on the Python standard library and nothing else. If an entity needs information that currently comes from `database` (today's date, a lookup, a config value), it **receives that information as a parameter**, supplied by whatever layer calls it. The entity never reaches out and asks for it.

This single rule is what Phase 1 identified as the core problem (`architecture_baseline.md` §3.3, §4 P1): `models/dtypes.py` imports `database`, creating a cycle, and breaking that cycle is Phase 3's entire purpose.

**Why a plain dataclass, not Pydantic, for the entity itself** (a choice worth defending explicitly, since it's a deviation from the existing codebase's pattern): Pydantic is a validation/serialization framework — a legitimate tool at the *boundary* (parsing a database row, validating external input), but pulling it into the innermost ring adds an outward-facing dependency the entity doesn't need. `Loan` (§6) is implemented as a plain `@dataclass`, importing nothing beyond `dataclasses`, `datetime`, and `typing`. The rest of this document follows the same standard for `Book`, `Borrower`, and `Fine`.

---

## 2. Current state — what `models/dtypes.py` actually holds today

```python
class Author(BaseModel):
    id: int = Field(alias='Author_id')
    name: str = Field(alias='Name')

class Book(BaseModel):
    isbn: str = Field(alias='Isbn')
    title: str = Field(alias='Title')

class BookAuthor(BaseModel):
    author_id: int = Field(alias='Author_id')
    isbn: str = Field(alias='Isbn')

class Borrower(BaseModel):
    id: int = Field(alias='Card_id')
    ssn: str = Field(alias='Ssn')
    name: str = Field(alias='Bname')
    address: str = Field(alias='Address')
    phone: str = Field(alias='Phone')

class Loan(BaseModel):
    id: int = Field(alias='Loan_id')
    isbn: str = Field(alias='Isbn')
    borrower_id: int = Field(alias='Card_id')
    title: str = Field(alias='Title')
    date_out: date = Field(alias='Date_out')
    due_date: date = Field(alias='Due_date')
    date_in: Optional[date] = Field(alias='Date_in')

    @property
    def is_overdue(self) -> bool:
        not_returned = (self.date_in is None)
        past_due = (db.get_current_date() > self.due_date)
        return not_returned and past_due

class Fine(BaseModel):
    loan_id: int = Field(alias='Loan_id')
    amt: int = Field(alias='Fine_amt')  # in cents
    paid: bool = Field(alias='Paid')
```

Every field alias (`alias='Card_id'`, `alias='Isbn'`) is shaped by the database column name, not by what the domain concept needs — a sign these types are currently *row-shaped*, not *domain-shaped*. Per Member 3's mapping work, the actual "row → object" conversion happens inline inside `database/query/*.py` (e.g. `book.py`'s `BookSearchResult(**dict(result))`), so these aliases exist purely to make that inline construction convenient — a persistence-layer convenience leaking into what's meant to be the domain layer.

---

## 3. Per-entity analysis

### 3.1 Loan — already extracted (see §6 for the verified code)

| Question | Answer |
|---|---|
| What makes it a domain entity? | A record of one book being borrowed by one borrower, with dates that determine its status. The library cares about this independent of how it's stored. |
| Fields belonging to the entity | `id`, `isbn`, `borrower_id`, `title`, `date_out`, `due_date`, `date_in` |
| Business-rule methods | `is_overdue(current_date)` — not returned AND current date is strictly past due date (the `>` vs `>=` quirk from `business_rules.md` is preserved exactly) |
| Dependency on database today | `is_overdue` called `db.get_current_date()` directly |
| What needed to change | Replace the internal database call with a parameter the caller supplies |

**Note:** `title` is carried on `Loan` today purely for display convenience (it's a join result, not an intrinsic property of a loan). It's kept on the extracted entity for now to avoid a larger change, but it's worth the team flagging as a smell: a `Loan` conceptually only needs `isbn` to identify which book; `title` belongs to `Book`. Not fixing this in Phase 3 — noting it for Phase 4+.

### 3.2 Book

| Question | Answer |
|---|---|
| What makes it a domain entity? | A physical/catalog item the library owns, identified by ISBN, independent of whether it's currently checked out. |
| Fields belonging to the entity | `isbn`, `title`. (`authors` is a relationship, not a field — see note below.) |
| Business-rule methods | None currently live on `Book` itself. **Availability** (`book_available_with_isbn()` in `database/query/book.py`) is really a question about the *current loan state* of a book, not an intrinsic property of the book — it depends on whether an active `Loan` exists for this ISBN. This is a rule that belongs at the boundary between `Book` and `Loan`, not purely inside `Book`. |
| Dependency on database today | None directly on the `Book` type itself — the dependency lives in the query functions that compute availability, not in the model. |
| What needed to change | Nothing about `Book`'s own fields. The open design question is **where availability should be decided**: an argument can be made either for a method on `Book` that takes "the list of currently active loans for this ISBN" as a parameter (mirroring the `Loan.is_overdue(current_date)` pattern), or for availability to be a concept that doesn't belong to `Book` or `Loan` alone, but to a small domain service that looks at both. Recommend the team decide this explicitly before Phase 4 — don't let it get decided implicitly by whoever happens to write the code first. |

**Note on `BookAuthor` and `Author`:** these model the many-to-many relationship between books and authors. They're not a business rule in themselves — they're a relationship/association, which is a persistence-layer concern (how the many-to-many is stored) more than a domain concept. Recommend `Book` eventually carries `authors: list[str]` directly (similar to how `BookSearchResult` already flattens this today) rather than the domain layer needing a separate `BookAuthor` entity at all.

### 3.3 Borrower

| Question | Answer |
|---|---|
| What makes it a domain entity? | A person registered with the library, identified by SSN, who can hold loans and owe fines. |
| Fields belonging to the entity | `id`, `ssn`, `name`, `address`, `phone` |
| Business-rule methods | The validation rules currently inside `create_borrower()` (`database/query/borrower.py`) are genuine domain rules, not persistence: SSN must be 9 numeric digits after hyphens are stripped; phone must be 10 numeric digits after formatting characters are stripped; all four fields are required. These read naturally as methods/validators *on* the entity (or a constructor that enforces them), not as code living inside a SQL-writing function. |
| Dependency on database today | None on the `Borrower` type itself. |
| What needed to change | The validation logic needs to move from `create_borrower()` into the entity (or a dedicated validation step the entity owns) — not yet done this phase, but this is the clearest, lowest-risk next candidate after `Loan`, since like `Loan.is_overdue`, it needs no external information at all (no date, no lookup — pure string validation). |

**Correction worth flagging to the team:** `architecture_baseline.md` (Phase 1, §2.4) repeated the README's claim that SSN uniqueness is enforced by a database constraint. I checked `database/schema.py` directly for this document and that's incorrect — the `Ssn` column is only `TEXT NOT NULL`, no `UNIQUE` constraint. Member 2's `business_rules.md` had this right already (duplicate-SSN rejection happens in application code, `borrower.py:114-120`). I'll fix the line in `architecture_baseline.md` separately; flagging here because it matters for this design: **uniqueness is not an invariant the database protects for us**, so if/when `Borrower` becomes a true domain entity, the team needs to decide whether uniqueness checking is a domain rule (the entity/constructor needs to know about existing borrowers — which pulls in a dependency) or stays an application-layer concern that happens *before* a `Borrower` is constructed. Recommend the latter — keep `Borrower` itself ignorant of "do any other borrowers exist."

### 3.4 Fine

| Question | Answer |
|---|---|
| What makes it a domain entity? | A monetary penalty tied to one loan, for returning a book late. |
| Fields belonging to the entity | `loan_id`, `amt` (cents), `paid` |
| Business-rule methods | Fine *calculation* (`business_rules.md`: 25 cents × days overdue) is a pure domain rule — given a loan's due date and a current date, compute the fine. This is currently inside `update_fines()` in `database/query/fine.py`, mixed with the SQL that writes the result. It's the same shape of problem as `Loan.is_overdue`: date math that doesn't need the database, it needs two dates. |
| Dependency on database today | `Fine` the type itself has none. The calculation function does, indirectly, via `get_current_date()`/the loan data it reads. |
| What needed to change | A `calculate_fine(days_overdue: int) -> int` (or `calculate_fine(due_date, current_date) -> int`) function/method, taking the same "receive what you need as a parameter" shape as `Loan.is_overdue`. This is a strong second candidate for extraction, and maps directly to the `domain/services/fine_calculator.py` file the team's target tree already anticipated. |

---

## 4. Summary table

| Entity | Fields clean already? | Has a database dependency to remove? | Business logic to extract | Recommended next after Loan |
|---|---|---|---|---|
| `Loan` | Yes | **Yes — done** (§6) | `is_overdue` | — (done) |
| `Book` | Yes | No direct dependency on the type itself | Availability (open design question, see §3.2) | Discuss as a team before coding |
| `Borrower` | Yes | No direct dependency on the type itself | SSN/phone/required-field validation | **Strong candidate — no external inputs needed, same shape as Loan** |
| `Fine` | Yes | No direct dependency on the type itself | Fine calculation (25¢/day) | **Strong candidate — same date-math shape as Loan** |

Recommendation for whoever picks up Phase 4 extraction work: do `Fine.calculate_fine` or `Borrower` validation next, in that order of simplicity — both take plain values as input (no lookups, no collections of other entities), exactly like `Loan.is_overdue` did. `Book` availability is harder because it inherently needs to know about `Loan`s, and deciding how to model that relationship cleanly is worth a short team discussion rather than a unilateral call.

---

## 5. What is explicitly *not* changing this phase

Consistent with the Phase 3 scope boundary the whole team agreed to:

- `models/dtypes.py` is untouched. The app still runs on it entirely.
- No UI, database, or application wiring changes.
- No entity beyond `Loan` gets actual code this phase — `Book`, `Borrower`, and `Fine` above are design only, for the team to review and agree on before anyone writes code.
- `src/domain/services/`, `src/application/`, `src/infrastructure/` are not created yet — there's no code to put in them.

---

## 6. Reference implementation — `Loan` (already built and verified)

```python
"""
Domain entity: Loan.
...
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Loan:
    id: int
    isbn: str
    borrower_id: int
    title: str
    date_out: date
    due_date: date
    date_in: Optional[date] = None

    def is_overdue(self, current_date: date) -> bool:
        not_returned = self.date_in is None
        past_due = current_date > self.due_date
        return not_returned and past_due

    @property
    def is_returned(self) -> bool:
        return self.date_in is not None
```

Verified: zero imports beyond the standard library; 6 unit tests in `tests/domain/test_loan_entity.py` pass in 0.02 seconds with no database involved at all (vs. ~163 seconds for the full characterization suite); the full suite of 123 characterization + 6 domain tests passes together, confirming nothing existing broke.

This is the template the team should follow for `Fine.calculate_fine` and `Borrower` validation when that work is picked up.
