from typing import Optional

from models import Author
from database.names import (
    AUTHORS_TABLE_NAME
)

from . import query

def get_author_by_id(author_id: str) -> Optional[Author]:
    sql = f"""
    SELECT
        Author_id,
        Name
    FROM {AUTHORS_TABLE_NAME}
    WHERE Author_id = ?
    """

    return query.get_one_or_none(sql, [author_id])
