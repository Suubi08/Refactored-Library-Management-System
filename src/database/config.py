from pathlib import Path

<<<<<<< HEAD
db_name: str = "library.db"
=======
db_name: str = ""
>>>>>>> 4ceeed32beff40fcf2cf85bdfea9058bac11d8e5

def set_db_name(value: str):
    global db_name

    db_path_root = Path(__file__).parent.parent

<<<<<<< HEAD
    db_name = str(db_path_root / value)
=======
    db_name = str(db_path_root / value)
>>>>>>> 4ceeed32beff40fcf2cf85bdfea9058bac11d8e5
