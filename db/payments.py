from db.connection import get_all_connections


def get_payment_score(user_id):
    conns = get_all_connections()
    conn = conns["payments"]

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT on_time_payments, total_payments FROM payment_records WHERE user_id = %s",
            (user_id,),
        )
        result = cursor.fetchone()
        if result is None:
            print(f"[WARN] No payment data for user_id={user_id}")
            return 0.0

        on_time, total = result
        if total == 0:
            return 0.0

        payment_score = (on_time / total) * 100
        return round(payment_score, 2)

    except Exception as e:
        print(f"[ERROR] Failed to fetch payment score: {e}")
        return 0.0
    finally:
        cursor.close()
        conn.close()
