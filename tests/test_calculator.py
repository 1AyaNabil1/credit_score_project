from datetime import date

import pytest

from db.connection import DatabaseError
from logic import calculator
from logic.scoring import InvalidRecordError

# The README screenshot shows "Ahlam Mohammed -> Score: 557.27 - Poor". These
# are her rows from utils/test_data.sql, scored on the day it was taken.
AHLAM = {
    "payments": (9, 12),
    "usage": (7000.0, 10000.0),
    "oldest_account": date(2021, 1, 1),
    "mix": (1, 4),
}
SCREENSHOT_DAY = date(2025, 5, 8)


@pytest.fixture
def records(monkeypatch):
    """Replace the four DB fetchers with an editable in-memory record."""
    data = dict(AHLAM)
    monkeypatch.setattr(calculator, "fetch_payment_totals", lambda _: data["payments"])
    monkeypatch.setattr(calculator, "fetch_credit_usage", lambda _: data["usage"])
    monkeypatch.setattr(
        calculator, "fetch_oldest_account_date", lambda _: data["oldest_account"]
    )
    monkeypatch.setattr(calculator, "fetch_credit_mix", lambda _: data["mix"])
    return data


def test_matches_the_readme_screenshot(records):
    result = calculator.score_user(2, today=SCREENSHOT_DAY)
    assert result.iscore == 557.27
    assert result.band == "Poor"
    assert result.components == {
        "payment": 75.0,
        "debt": 30.0,
        "history": 43.51,
        "mix": 25.0,
    }
    assert result.missing == ()


def test_missing_data_counts_as_zero_and_is_reported(records):
    records["usage"] = None
    records["mix"] = None
    result = calculator.score_user(2, today=SCREENSHOT_DAY)
    assert result.missing == ("debt", "mix")
    assert result.components["debt"] == 0.0
    assert result.components["mix"] == 0.0
    assert result.iscore == pytest.approx(
        300 + (0.35 * 75 + 0.15 * 43.51) * 5.5, abs=0.01
    )


def test_user_with_no_data_gets_minimum_score(records):
    for key in records:
        records[key] = None
    result = calculator.score_user(9, today=SCREENSHOT_DAY)
    assert result.iscore == 300.0
    assert result.missing == ("payment", "debt", "history", "mix")


def test_invalid_record_names_the_user(records):
    records["payments"] = (13, 12)
    with pytest.raises(InvalidRecordError, match="user 2.*on_time_payments"):
        calculator.score_user(2, today=SCREENSHOT_DAY)


def test_database_errors_are_not_turned_into_a_score(monkeypatch, records):
    def down(_user_id):
        raise DatabaseError("Could not connect")

    monkeypatch.setattr(calculator, "fetch_credit_usage", down)
    with pytest.raises(DatabaseError):
        calculator.score_user(2, today=SCREENSHOT_DAY)


def test_calculate_iscore_returns_just_the_number(records, monkeypatch):
    monkeypatch.setattr(
        calculator,
        "score_user",
        lambda user_id: calculator.ScoreBreakdown(user_id, 612.5),
    )
    assert calculator.calculate_iScore(2) == 612.5
