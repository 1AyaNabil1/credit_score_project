from db.payments import get_payment_score
from db.debt import get_debt_score
from db.history import get_history_score
from db.mix import get_mix_score


def calculate_iScore(user_id):
    try:
        payment_score = get_payment_score(user_id)
        debt_score = get_debt_score(user_id)
        history_score = get_history_score(user_id)
        mix_score = get_mix_score(user_id)

        print(
            f"[INFO] Scores for user {user_id} → Payment: {payment_score}, Debt: {debt_score}, History: {history_score}, Mix: {mix_score}"
        )

        weighted_score = (
            0.35 * payment_score
            + 0.30 * debt_score
            + 0.15 * history_score
            + 0.20 * mix_score
        )

        # Scale to iScore range (300–850)
        scaled_score = 300 + ((weighted_score / 100) * (850 - 300))
        return round(scaled_score, 2)

    except Exception as e:
        print(f"[ERROR] Failed to calculate iScore: {e}")
        return 300.0  # Minimum score fallback
