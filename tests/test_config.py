import pytest

from db import config
from db.config import ConfigError, DBSettings, load_db_settings

VARIABLES = (
    "ISCORE_DB_HOST",
    "ISCORE_DB_PORT",
    "ISCORE_DB_USER",
    "ISCORE_DB_PASSWORD",
    "ISCORE_DB_CONNECT_TIMEOUT",
)


def test_defaults_when_nothing_is_set():
    assert load_db_settings({}) == DBSettings(
        host="localhost", port=3306, user="root", password="", connect_timeout=5
    )


def test_reads_every_variable():
    settings = load_db_settings(
        {
            "ISCORE_DB_HOST": "db.internal",
            "ISCORE_DB_PORT": "3307",
            "ISCORE_DB_USER": "iscore",
            "ISCORE_DB_PASSWORD": " keeps spaces ",
            "ISCORE_DB_CONNECT_TIMEOUT": "10",
        }
    )
    assert settings == DBSettings("db.internal", 3307, "iscore", " keeps spaces ", 10)


def test_connect_kwargs_never_hardcode_a_password():
    kwargs = load_db_settings({}).connect_kwargs()
    assert kwargs["password"] == ""
    assert kwargs["connection_timeout"] == 5


@pytest.mark.parametrize("port", ["abc", "0", "70000", "-1"])
def test_rejects_bad_port(port):
    with pytest.raises(ConfigError, match="ISCORE_DB_PORT"):
        load_db_settings({"ISCORE_DB_PORT": port})


def test_env_file_is_loaded_but_real_environment_wins(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("ISCORE_DB_HOST=from-dotenv\nISCORE_DB_USER=dotenv-user\n")
    monkeypatch.setattr(config, "ENV_FILE", env_file)
    for name in VARIABLES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("ISCORE_DB_USER", "shell-user")

    settings = load_db_settings()

    assert settings.host == "from-dotenv"
    assert settings.user == "shell-user"
