"""
Domain entity: Book.

DRAFT -- Marion owns the real domain-design pass on this entity (see
docs/domain-design.md section 3.2, which already flags the open question
of where "is this book available" should live). This minimal version
exists only so CheckoutBook (application/use_cases/checkout_book.py) has
something concrete to depend on before we present Thursday. It deliberately does
NOT decide the availability question -- that's why CheckoutBook asks the
LoanRepository whether the book is available, not the Book entity
itself. I can Replace/extend this once Marion's domain design for Book is
finalized; nothing about the use case's logic should need to change when
that happens, only this file.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Book:
    isbn: str
    title: str
