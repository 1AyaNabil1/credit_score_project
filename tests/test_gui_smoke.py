"""Smoke test of the CustomTkinter window with the data layer faked out.

Needs Tk and a display, and is skipped without them unless
ISCORE_REQUIRE_GUI_TESTS=1 (set in CI, which provides a display through
xvfb-run). The window is withdrawn straight away, so nothing appears on
screen.
"""

import os

import pytest

pytestmark = pytest.mark.gui


def _why_tk_is_unusable():
    try:
        import tkinter

        import customtkinter  # noqa: F401
    except ImportError as e:
        return f"Tk is not installed: {e}"
    try:
        root = tkinter.Tk()
    except tkinter.TclError as e:
        return f"no display available for Tk: {e}"
    root.destroy()
    return None


_reason = _why_tk_is_unusable()
if _reason:
    if os.environ.get("ISCORE_REQUIRE_GUI_TESTS") == "1":
        raise RuntimeError(f"GUI tests are required but cannot run: {_reason}")
    pytest.skip(_reason, allow_module_level=True)

import matplotlib  # noqa: E402

matplotlib.use("Agg")  # the gauge is drawn on a Tk canvas; no pyplot windows

from db.connection import DatabaseError  # noqa: E402
from gui import GUI  # noqa: E402
from logic.calculator import ScoreBreakdown  # noqa: E402

USERS = [
    {"user_id": 1, "full_name": "Aya Nabil"},
    {"user_id": 2, "full_name": "Ahlam Mohammed"},
]


@pytest.fixture
def dialogs(monkeypatch):
    shown = []
    for kind in ("showinfo", "showwarning", "showerror"):
        monkeypatch.setattr(
            GUI.messagebox, kind, lambda title, msg, _k=kind: shown.append((_k, msg))
        )
    monkeypatch.setattr(GUI.messagebox, "askyesno", lambda *a, **k: True)
    return shown


@pytest.fixture
def store(monkeypatch):
    users = [dict(u) for u in USERS]

    def get_user_by_id(user_id):
        return next(
            (dict(u, national_id="X") for u in users if u["user_id"] == user_id), None
        )

    def delete_user(user_id):
        before = len(users)
        users[:] = [u for u in users if u["user_id"] != user_id]
        return len(users) < before

    monkeypatch.setattr(GUI.user_db, "get_all_users", lambda: [dict(u) for u in users])
    monkeypatch.setattr(GUI.user_db, "get_user_by_id", get_user_by_id)
    monkeypatch.setattr(GUI.user_db, "delete_user", delete_user)
    monkeypatch.setattr(
        GUI,
        "score_user",
        lambda user_id: ScoreBreakdown(user_id, 557.27, {}, ("mix",)),
    )
    monkeypatch.setattr(GUI, "calculate_iScore", lambda user_id: 557.27)
    return users


@pytest.fixture
def app(dialogs, store):
    window = GUI.CreditScoreApp()
    window.withdraw()
    yield window
    window.destroy()


def test_lists_users_and_shows_a_score(app, dialogs):
    assert list(app.user_combo.cget("values")) == [
        "1 - Aya Nabil",
        "2 - Ahlam Mohammed",
    ]
    app.on_user_selected("2 - Ahlam Mohammed")
    app.calculate_score()
    assert app.result_label.cget("text") == "Ahlam Mohammed → Score: 557.27 — Poor"
    assert "no data for mix" in app.status.cget("text")
    assert app.chart_frame.winfo_children(), "gauge was not drawn"
    assert dialogs == []


def test_database_error_is_shown_not_raised(app, dialogs, monkeypatch):
    def down(user_id):
        raise DatabaseError("Could not connect to database 'payments_db'")

    monkeypatch.setattr(GUI, "score_user", down)
    app.on_user_selected("1 - Aya Nabil")
    app.calculate_score()
    assert dialogs == [("showerror", "Could not connect to database 'payments_db'")]
    assert app.result_label.cget("text") == ""


def test_delete_clears_selection_and_result(app, dialogs):
    app.on_user_selected("2 - Ahlam Mohammed")
    app.calculate_score()
    app.delete_user()
    assert app.selected_user_id is None
    assert list(app.user_combo.cget("values")) == ["1 - Aya Nabil"]
    assert app.result_label.cget("text") == ""
    app.calculate_score()
    assert dialogs[-1] == ("showwarning", "Please select a user.")


def test_export_writes_csv(app, dialogs, monkeypatch, tmp_path):
    target = tmp_path / "scores.csv"
    monkeypatch.setattr(GUI.filedialog, "asksaveasfilename", lambda **k: str(target))
    app.export_csv()
    assert target.read_text(encoding="utf-8").splitlines() == [
        "User ID,Full Name,Score,Band",
        "1,Aya Nabil,557.27,Poor",
        "2,Ahlam Mohammed,557.27,Poor",
    ]
    assert dialogs[-1][0] == "showinfo"
