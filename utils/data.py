"""
utils/data.py
=============
Small standalone tools for generating test data. Nothing in here touches
the browser — that's what makes it a "util" rather than a helper.
"""

import time


def unique_email():
    """
    Return a brand-new email address every run, e.g.
    "student.1720855555123@example.com".

    We need this because the site remembers registered emails — if we
    reused the same address, the test would fail on its second run with
    "Email Address already exist!". time.time() is the current time in
    seconds, so the number is different every millisecond.
    """
    return f"student.{int(time.time() * 1000)}@example.com"
