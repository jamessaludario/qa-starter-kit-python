"""
utils/data.py
=============
Small standalone tools for generating test data. Nothing in here touches
the browser — that's what makes it a "util" rather than a helper.
"""

import time


def unique_email(domain="example.com"):
    """
    Return a brand-new email address every run, e.g.
    "qa.1720855555123@example.com". Use it whenever your app remembers
    registered emails — reusing an address makes reruns fail.
    """
    return f"qa.{int(time.time() * 1000)}@{domain}"


def unique_name(prefix="qa"):
    """A unique short name, e.g. "qa-1720855555123" — handy for records
    your tests create, so runs never collide with each other."""
    return f"{prefix}-{int(time.time() * 1000)}"
