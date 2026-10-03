from db.connection import DATABASES, db_cursor
from logic.validation import ValidationError, clean_new_user


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


def add_user(full_name, national_id):
    """Validate and insert a new user; return the new user_id.

    Raises logic.validation.ValidationError for bad input or a national ID
    that is already registered.
    """
    name, nid = clean_new_user(full_name, national_id)
    with db_cursor("users") as cursor:
        cursor.execute("SELECT 1 FROM users WHERE national_id = %s", (nid,))
        if cursor.fetchone() is not None:
            raise ValidationError("A user with this national ID already exists.")
        # users.user_id has no AUTO_INCREMENT; lock the rows while picking the next id.
        cursor.execute("SELECT COALESCE(MAX(user_id), 0) + 1 FROM users FOR UPDATE")
        (new_id,) = cursor.fetchone()
        cursor.execute(
            "INSERT INTO users (user_id, full_name, national_id) VALUES (%s, %s, %s)",
            (new_id, name, nid),
        )
    return int(new_id)


# Tables in the score databases that reference users_db.users(user_id).
_DEPENDENT_TABLES = (
    ("payments", "payment_records"),
    ("debt", "credit_usage"),
    ("history", "credit_history"),
    ("mix", "credit_mix"),
)


def delete_user(user_id):
    """Delete a user and their rows in the four score databases.

    The rows are removed in one transaction, children first, because the
    score tables have foreign keys to users_db.users. Returns True if the
    user existed.
    """
    with db_cursor("users") as cursor:
        for key, table in _DEPENDENT_TABLES:
            # Identifiers come from the constants above, never from input.
            cursor.execute(
                f"DELETE FROM `{DATABASES[key]}`.`{table}` WHERE user_id = %s",
                (user_id,),
            )
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        deleted = cursor.rowcount > 0
    return deleted
