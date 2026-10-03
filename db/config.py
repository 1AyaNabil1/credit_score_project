"""Database settings, read from environment variables (or a local .env file).

Nothing secret lives in the source code. Copy ``.env.example`` to ``.env`` and
fill in your own MySQL credentials, or export the variables in your shell.
Variables already set in the environment win over values in ``.env``.
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class ConfigError(ValueError):
    """Raised when a database setting is present but invalid."""


@dataclass(frozen=True)
class DBSettings:
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    connect_timeout: int = 5

    def connect_kwargs(self) -> dict:
        """Keyword arguments for ``mysql.connector.connect``."""
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "connection_timeout": self.connect_timeout,
            "raise_on_warnings": True,
        }


def _positive_int(
    environ: Mapping[str, str], name: str, default: int, upper: int
) -> int:
    raw = environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ConfigError(f"{name} must be a whole number, got {raw!r}") from None
    if not 1 <= value <= upper:
        raise ConfigError(f"{name} must be between 1 and {upper}, got {value}")
    return value


def load_db_settings(environ: Mapping[str, str] | None = None) -> DBSettings:
    """Build :class:`DBSettings` from ``ISCORE_DB_*`` variables.

    When ``environ`` is omitted, ``.env`` in the project root is loaded first
    (without overriding variables that are already set) and ``os.environ`` is
    used. Pass a mapping explicitly to read settings from somewhere else, e.g.
    in tests.
    """
    if environ is None:
        load_dotenv(ENV_FILE, override=False)
        environ = os.environ

    defaults = DBSettings()
    return DBSettings(
        host=environ.get("ISCORE_DB_HOST", "").strip() or defaults.host,
        port=_positive_int(environ, "ISCORE_DB_PORT", defaults.port, 65535),
        user=environ.get("ISCORE_DB_USER", "").strip() or defaults.user,
        password=environ.get("ISCORE_DB_PASSWORD", defaults.password),
        connect_timeout=_positive_int(
            environ, "ISCORE_DB_CONNECT_TIMEOUT", defaults.connect_timeout, 600
        ),
    )
