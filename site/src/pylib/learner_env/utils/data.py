"""utils/data.py - test data generators, mirroring the kit's own copy.

Nothing here touches the browser, which is exactly what makes it a
"util" rather than a helper.
"""

import time


def unique_email():
    """A brand-new email address every call.

    Registration tests need this because the site remembers addresses:
    reuse one and the second run fails with "Email Address already
    exist!" - a real bug in a real suite, caused by a test that was not
    independent.
    """
    return f"student.{int(time.time() * 1000)}@example.com"
