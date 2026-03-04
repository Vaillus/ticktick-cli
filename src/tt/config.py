import os
from pathlib import Path

from dotenv import dotenv_values, set_key

CONFIG_DIR = Path(os.environ.get("TT_CONFIG_DIR", Path.home() / ".config" / "tt"))
ENV_FILE = CONFIG_DIR / ".env"

REQUIRED_KEYS = ("TICKTICK_CLIENT_ID", "TICKTICK_CLIENT_SECRET")
TOKEN_KEYS = ("TICKTICK_ACCESS_TOKEN", "TICKTICK_REFRESH_TOKEN")


class ConfigError(Exception):
    pass


def load_config() -> dict[str, str]:
    if not ENV_FILE.exists():
        raise ConfigError(f"Config not found: {ENV_FILE}\nRun 'tt auth' first.")
    values = dotenv_values(ENV_FILE)
    return {k: v for k, v in values.items() if v is not None}


def save_token(key: str, value: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    set_key(str(ENV_FILE), key, value)


def save_tokens(access_token: str, refresh_token: str) -> None:
    save_token("TICKTICK_ACCESS_TOKEN", access_token)
    save_token("TICKTICK_REFRESH_TOKEN", refresh_token)


def get_client_credentials() -> tuple[str, str]:
    config = load_config()
    client_id = config.get("TICKTICK_CLIENT_ID")
    client_secret = config.get("TICKTICK_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ConfigError(
            "Missing TICKTICK_CLIENT_ID or TICKTICK_CLIENT_SECRET in "
            f"{ENV_FILE}\nAdd them manually before running 'tt auth'."
        )
    return client_id, client_secret


def get_access_token() -> str:
    config = load_config()
    token = config.get("TICKTICK_ACCESS_TOKEN")
    if not token:
        raise ConfigError("No access token found. Run 'tt auth' first.")
    return token


def get_refresh_token() -> str:
    config = load_config()
    token = config.get("TICKTICK_REFRESH_TOKEN")
    if not token:
        raise ConfigError("No refresh token found. Run 'tt auth' first.")
    return token


def get_inbox_id() -> str | None:
    config = load_config()
    return config.get("TICKTICK_INBOX_ID") or None


def save_inbox_id(inbox_id: str) -> None:
    save_token("TICKTICK_INBOX_ID", inbox_id)
