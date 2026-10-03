"""End-to-end tests against a real, disposable MySQL server.

WARNING: these tests DROP and recreate users_db, payments_db, debt_db,
history_db and mix_reference_db on the server configured by ISCORE_DB_*.
They only run when ISCORE_RUN_DB_TESTS=1. Never point them at a server whose
data you care about; CI runs them against a throwaway MySQL container.
"""

import os
from datetime import date
from pathlib import Path

import mysql.connector
import pytest

import main
from db.config import load_db_settings
from db.users import add_user, delete_user, get_all_users, get_user_by_id
from logic.calculator import score_user
from logic.scoring import InvalidRecordError
from logic.validation import ValidationError

pytestmark = [
    pytest.mark.mysql,
    pytest.mark.skipif(
        os.environ.get("ISCORE_RUN_DB_TESTS") != "1",
        reason="set ISCORE_RUN_DB_TESTS=1 to run against a disposable MySQL server",
    ),
]

UTILS = Path(__file__).resolve().parent.parent / "utils"
# Child databases first: their tables have foreign keys to users_db.users.
DROP_ORDER = ("payments_db", "debt_db", "history_db", "mix_reference_db", "users_db")

# Seeded users scored on 2025-05-08, worked out by hand from utils/test_data.sql.
# User 2 is the README screenshot ("557.27 - Poor").
DAY = date(2025, 5, 8)
EXPECTED = {1: 701.71, 2: 557.27, 3: 745.34, 4: 666.39, 5: 737.0, 6: 701.71}


def _statements(path):
    """Split a .sql file into statements, dropping -- comments."""
    text = "\n".join(
        line.split("--", 1)[0] for line in path.read_text(encoding="utf-8").splitlines()
    )
    return [statement.strip() for statement in text.split(";") if statement.strip()]


def _execute(statements):
    kwargs = load_db_settings().connect_kwargs()
    # "IF EXISTS" notes are expected here; don't turn them into errors.
    kwargs["raise_on_warnings"] = False
    conn = mysql.connector.connect(**kwargs)
    try:
        cursor = conn.cursor(buffered=True)
        rows = []
        for statement in statements:
            cursor.execute(statement)
            if cursor.with_rows:
                rows = cursor.fetchall()
        conn.commit()
        return rows
    finally:
        conn.close()


def _count(table, user_id):
    return _execute([f"SELECT COUNT(*) FROM {table} WHERE user_id = {int(user_id)}"])[
        0
    ][0]


@pytest.fixture(autouse=True)
def seeded_db():
    """Recreate the five databases from utils/*.sql before every test."""
    _execute(
        [f"DROP DATABASE IF EXISTS {name}" for name in DROP_ORDER]
        + _statements(UTILS / "schema.sql")
        + _statements(UTILS / "test_data.sql")
    )


def test_seeded_users_get_the_hand_computed_scores():
    scores = {uid: score_user(uid, today=DAY).iscore for uid in EXPECTED}
    assert scores == EXPECTED
    assert score_user(2, today=DAY).band == "Poor"


def test_user_list_and_lookup():
    assert [u["user_id"] for u in get_all_users()] == [1, 2, 3, 4, 5, 6]
    assert get_user_by_id(2)["full_name"] == "Ahlam Mohammed"
    assert get_user_by_id(99) is None


def test_several_rows_per_user_are_combined():
    # Before the fix, a second row made the cursor fail with
    # "Unread result found" and the user silently scored 300.
    _execute(
        [
            "INSERT INTO payments_db.payment_records"
            " (user_id, on_time_payments, total_payments) VALUES (3, 0, 20)",
            "INSERT INTO debt_db.credit_usage"
            " (user_id, used_credit, credit_limit) VALUES (3, 5000, 5000)",
            "INSERT INTO history_db.credit_history"
            " (user_id, account_open_date) VALUES (3, '2010-01-01')",
            "INSERT INTO mix_reference_db.credit_mix"
            " (user_id, credit_types_used, total_credit_types) VALUES (3, 4, 4)",
        ]
    )
    result = score_user(3, today=DAY)
    assert result.components == {
        "payment": 50.0,  # (20 + 0) / (20 + 20)
        "debt": 40.0,  # 1 - (1000 + 5000) / (5000 + 5000)
        "history": 100.0,  # oldest account is over 10 years old
        "mix": 100.0,  # latest mix row
    }


def test_impossible_rows_are_reported_not_scored():
    _execute(["UPDATE payments_db.payment_records SET on_time_payments = 99"])
    with pytest.raises(InvalidRecordError, match="user 4"):
        score_user(4, today=DAY)


def test_deleting_a_user_removes_their_records_everywhere():
    # Before the fix, this failed with MySQL error 1451 (foreign key).
    assert delete_user(2) is True
    assert get_user_by_id(2) is None
    for table in (
        "payments_db.payment_records",
        "debt_db.credit_usage",
        "history_db.credit_history",
        "mix_reference_db.credit_mix",
    ):
        assert _count(table, 2) == 0
        assert _count(table, 1) == 1
    assert delete_user(2) is False


def test_added_user_scores_minimum_until_they_have_data():
    new_id = add_user("  Test   Person ", "TEST-0001")
    assert new_id == 7
    assert get_user_by_id(new_id)["full_name"] == "Test Person"

    result = score_user(new_id, today=DAY)
    assert result.iscore == 300.0
    assert result.missing == ("payment", "debt", "history", "mix")

    with pytest.raises(ValidationError, match="already exists"):
        add_user("Someone Else", "TEST-0001")


def test_command_line_report(capsys):
    assert main.main() == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 6
    assert lines[1].startswith("User: Ahlam Mohammed, iScore: ")
