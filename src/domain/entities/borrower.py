
from dataclasses import dataclass


@dataclass(frozen=True)
class Borrower:
    id: int
    ssn: str
    name: str
    address: str
    phone: str

    def validate(self) -> list[str]:
        errors = []

        # Add the required-field checks here.
        required_fields = {
            "Name": self.name,
            "SSN": self.ssn,
            "Address": self.address,
            "Phone": self.phone,
        }

        for label, value in required_fields.items():
            if not value.strip():
                errors.append(label)
        # Then check the normalized SSN and phone.
        if self.ssn.strip():
            normalized_ssn = self.ssn.replace("-", "")
            if not normalized_ssn.isnumeric() or len(normalized_ssn) != 9:
                errors.append("Not a valid SSN.")

        if self.phone.strip():
            normalized_phone = (
                self.phone
                .replace("(", "")
                .replace(")", "")
                .replace("-", "")
                .replace(" ", "")
            )
            if not normalized_phone.isnumeric() or len(normalized_phone) != 10:
                errors.append("Not a valid Phone Number.")

        return errors
