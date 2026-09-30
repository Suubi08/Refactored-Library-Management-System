from database.names import (
    BOOKS_TABLE_NAME,
    BOOK_AUTHORS_TABLE_NAME,
    AUTHORS_TABLE_NAME,
    BORROWERS_TABLE_NAME,
    BOOK_LOANS_TABLE_NAME,
    FINES_TABLE_NAME,
    METADATA_TABLE_NAME,
)

queries = {

    'books': f"""
        CREATE TABLE {BOOKS_TABLE_NAME} (
            Isbn TEXT NOT NULL,
            Title TEXT NOT NULL,

            PRIMARY KEY (Isbn)
        );
    """,

    'book_authors': f"""
        CREATE TABLE {BOOK_AUTHORS_TABLE_NAME} (
            Author_id TEXT NOT NULL,
            Isbn TEXT NOT NULL,

            PRIMARY KEY(Author_id, Isbn),

            FOREIGN KEY(Author_id) REFERENCES AUTHORS(Author_id),
            FOREIGN KEY(Isbn) REFERENCES BOOK(Isbn)
        );
    """,

    'authors': f"""
        CREATE TABLE {AUTHORS_TABLE_NAME} (
            Author_id TEXT NOT NULL,
            Name TEXT NOT NULL,

            PRIMARY KEY (Author_id)
        );
    """,

    'borrowers': f"""
        CREATE TABLE {BORROWERS_TABLE_NAME} (
            Card_id INTEGER PRIMARY KEY AUTOINCREMENT,
            Ssn TEXT NOT NULL,
            Bname TEXT NOT NULL,
            Address TEXT NOT NULL,
            Phone TEXT NOT NULL
        );
    """,

    'loans': f"""
        CREATE TABLE {BOOK_LOANS_TABLE_NAME} (
            Loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            Isbn TEXT NOT NULL,
            Card_id INTEGER NOT NULL,
            Date_out TEXT NOT NULL,
            Due_date TEXT NOT NULL,
            Date_in TEXT,

            FOREIGN KEY(Isbn) REFERENCES BOOK(Isbn),
            FOREIGN KEY(Card_id) REFERENCES BORROWER(Card_id)
        );
    """,

    'fines': f"""
        CREATE TABLE {FINES_TABLE_NAME} (
            Loan_id INTEGER NOT NULL,
            Fine_amt INTEGER NOT NULL,
            Paid INTEGER NOT NULL,

            PRIMARY KEY (Loan_id),

            FOREIGN KEY(Loan_id) REFERENCES BOOK_LOANS(Loan_id)
        );
    """,

    'metadata': f"""
        CREATE TABLE IF NOT EXISTS {METADATA_TABLE_NAME} (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """
}
