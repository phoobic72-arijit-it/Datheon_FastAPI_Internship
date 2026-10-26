import secrets
from pathlib import Path

from dotenv import dotenv_values, set_key


def main():
    env_path = Path(__file__).resolve().parent / ".env"

    env_path.touch(mode=0o600, exist_ok=True)
    existing = dotenv_values(env_path)

    defaults = {
        "SECRET_KEY": secrets.token_hex(32),
        "ADMIN_USERNAME": "admin",
        "ADMIN_PASSWORD": secrets.token_urlsafe(24),
    }

    for key, value in defaults.items():
        if not existing.get(key):
            set_key(str(env_path), key, value)

    env_path.chmod(0o600)

    print("Local configuration is ready in .env.")
    print("Open .env to see ADMIN_USERNAME and ADMIN_PASSWORD.")


if __name__ == "__main__":
    main()