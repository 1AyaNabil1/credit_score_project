from db.connection import db_cursor


def fetch_payment_totals(user_id):
    """Return ``(on_time_payments, total_payments)`` summed over all of the
    user's payment records, or None if the user has no payment records."""
    with db_cursor("payments") as cursor:
        cursor.execute(
            "SELECT SUM(on_time_payments), SUM(total_payments) "
            "FROM payment_records WHERE user_id = %s",
            (user_id,),
        )
        on_time, total = cursor.fetchone()
    if total is None:
        return None
    return int(on_time or 0), int(total)
