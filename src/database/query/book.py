from typing import Optional

from database.names import (
    BOOKS_TABLE_NAME,
    BOOK_AUTHORS_TABLE_NAME,
    BOOK_LOANS_TABLE_NAME,
    AUTHORS_TABLE_NAME,
    BORROWERS_TABLE_NAME
)

from models import BookSearchResult

from . import query

def search_books(search_term: str, filters: Optional[dict] = None) -> list[BookSearchResult]:
    if not search_term:
        return []

    sql = f"""
    SELECT
        b.Isbn as Isbn,
        b.Title as Title,
        GROUP_CONCAT(a.Name, ', ') as Author_names,
        GROUP_CONCAT(a.Author_id, ', ') as Author_ids,
        CASE
            WHEN l.Isbn IS NOT NULL THEN 0
            ELSE 1
        END as Status,
        l.Card_id as Card_id
    FROM {BOOKS_TABLE_NAME} b
    LEFT JOIN {BOOK_AUTHORS_TABLE_NAME} ba ON ba.Isbn = b.Isbn
    LEFT JOIN {AUTHORS_TABLE_NAME} a ON a.Author_id = ba.Author_id
    LEFT JOIN {BOOK_LOANS_TABLE_NAME} l ON b.Isbn = l.Isbn AND l.Date_in IS NULL
    LEFT JOIN {BORROWERS_TABLE_NAME} br ON br.Card_id = l.Card_id
    GROUP BY b.Isbn
    HAVING ("""
    
    conditions = []
    params = []
    
    if filters and 'columns' in filters:
        # by columns
        columns = {
            'ISBN': 'b.Isbn',
            'Title': 'b.Title',
            'Authors': 'Author_names'
        }
        
        for column_name, is_enabled in filters['columns']:
            if is_enabled and column_name in columns:
                conditions.append(f"{columns[column_name]} LIKE ? COLLATE NOCASE")
                params.append(f"%{search_term}%")
    else:
        conditions = [
            "b.Isbn LIKE ? COLLATE NOCASE",
            "b.Title LIKE ? COLLATE NOCASE",
            "Author_names LIKE ? COLLATE NOCASE"
        ]
        params = [f"%{search_term}%" for _ in range(3)]
    
    sql += " OR ".join(conditions) + ")"
    
    if filters and 'availability' in filters:
        availability = filters['availability']
        if availability == 'Available':
            sql += " AND (CASE WHEN l.Isbn IS NOT NULL THEN 0 ELSE 1 END) = 1"
        elif availability == 'Unavailable':
            sql += " AND (CASE WHEN l.Isbn IS NOT NULL THEN 0 ELSE 1 END) = 0"
        else:
            pass # no filter
    
    results = query.get_all_or_none(sql, params)

    if not results:
        return []

    return [BookSearchResult(**dict(result)) for result in results]

def get_book_by_isbn(isbn: str) -> Optional[BookSearchResult]:
    books = search_books(isbn)

    if not books:
        return None

    return books[0]

def book_exists_with_isbn(isbn: str) -> bool:
    return get_book_by_isbn(isbn) is not None

def book_available_with_isbn(isbn: str) -> bool:
    sql = f"""
    SELECT
        COUNT(*) as n_checkouts
    FROM {BOOK_LOANS_TABLE_NAME}
    WHERE Isbn = ?
      AND Date_in IS NULL
    """

    result = query.get_one_or_none(sql, [isbn])

    if result is None:
        return True

    return result[0] == 0
