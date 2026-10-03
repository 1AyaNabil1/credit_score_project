"""Pure iScore formulas: no database, no GUI, no clock.

Each factor is turned into a component score from 0 to 100. The iScore is the
weighted sum of the components mapped linearly onto the 300-850 range, so a
user with every component at 0 gets 300 and one with every component at 100
gets 850.

Values that cannot be right (negative counts, more on-time payments than
payments, an account opened in the future, ...) raise InvalidRecordError
instead of being scored silently.
"""

import math
from collections.abc import Mapping
from datetime import date, datetime

MIN_SCORE = 300
MAX_SCORE = 850

# Share of each component in the final score. Must add up to 1.
WEIGHTS = {
    "payment": 0.35,  # on-time payments / total payments
    "debt": 0.30,  # 1 - credit utilisation (used credit / credit limit)
    "history": 0.15,  # age of the oldest account, capped at MAX_HISTORY_YEARS
    "mix": 0.20,  # credit types used / credit types available
}

MAX_HISTORY_YEARS = 10
DAYS_PER_YEAR = 365

# Upper bounds (exclusive) of each band; anything at or above 800 is Excellent.
SCORE_BANDS = (
    (580, "Poor"),
    (670, "Fair"),
    (740, "Good"),
    (800, "Very Good"),
)
TOP_BAND = "Excellent"


class InvalidRecordError(ValueError):
    """A stored record holds values that cannot be scored."""


def _non_negative(name: str, value) -> float:
    """Convert a DB value (int, float or Decimal) to float, rejecting bad input."""
    if isinstance(value, bool):
        raise InvalidRecordError(f"{name} must be a number, got {value!r}")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise InvalidRecordError(f"{name} must be a number, got {value!r}") from None
    if not math.isfinite(number):
        raise InvalidRecordError(f"{name} must be a finite number, got {value!r}")
    if number < 0:
        raise InvalidRecordError(f"{name} cannot be negative, got {value!r}")
    return number


def payment_score(on_time_payments, total_payments) -> float:
    """Share of payments made on time, 0-100. No payments scores 0."""
    on_time = _non_negative("on_time_payments", on_time_payments)
    total = _non_negative("total_payments", total_payments)
    if on_time > total:
        raise InvalidRecordError(
            f"on_time_payments ({on_time:g}) exceeds total_payments ({total:g})"
        )
    if total == 0:
        return 0.0
    return round(on_time / total * 100, 2)


def debt_score(used_credit, credit_limit) -> float:
    """100 minus credit utilisation in percent, 0-100.

    A limit of 0 scores 0, and so does an account over its limit.
    """
    used = _non_negative("used_credit", used_credit)
    limit = _non_negative("credit_limit", credit_limit)
    if limit == 0:
        return 0.0
    return round(max(0.0, 1 - used / limit) * 100, 2)


def history_score(account_open_date, today: date) -> float:
    """Age of the oldest account relative to MAX_HISTORY_YEARS, 0-100."""
    if isinstance(account_open_date, datetime):
        account_open_date = account_open_date.date()
    if not isinstance(account_open_date, date):
        raise InvalidRecordError(
            f"account_open_date must be a date, got {account_open_date!r}"
        )
    if account_open_date > today:
        raise InvalidRecordError(
            f"account_open_date {account_open_date.isoformat()} is in the future"
        )
    age_years = (today - account_open_date).days / DAYS_PER_YEAR
    return round(min(age_years / MAX_HISTORY_YEARS * 100, 100), 2)


def mix_score(credit_types_used, total_credit_types) -> float:
    """Share of the available credit types the user has, 0-100."""
    used = _non_negative("credit_types_used", credit_types_used)
    total = _non_negative("total_credit_types", total_credit_types)
    if used > total:
        raise InvalidRecordError(
            f"credit_types_used ({used:g}) exceeds total_credit_types ({total:g})"
        )
    if total == 0:
        return 0.0
    return round(used / total * 100, 2)


def combine(components: Mapping[str, float]) -> float:
    """Weighted sum of the four component scores, scaled to 300-850."""
    if set(components) != set(WEIGHTS):
        raise ValueError(
            f"expected components {sorted(WEIGHTS)}, got {sorted(components)}"
        )
    for name, value in components.items():
        if not 0 <= value <= 100:
            raise ValueError(f"component {name!r} must be within 0-100, got {value}")
    weighted = sum(WEIGHTS[name] * components[name] for name in WEIGHTS)
    return round(MIN_SCORE + weighted / 100 * (MAX_SCORE - MIN_SCORE), 2)


def score_band(score: float) -> str:
    """Name of the band an iScore falls in (Poor ... Excellent)."""
    for upper_bound, band in SCORE_BANDS:
        if score < upper_bound:
            return band
    return TOP_BAND
