import mysql.connector
from mysql.connector import Error

from db.config import load_db_settings


# Connect to a specific MySQL database
def connect_to_db(db_name):
    try:
        conn = mysql.connector.connect(
            database=db_name, **load_db_settings().connect_kwargs()
        )
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
