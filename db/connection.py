import mysql.connector
from mysql.connector import Error

# 🔐 Global connection settings (adjust your password if needed)
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ayanabil@123",  # ← Replace this
    "raise_on_warnings": True,
}


# Connect to a specific MySQL database
def connect_to_db(db_name):
    try:
        conn = mysql.connector.connect(database=db_name, **DB_CONFIG)
        if conn.is_connected():
            print(f"[CONNECTED] to {db_name}")
            return conn
    except Error as e:
        print(f"[ERROR] Failed to connect to {db_name}: {e}")
    return None


# Get all database connections in one call
def get_all_connections():
    return {
        "users": connect_to_db("users_db"),
        "payments": connect_to_db("payments_db"),
        "debt": connect_to_db("debt_db"),
        "history": connect_to_db("history_db"),
        "mix": connect_to_db("mix_reference_db"),
    }
