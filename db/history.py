from db.connection import db_cursor


def fetch_oldest_account_date(user_id):
    """Return the opening date of the user's oldest account, or None if the
    user has no account history."""
    with db_cursor("history") as cursor:
        cursor.execute(
            "SELECT MIN(account_open_date) FROM credit_history WHERE user_id = %s",
            (user_id,),
        )
        (open_date,) = cursor.fetchone()
    return open_date
