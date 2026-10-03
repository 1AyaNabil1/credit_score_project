from db.connection import db_cursor


def get_user_by_id(user_id):
    """Return ``{"user_id", "full_name", "national_id"}`` or None if not found."""
    with db_cursor("users") as cursor:
        cursor.execute(
            "SELECT user_id, full_name, national_id FROM users WHERE user_id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return {"user_id": row[0], "full_name": row[1], "national_id": row[2]}


def get_all_users():
    """Return every user as ``{"user_id", "full_name"}``, ordered by id.

    National IDs are deliberately not loaded here.
    """
    with db_cursor("users") as cursor:
        cursor.execute("SELECT user_id, full_name FROM users ORDER BY user_id")
        rows = cursor.fetchall()
    return [{"user_id": row[0], "full_name": row[1]} for row in rows]
