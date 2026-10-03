"""MySQL connection helpers.

The data lives in five MySQL databases (schemas) on one server; see
utils/schema.sql. Every query opens one connection to the database it needs
and closes it again, and any MySQL failure is raised as DatabaseError so
callers can tell "the database is down" apart from "this user has no data".
"""

from collections.abc import Iterator
from contextlib import contextmanager, suppress

import mysql.connector
from mysql.connector import Error as MySQLError

from db.config import load_db_settings

# Logical name -> MySQL database name, as created by utils/schema.sql.
DATABASES = {
    "users": "users_db",
    "payments": "payments_db",
    "debt": "debt_db",
    "history": "history_db",
    "mix": "mix_reference_db",
}


class DatabaseError(RuntimeError):
    """MySQL could not be reached, or a query failed."""


def connect_to_db(db_name: str):
    """Open a connection to one database. Raises DatabaseError on failure."""
    try:
        return mysql.connector.connect(
            database=db_name, **load_db_settings().connect_kwargs()
        )
    except MySQLError as e:
        raise DatabaseError(f"Could not connect to database {db_name!r}: {e}") from e


@contextmanager
def db_cursor(key: str) -> Iterator:
    """Yield a buffered cursor on ``DATABASES[key]``.

    Everything executed inside the ``with`` block is one transaction: it is
    committed when the block finishes and rolled back if it raises. The
    cursor and connection are always closed. MySQL errors are re-raised as
    DatabaseError.
    """
    db_name = DATABASES[key]
    conn = connect_to_db(db_name)
    cursor = None
    try:
        cursor = conn.cursor(buffered=True)
        yield cursor
        conn.commit()
    except MySQLError as e:
        with suppress(MySQLError):
            conn.rollback()
        raise DatabaseError(f"Query on database {db_name!r} failed: {e}") from e
    except BaseException:
        with suppress(MySQLError):
            conn.rollback()
        raise
    finally:
        if cursor is not None:
            with suppress(MySQLError):
                cursor.close()
        with suppress(MySQLError):
            conn.close()


def get_all_connections():
    """Open a connection to every database.

    Deprecated: callers must close all five connections themselves. Use
    db_cursor() instead.
    """
    return {key: connect_to_db(name) for key, name in DATABASES.items()}
