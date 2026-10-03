from db.connection import db_cursor


def fetch_credit_mix(user_id):
    """Return ``(credit_types_used, total_credit_types)`` from the user's most
    recent credit-mix record, or None if there is no complete record."""
    with db_cursor("mix") as cursor:
        cursor.execute(
            "SELECT credit_types_used, total_credit_types FROM credit_mix "
            "WHERE user_id = %s ORDER BY mix_id DESC LIMIT 1",
            (user_id,),
        )
        row = cursor.fetchone()
    if row is None or None in row:
        return None
    return int(row[0]), int(row[1])
