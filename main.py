"""Print every user's iScore: a command-line alternative to the GUI."""

import sys

from db.connection import DatabaseError
from db.users import get_all_users
from logic.calculator import score_user
from logic.scoring import InvalidRecordError


def main() -> int:
    try:
        users = get_all_users()
    except DatabaseError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    if not users:
        print("No users found.")
        return 0

    exit_code = 0
    for user in users:
        try:
            result = score_user(user["user_id"])
        except (DatabaseError, InvalidRecordError) as e:
            print(f"User: {user['full_name']}, error: {e}", file=sys.stderr)
            exit_code = 1
            continue
        note = f" [no data: {', '.join(result.missing)}]" if result.missing else ""
        print(
            f"User: {user['full_name']}, iScore: {result.iscore} ({result.band}){note}"
        )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
