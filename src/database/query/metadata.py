from typing import Optional

from database.names import METADATA_TABLE_NAME

from . import query

def get_value(key: str) -> Optional[str]:
    sql = f"""
        SELECT value FROM {METADATA_TABLE_NAME}
        WHERE key = ?
    """

    result = query.get_one_or_none(sql, [key])

    if not result:
        return None

    return str(result[0])

def set_value(key: str, value: str) -> bool:
    sql = f"""
    INSERT OR REPLACE INTO {METADATA_TABLE_NAME} (
        key,
        value
    ) VALUES (
        ?,
        ?
    )
    """

    params = [key, value]

    return query.try_execute_one(sql, params)
