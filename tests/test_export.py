import csv

import pytest

from db.connection import DatabaseError
from logic.export import HEADER, build_rows, write_csv

USERS = [
    {"user_id": 1, "full_name": "Aya Nabil"},
    {"user_id": 2, "full_name": "آية أحمد"},
]


def test_builds_one_row_per_user_with_band():
    scores = {1: 713.3, 2: 568.86}
    rows = build_rows(USERS, scores.__getitem__)
    assert rows == [
        (1, "Aya Nabil", 713.3, "Good"),
        (2, "آية أحمد", 568.86, "Poor"),
    ]


@pytest.mark.parametrize("name", ["=1+1", "+1", "-1", "@SUM(A1)", "\tx"])
def test_neutralises_spreadsheet_formulas(name):
    rows = build_rows([{"user_id": 1, "full_name": name}], lambda _: 600.0)
    assert rows[0][1] == "'" + name


def test_scoring_error_propagates_before_anything_is_written():
    def score_of(user_id):
        if user_id == 2:
            raise DatabaseError("lost connection")
        return 700.0

    with pytest.raises(DatabaseError):
        build_rows(USERS, score_of)


def test_writes_utf8_csv_with_header(tmp_path):
    path = tmp_path / "scores.csv"
    write_csv(path, build_rows(USERS, lambda _: 700.0))
    with open(path, newline="", encoding="utf-8") as f:
        lines = list(csv.reader(f))
    assert lines[0] == list(HEADER)
    assert lines[1:] == [
        ["1", "Aya Nabil", "700.0", "Good"],
        ["2", "آية أحمد", "700.0", "Good"],
    ]
