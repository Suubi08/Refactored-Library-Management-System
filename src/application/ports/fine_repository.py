"""
Port: FineRepository. See book_repository.py for the general explanation
of why this is a Protocol, not a concrete class.

Only the one method CheckoutBook actually needs is declared here. Resist
the urge to pre-declare pay_fines()/get_total_fines() etc. on this
interface before a use case actually needs them -- an interface should
grow driven by real callers, not be designed speculatively ahead of use.
"""
from typing import Protocol


class FineRepository(Protocol):
    def has_unpaid_fines(self, borrower_id: int) -> bool:
        """True if this borrower has any unpaid fine on record."""
        ...
