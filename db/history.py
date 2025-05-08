from db.connection import get_all_connections
from datetime import datetime


def get_history_score(user_id):
    conns = get_all_connections()
    conn = conns["history"]

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT account_open_date FROM credit_history WHERE user_id = %s",
            (user_id,),
        )
        result = cursor.fetchone()
        if result is None:
            print(f"[WARN] No account history for user_id={user_id}")
            return 0.0

        open_date = result[0]
        today = datetime.today().date()
        age_years = (today - open_date).days / 365

        max_age_years = 10
        history_score = min((age_years / max_age_years) * 100, 100)
        return round(history_score, 2)

    except Exception as e:
        print(f"[ERROR] Failed to fetch history score: {e}")
        return 0.0
    finally:
        if "cursor" in locals():
            cursor.close()
        if conn:
            conn.close()
