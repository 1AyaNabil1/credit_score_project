from db.connection import get_all_connections


def get_debt_score(user_id):
    conns = get_all_connections()
    conn = conns["debt"]

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT used_credit, credit_limit FROM credit_usage WHERE user_id = %s",
            (user_id,),
        )
        result = cursor.fetchone()
        if result is None:
            print(f"[WARN] No debt data for user_id={user_id}")
            return 0.0

        used, limit = result
        if limit == 0:
            return 0.0

        debt_score = (1 - (used / limit)) * 100
        return round(debt_score, 2)

    except Exception as e:
        print(f"[ERROR] Failed to fetch debt score: {e}")
        return 0.0
    finally:
        if "cursor" in locals():
            cursor.close()
        if conn:
            conn.close()
