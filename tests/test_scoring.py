from datetime import date, datetime
from decimal import Decimal

import pytest

from logic import scoring
from logic.scoring import InvalidRecordError

TODAY = date(2025, 5, 8)


def test_weights_add_up_to_one():
    assert sum(scoring.WEIGHTS.values()) == pytest.approx(1.0)


class TestPaymentScore:
    def test_share_of_on_time_payments(self):
        assert scoring.payment_score(18, 20) == 90.0
        assert scoring.payment_score(9, 12) == 75.0

    def test_accepts_decimal_from_mysql(self):
        assert scoring.payment_score(Decimal("9"), Decimal("12")) == 75.0

    def test_no_payments_scores_zero(self):
        assert scoring.payment_score(0, 0) == 0.0

    def test_rounds_to_two_decimals(self):
        assert scoring.payment_score(1, 3) == 33.33

    @pytest.mark.parametrize(
        ("on_time", "total"),
        [(21, 20), (-1, 20), (1, -1), (None, 20), ("x", 20), (True, 2)],
    )
    def test_rejects_impossible_values(self, on_time, total):
        with pytest.raises(InvalidRecordError):
            scoring.payment_score(on_time, total)

    def test_rejects_nan(self):
        with pytest.raises(InvalidRecordError):
            scoring.payment_score(float("nan"), 20)


class TestDebtScore:
    def test_is_100_minus_utilisation(self):
        assert scoring.debt_score(3000, 10000) == 70.0
        assert scoring.debt_score(Decimal("7000.00"), Decimal("10000.00")) == 30.0

    def test_unused_credit_scores_100(self):
        assert scoring.debt_score(0, 5000) == 100.0

    def test_over_the_limit_scores_zero_not_negative(self):
        assert scoring.debt_score(12000, 10000) == 0.0

    def test_zero_limit_scores_zero(self):
        assert scoring.debt_score(0, 0) == 0.0

    def test_rejects_negative_amounts(self):
        with pytest.raises(InvalidRecordError):
            scoring.debt_score(-1, 100)
        with pytest.raises(InvalidRecordError):
            scoring.debt_score(1, -100)


class TestHistoryScore:
    def test_scales_age_to_ten_years(self):
        # 5 * 365 days is exactly half of MAX_HISTORY_YEARS.
        assert scoring.history_score(date(2020, 5, 9), TODAY) == 50.0

    def test_capped_at_100(self):
        assert scoring.history_score(date(1990, 1, 1), TODAY) == 100.0

    def test_account_opened_today_scores_zero(self):
        assert scoring.history_score(TODAY, TODAY) == 0.0

    def test_accepts_datetime(self):
        assert scoring.history_score(datetime(2020, 5, 9, 13, 30), TODAY) == 50.0

    def test_rejects_future_date(self):
        with pytest.raises(InvalidRecordError, match="future"):
            scoring.history_score(date(2030, 1, 1), TODAY)

    def test_rejects_non_date(self):
        with pytest.raises(InvalidRecordError):
            scoring.history_score("2020-01-01", TODAY)


class TestMixScore:
    def test_share_of_credit_types(self):
        assert scoring.mix_score(2, 4) == 50.0
        assert scoring.mix_score(3, 4) == 75.0

    def test_zero_types_available_scores_zero(self):
        assert scoring.mix_score(0, 0) == 0.0

    def test_rejects_more_types_than_exist(self):
        with pytest.raises(InvalidRecordError):
            scoring.mix_score(5, 4)


class TestCombine:
    def test_all_zero_is_minimum(self):
        components = dict.fromkeys(scoring.WEIGHTS, 0.0)
        assert scoring.combine(components) == scoring.MIN_SCORE == 300

    def test_all_hundred_is_maximum(self):
        components = dict.fromkeys(scoring.WEIGHTS, 100.0)
        assert scoring.combine(components) == scoring.MAX_SCORE == 850

    def test_weighted_example(self):
        # 0.35*90 + 0.30*70 + 0.15*84.3 + 0.20*50 = 75.145 -> 300 + 0.75145*550
        components = {"payment": 90.0, "debt": 70.0, "history": 84.3, "mix": 50.0}
        assert scoring.combine(components) == 713.3

    def test_rejects_missing_or_unknown_components(self):
        with pytest.raises(ValueError):
            scoring.combine({"payment": 50.0})
        with pytest.raises(ValueError):
            scoring.combine({**dict.fromkeys(scoring.WEIGHTS, 1.0), "extra": 1.0})

    def test_rejects_out_of_range_component(self):
        components = {**dict.fromkeys(scoring.WEIGHTS, 50.0), "debt": 120.0}
        with pytest.raises(ValueError):
            scoring.combine(components)


@pytest.mark.parametrize(
    ("score", "band"),
    [
        (300, "Poor"),
        (579.99, "Poor"),
        (580, "Fair"),
        (669.99, "Fair"),
        (670, "Good"),
        (739.99, "Good"),
        (740, "Very Good"),
        (799.99, "Very Good"),
        (800, "Excellent"),
        (850, "Excellent"),
    ],
)
def test_score_band_boundaries(score, band):
    assert scoring.score_band(score) == band
