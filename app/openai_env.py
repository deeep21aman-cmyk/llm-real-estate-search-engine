import os

from dotenv import load_dotenv


load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")

    cleaned = value.strip().strip("\"'“”‘’")
    if not cleaned:
        raise RuntimeError(f"Missing required environment variable: {name}")

    return cleaned
