from application.use_cases.checkout_book import CheckoutBook
from infrastructure.sqlite.book_repository import SqliteBookRepository
from infrastructure.sqlite.borrower_repository import SqliteBorrowerRepository
from infrastructure.sqlite.loan_repository import SqliteLoanRepository
from infrastructure.sqlite.fine_repository import SqliteFineRepository


def build_checkout_book() -> CheckoutBook:
    return CheckoutBook(
        book_repository=SqliteBookRepository(),
        borrower_repository=SqliteBorrowerRepository(),
        loan_repository=SqliteLoanRepository(),
        fine_repository=SqliteFineRepository(),
        )
