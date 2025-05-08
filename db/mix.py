from db.connection import get_all_connections


def get_mix_score(user_id):
    conns = get_all_connections()
    conn = conns["mix"]

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT credit_types_used, total_credit_types FROM credit_mix WHERE user_id = %s",
            (user_id,),
        )
        result = cursor.fetchone()
        if result is None:
            print(f"[WARN] No mix data for user_id={user_id}")
            return 0.0

        used, total = result
        if total == 0:
            return 0.0

        mix_score = (used / total) * 100
        return round(mix_score, 2)

    except Exception as e:
        print(f"[ERROR] Failed to fetch mix score: {e}")
        return 0.0
    finally:
        if "cursor" in locals():
            cursor.close()
        if conn:
            conn.close()
