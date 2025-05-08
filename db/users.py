from db.connection import get_all_connections


def get_user_by_id(user_id):
    conns = get_all_connections()
    conn = conns["users"]

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, full_name, national_id FROM users WHERE user_id = %s",
            (user_id,),
        )
        result = cursor.fetchone()
        if result is None:
            print(f"[WARN] User ID {user_id} not found.")
            return None

        return {"user_id": result[0], "full_name": result[1], "national_id": result[2]}

    except Exception as e:
        print(f"[ERROR] Failed to fetch user info: {e}")
        return None
    finally:
        if "cursor" in locals():
            cursor.close()
        if conn:
            conn.close()


def get_all_users():
    conns = get_all_connections()
    conn = conns["users"]

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, full_name FROM users")
        rows = cursor.fetchall()
        return [{"user_id": row[0], "full_name": row[1]} for row in rows]

    except Exception as e:
        print(f"[ERROR] Failed to fetch user list: {e}")
        return []
    finally:
        if "cursor" in locals():
            cursor.close()
        if conn:
            conn.close()
