import pytest


@pytest.mark.parametrize(
	("name", "ssn", "address", "phone", "missing_field"),
	[
		("", "123456789", "1 Test St", "1234567890", "Name"),
		("Test Borrower", "", "1 Test St", "1234567890", "SSN"),
		("Test Borrower", "123456789", "", "1234567890", "Address"),
		("Test Borrower", "123456789", "1 Test St", "", "Phone"),
	],
)
def test_create_borrower_rejects_missing_required_fields(
	test_db, name, ssn, address, phone, missing_field
):
	result = test_db.create_borrower(name, ssn, address, phone)

	assert result.status is False
	assert result.message == f"Missing field(s): {missing_field}"


@pytest.mark.parametrize("ssn", ["123-45-6789", "123456789"])
def test_create_borrower_accepts_nine_digit_ssn_with_or_without_hyphens(
	test_db, ssn
):
	result = test_db.create_borrower(
		"Test Borrower", ssn, "1 Test St", "1234567890"
	)

	assert result.status is True
	assert result.message == "Borrower created successfully."
	borrower = test_db.get_borrower_by_ssn("123456789")
	assert borrower is not None
	assert borrower.ssn == "123456789"


@pytest.mark.parametrize("ssn", ["12345678", "1234567890", "12345abcd"])
def test_create_borrower_rejects_invalid_ssn(test_db, ssn):
	result = test_db.create_borrower(
		"Test Borrower", ssn, "1 Test St", "1234567890"
	)

	assert result.status is False
	assert result.message == "Not a valid SSN."


@pytest.mark.parametrize("phone", ["(123) 456-7890", "1234567890"])
def test_create_borrower_strips_phone_formatting(test_db, phone):
	result = test_db.create_borrower(
		"Test Borrower", "987654321", "1 Test St", phone
	)

	assert result.status is True
	assert result.message == "Borrower created successfully."
	borrower = test_db.get_borrower_by_ssn("987654321")
	assert borrower is not None
	assert borrower.phone == "1234567890"


@pytest.mark.parametrize("phone", ["123456789", "12345678901", "12345abcde"])
def test_create_borrower_rejects_invalid_phone(test_db, phone):
	result = test_db.create_borrower(
		"Test Borrower", "987654321", "1 Test St", phone
	)

	assert result.status is False
	assert result.message == "Not a valid Phone Number."


def test_create_borrower_rejects_duplicate_ssn_in_application(test_db):
	first = test_db.create_borrower(
		"First Borrower", "987654321", "1 Test St", "1234567890"
	)
	second = test_db.create_borrower(
		"Second Borrower", "987654321", "2 Test St", "0987654321"
	)

	assert first.status is True
	assert first.message == "Borrower created successfully."
	assert second.status is False
	assert second.message == "Borrower with this SSN already exists."
