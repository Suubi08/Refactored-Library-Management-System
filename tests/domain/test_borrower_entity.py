from domain.entities.borrower import Borrower


def test_valid_formatted_details_return_no_errors():
    borrower = Borrower(
        id=1,
        ssn="123-456-789",
        name="Ada",
        address="1 Main Street",
        phone="(123) 456-7890",
    )

    assert borrower.validate() == []


def test_blank_details_return_missing_field_errors():
    borrower = Borrower(
        id=1,
        ssn="",
        name="",
        address="",
        phone="",
    )

    assert borrower.validate() == ["Name", "SSN", "Address", "Phone"]


def test_invalid_ssn_returns_ssn_error():
    borrower = Borrower(
        id=1,
        ssn="123-45",
        name="Ada",
        address="1 Main Street",
        phone="(123) 456-7890",
    )

    assert borrower.validate() == ["Not a valid SSN."]


def test_invalid_phone_returns_phone_error():
    borrower = Borrower(
        id=1,
        ssn="123-456-789",
        name="Ada",
        address="1 Main Street",
        phone="123",
    )

    assert borrower.validate() == ["Not a valid Phone Number."]
