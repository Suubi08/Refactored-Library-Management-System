from pathlib import Path

db_name: str = "library.db"

def set_db_name(value: str):
    global db_name

    db_path_root = Path(__file__).parent.parent

    db_name = str(db_path_root / value)