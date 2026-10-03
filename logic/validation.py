"""Validation of user input before it reaches the database."""

import re

# Column sizes from utils/schema.sql (users_db.users).
MAX_NAME_LENGTH = 100
MAX_NATIONAL_ID_LENGTH = 20

_NATIONAL_ID_PATTERN = re.compile(r"[A-Za-z0-9-]+")


class ValidationError(ValueError):
    """User input that cannot be saved; the message is safe to show."""


def clean_new_user(full_name, national_id) -> tuple[str, str]:
    """Normalise and validate a new user's name and national ID.

    Returns ``(full_name, national_id)`` with surrounding whitespace removed
    and runs of inner whitespace in the name collapsed to single spaces.
    """
    name = " ".join(str(full_name or "").split())
    nid = str(national_id or "").strip()

    if not name:
        raise ValidationError("Full name is required.")
    if len(name) > MAX_NAME_LENGTH:
        raise ValidationError(
            f"Full name must be at most {MAX_NAME_LENGTH} characters."
        )
    if not nid:
        raise ValidationError("National ID is required.")
    if len(nid) > MAX_NATIONAL_ID_LENGTH:
        raise ValidationError(
            f"National ID must be at most {MAX_NATIONAL_ID_LENGTH} characters."
        )
    if not _NATIONAL_ID_PATTERN.fullmatch(nid):
        raise ValidationError(
            "National ID may only contain letters, digits and hyphens."
        )
    return name, nid
