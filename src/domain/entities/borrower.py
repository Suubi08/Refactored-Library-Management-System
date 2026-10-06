"""
Domain entity: Borrower.

DRAFT -- Marion owns the real domain-design pass on this entity (see
docs/domain-design.md section 3.3, which already identifies SSN/phone
validation as the next extraction candidate after Loan). This minimal
version exists only so CheckoutBook has something concrete to depend on
before we present on Thursday -- it intentionally carries NO validation logic, since
validation belongs at borrower *creation* time, not at checkout time,
and CheckoutBook never constructs a Borrower, only reads one.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Borrower:
    id: int
    ssn: str
    name: str
    address: str
    phone: str
