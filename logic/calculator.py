"""Compute a user's iScore from the four score databases.

The formulas live in logic.scoring; this module only fetches each user's
records and feeds them in. Database failures raise db.connection.DatabaseError
and impossible records raise logic.scoring.InvalidRecordError, instead of
quietly returning a minimum score.
"""

import logging
from dataclasses import dataclass, field
from datetime import date

from db.debt import fetch_credit_usage
from db.history import fetch_oldest_account_date
from db.mix import fetch_credit_mix
from db.payments import fetch_payment_totals
from logic import scoring
from logic.scoring import InvalidRecordError

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScoreBreakdown:
    user_id: int
    iscore: float
    # Component scores (0-100) keyed like scoring.WEIGHTS.
    components: dict = field(default_factory=dict)
    # Components with no stored data; they count as 0.
    missing: tuple = ()

    @property
    def band(self) -> str:
        return scoring.score_band(self.iscore)


def score_user(user_id, today: date | None = None) -> ScoreBreakdown:
    """Fetch a user's records and compute their iScore.

    A component with no stored data counts as 0 and is listed in ``missing``.
    """
    today = today or date.today()

    payments = fetch_payment_totals(user_id)
    usage = fetch_credit_usage(user_id)
    oldest_account = fetch_oldest_account_date(user_id)
    mix = fetch_credit_mix(user_id)

    try:
        scores = {
            "payment": None if payments is None else scoring.payment_score(*payments),
            "debt": None if usage is None else scoring.debt_score(*usage),
            "history": (
                None
                if oldest_account is None
                else scoring.history_score(oldest_account, today)
            ),
            "mix": None if mix is None else scoring.mix_score(*mix),
        }
    except InvalidRecordError as e:
        raise InvalidRecordError(f"Cannot score user {user_id}: {e}") from e

    missing = tuple(name for name, value in scores.items() if value is None)
    components = {name: value or 0.0 for name, value in scores.items()}
    iscore = scoring.combine(components)
    log.debug("user %s components=%s missing=%s", user_id, components, missing)
    return ScoreBreakdown(user_id, iscore, components, missing)


def calculate_iScore(user_id) -> float:
    """Return just the iScore (300-850) for a user."""
    return score_user(user_id).iscore
