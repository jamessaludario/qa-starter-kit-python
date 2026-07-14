"""
constants.py
============
Every fixed value the tests share, in ONE place. Your app's address
comes from the .env file (copy .env.example to .env and fill it in).
"""

import os
from pathlib import Path


def _load_dotenv():
    """
    Read the .env file next to this script (if there is one) and put its
    KEY=value lines into the environment. A tiny stand-in for the
    python-dotenv package so the kit needs one less dependency.
    """
    env_file = Path(__file__).with_name(".env")
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

# A short name for your project (used in report titles).
PROJECT_NAME = os.environ.get("PROJECT_NAME", "my-app")

# The web app under test. Everything starts from this address.
BASE_URL = os.environ.get("BASE_URL", "")
if not BASE_URL:
    raise SystemExit(
        "BASE_URL is not set!\n"
        "Copy .env.example to .env and fill in your app's address."
    )

# Requests whose URL contains any of these keywords are blocked during
# tests (see fixtures/browser.py). Useful for ad/analytics scripts that
# make tests flaky. Empty by default.
BLOCKED_URL_KEYWORDS = []

# Add your app's shared test data below — login credentials for a test
# account, form data the tests reuse, and so on. Keeping it here means
# every test uses the same values and there is one place to update.
# Example:
# TEST_USER = {"email": "qa@example.com", "password": "..."}
