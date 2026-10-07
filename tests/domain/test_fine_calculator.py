from domain.services.fine_calculator import calculate_fine


def test_calculates_fine_for_overdue_days():
    assert calculate_fine(4) == 100


def test_zero_overdue_days_has_no_fine():
    assert calculate_fine(0) == 0
