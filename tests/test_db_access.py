"""Data-access tests against a fake mysql.connector, so no server is needed."""

import socket
from datetime import date
from decimal import Decimal

import pytest
from mysql.connector import Error as MySQLError

from db import connection, debt, history, mix, payments, users
from db.config import DBSettings
from db.connection import DatabaseError, db_cursor
from logic.validation import ValidationError


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self.rowcount = 0
        self.closed = False
        self._result = []

    def execute(self, sql, params=()):
        self.conn.executed.append((" ".join(sql.split()), params))
        if self.conn.fail_on and self.conn.fail_on in sql:
            raise MySQLError(msg="simulated failure")
        self._result = list(self.conn.results.pop(0)) if self.conn.results else []
        self.rowcount = len(self._result) or 1

    def fetchone(self):
        return self._result.pop(0) if self._result else None

    def fetchall(self):
        rows, self._result = self._result, []
        return rows

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, results=(), fail_on=None):
        self.results = list(results)
        self.fail_on = fail_on
        self.executed = []
        self.cursors = []
        self.committed = self.rolled_back = self.closed = False

    def cursor(self, buffered=False):
        assert buffered, "cursors must be buffered to avoid 'Unread result found'"
        cursor = FakeCursor(self)
        self.cursors.append(cursor)
        return cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


@pytest.fixture
def fake_db(monkeypatch):
    """Make every connect() return a FakeConnection fed with queued results.

    Each queued item is the list of rows returned by one execute() call.
    """
    state = {"connections": [], "results": [], "fail_on": None}

    def connect(**kwargs):
        conn = FakeConnection(state["results"], state["fail_on"])
        conn.kwargs = kwargs
        state["results"] = []
        state["connections"].append(conn)
        return conn

    monkeypatch.setattr(connection.mysql.connector, "connect", connect)
    monkeypatch.setattr(
        connection, "load_db_settings", lambda: DBSettings(host="db.test")
    )
    return state


class TestDbCursor:
    def test_commits_and_closes_everything(self, fake_db):
        with db_cursor("payments") as cursor:
            cursor.execute("SELECT 1")
        (conn,) = fake_db["connections"]
        assert conn.kwargs["database"] == "payments_db"
        assert conn.kwargs["host"] == "db.test"
        assert conn.committed and conn.closed and conn.cursors[0].closed
        assert not conn.rolled_back

    def test_mysql_error_rolls_back_and_raises_database_error(self, fake_db):
        fake_db["fail_on"] = "SELECT"
        with pytest.raises(DatabaseError, match="payments_db"):
            with db_cursor("payments") as cursor:
                cursor.execute("SELECT 1")
        (conn,) = fake_db["connections"]
        assert conn.rolled_back and conn.closed and not conn.committed

    def test_other_errors_roll_back_and_pass_through(self, fake_db):
        with pytest.raises(KeyError):
            with db_cursor("users"):
                raise KeyError("boom")
        (conn,) = fake_db["connections"]
        assert conn.rolled_back and conn.closed

    def test_connection_failure_raises_database_error(self, monkeypatch):
        def refuse(**kwargs):
            raise MySQLError(msg="Can't connect")

        monkeypatch.setattr(connection.mysql.connector, "connect", refuse)
        with pytest.raises(DatabaseError, match="Could not connect"):
            with db_cursor("users"):
                pass


def _closed_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_unreachable_server_raises_instead_of_scoring_300(monkeypatch):
    from logic.calculator import score_user

    monkeypatch.setenv("ISCORE_DB_HOST", "127.0.0.1")
    monkeypatch.setenv("ISCORE_DB_PORT", str(_closed_port()))
    monkeypatch.setenv("ISCORE_DB_CONNECT_TIMEOUT", "2")
    with pytest.raises(DatabaseError):
        score_user(1)


class TestFetchers:
    def test_payments_are_summed_and_converted(self, fake_db):
        fake_db["results"] = [[(Decimal("38"), Decimal("40"))]]
        assert payments.fetch_payment_totals(1) == (38, 40)
        sql, params = fake_db["connections"][0].executed[0]
        assert "SUM(on_time_payments)" in sql and params == (1,)

    def test_no_payment_rows_is_none(self, fake_db):
        fake_db["results"] = [[(None, None)]]
        assert payments.fetch_payment_totals(1) is None

    def test_credit_usage_decimal_becomes_float(self, fake_db):
        fake_db["results"] = [[(Decimal("3000.00"), Decimal("10000.00"))]]
        assert debt.fetch_credit_usage(1) == (3000.0, 10000.0)

    def test_no_credit_lines_is_none(self, fake_db):
        fake_db["results"] = [[(None, None)]]
        assert debt.fetch_credit_usage(1) is None

    def test_history_returns_oldest_date(self, fake_db):
        fake_db["results"] = [[(date(2018, 5, 1),)]]
        assert history.fetch_oldest_account_date(1) == date(2018, 5, 1)
        assert "MIN(account_open_date)" in fake_db["connections"][0].executed[0][0]

    def test_mix_uses_latest_row(self, fake_db):
        fake_db["results"] = [[(2, 4)]]
        assert mix.fetch_credit_mix(1) == (2, 4)
        assert (
            "ORDER BY mix_id DESC LIMIT 1" in fake_db["connections"][0].executed[0][0]
        )

    @pytest.mark.parametrize("rows", [[], [(None, 4)], [(2, None)]])
    def test_missing_or_incomplete_mix_is_none(self, fake_db, rows):
        fake_db["results"] = [rows]
        assert mix.fetch_credit_mix(1) is None

    def test_each_fetch_uses_exactly_one_connection(self, fake_db):
        fake_db["results"] = [[(1, 2)]]
        payments.fetch_payment_totals(1)
        assert len(fake_db["connections"]) == 1


class TestUsers:
    def test_get_user_by_id(self, fake_db):
        fake_db["results"] = [[(1, "Aya Nabil", "EGY1")]]
        assert users.get_user_by_id(1) == {
            "user_id": 1,
            "full_name": "Aya Nabil",
            "national_id": "EGY1",
        }

    def test_unknown_user_is_none(self, fake_db):
        fake_db["results"] = [[]]
        assert users.get_user_by_id(99) is None

    def test_user_list_leaves_out_national_ids(self, fake_db):
        fake_db["results"] = [[(1, "A"), (2, "B")]]
        assert users.get_all_users() == [
            {"user_id": 1, "full_name": "A"},
            {"user_id": 2, "full_name": "B"},
        ]
        assert "national_id" not in fake_db["connections"][0].executed[0][0]

    def test_add_user_cleans_input_and_picks_next_id(self, fake_db):
        fake_db["results"] = [[], [(7,)], []]
        assert users.add_user("  New   User ", " NEW-1 ") == 7
        (conn,) = fake_db["connections"]
        insert_sql, insert_params = conn.executed[-1]
        assert insert_sql.startswith("INSERT INTO users")
        assert insert_params == (7, "New User", "NEW-1")
        assert conn.committed

    def test_add_user_rejects_duplicate_national_id(self, fake_db):
        fake_db["results"] = [[(1,)]]
        with pytest.raises(ValidationError, match="already exists"):
            users.add_user("Someone", "EGY1")
        (conn,) = fake_db["connections"]
        assert conn.rolled_back and not conn.committed
        assert not any(sql.startswith("INSERT") for sql, _ in conn.executed)

    def test_add_user_validates_before_touching_the_database(self, fake_db):
        with pytest.raises(ValidationError):
            users.add_user("", "EGY1")
        assert fake_db["connections"] == []

    def test_delete_removes_dependent_rows_first_in_one_transaction(self, fake_db):
        assert users.delete_user(3) is True
        (conn,) = fake_db["connections"]
        tables = [sql.split()[2] for sql, _ in conn.executed]
        assert tables == [
            "`payments_db`.`payment_records`",
            "`debt_db`.`credit_usage`",
            "`history_db`.`credit_history`",
            "`mix_reference_db`.`credit_mix`",
            "users",
        ]
        assert all(params == (3,) for _, params in conn.executed)
        assert conn.committed

    def test_failed_delete_rolls_back(self, fake_db):
        fake_db["fail_on"] = "credit_history"
        with pytest.raises(DatabaseError):
            users.delete_user(3)
        (conn,) = fake_db["connections"]
        assert conn.rolled_back and not conn.committed
