from database.names import BORROWERS_TABLE_NAME
from models import OperationResult

from . import query


def create_borrower(name: str, ssn: str, address: str, phone: str) -> OperationResult:
    required_fields = {
        "Name": name,
        "SSN": ssn,
        "Address": address,
        "Phone": phone,
    }
    missing_fields = [label for label, value in required_fields.items() if not value.strip()]

    if missing_fields:
        return OperationResult(
            status=False,
            message=f"Missing field(s): {', '.join(missing_fields)}",
        )

    normalized_ssn = "".join(character for character in ssn if character.isdigit())
    normalized_phone = "".join(character for character in phone if character.isdigit())

    if len(normalized_ssn) != 9:
        return OperationResult(status=False, message="SSN must contain exactly 9 digits.")

    if len(normalized_phone) != 10:
        return OperationResult(status=False, message="Phone must contain exactly 10 digits.")

    sql = f"""
        INSERT INTO {BORROWERS_TABLE_NAME} (Ssn, Bname, Address, Phone)
        VALUES (?, ?, ?, ?)
    """
    success = query.try_execute_one(
        sql,
        [normalized_ssn, name.strip(), address.strip(), normalized_phone],
    )

    if not success:
        return OperationResult(
            status=False,
            message="Could not create borrower. SSN may already be registered.",
        )

    return OperationResult(status=True, message="Borrower created successfully.")