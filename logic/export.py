"""CSV export of every user's iScore and band."""

import csv
from collections.abc import Callable, Iterable

from logic.scoring import score_band

HEADER = ("User ID", "Full Name", "Score", "Band")

# Spreadsheet apps treat cells starting with these as formulas.
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _safe_cell(text: str) -> str:
    """Prefix a quote so a name such as "=HYPERLINK(...)" stays plain text."""
    return "'" + text if text.startswith(_FORMULA_PREFIXES) else text


def build_rows(users: Iterable[dict], score_of: Callable[[int], float]) -> list:
    """Score every user and return the CSV rows (without the header).

    All scores are computed before anything is written, so a database error
    part-way through cannot leave a half-written file.
    """
    rows = []
    for user in users:
        score = score_of(user["user_id"])
        rows.append(
            (user["user_id"], _safe_cell(user["full_name"]), score, score_band(score))
        )
    return rows


def write_csv(path, rows) -> None:
    """Write the header and rows as UTF-8, so non-Latin names survive."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(rows)
