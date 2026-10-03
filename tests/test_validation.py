import pytest

from logic.validation import ValidationError, clean_new_user


def test_trims_and_collapses_whitespace():
    assert clean_new_user("  Aya   Nabil\t", " EGY-123 ") == ("Aya Nabil", "EGY-123")


def test_accepts_non_latin_names():
    assert clean_new_user("آية نبيل", "29901011234567") == (
        "آية نبيل",
        "29901011234567",
    )


@pytest.mark.parametrize(
    ("name", "nid", "message"),
    [
        ("", "EGY1", "Full name is required"),
        ("   ", "EGY1", "Full name is required"),
        (None, "EGY1", "Full name is required"),
        ("A" * 101, "EGY1", "at most 100"),
        ("Aya", "", "National ID is required"),
        ("Aya", "1" * 21, "at most 20"),
        ("Aya", "EGY 123", "letters, digits and hyphens"),
        ("Aya", "1;DROP", "letters, digits and hyphens"),
    ],
)
def test_rejects_bad_input(name, nid, message):
    with pytest.raises(ValidationError, match=message):
        clean_new_user(name, nid)


def test_limits_match_the_schema_columns():
    name, nid = clean_new_user("A" * 100, "1" * 20)
    assert len(name) == 100
    assert len(nid) == 20
