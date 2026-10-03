from db.connection import db_cursor


def fetch_credit_usage(user_id):
    """Return ``(used_credit, credit_limit)`` summed over all of the user's
    credit lines, or None if the user has no credit lines."""
    with db_cursor("debt") as cursor:
        cursor.execute(
            "SELECT SUM(used_credit), SUM(credit_limit) "
            "FROM credit_usage WHERE user_id = %s",
            (user_id,),
        )
        used, limit = cursor.fetchone()
    if used is None or limit is None:
        return None
    return float(used), float(limit)
