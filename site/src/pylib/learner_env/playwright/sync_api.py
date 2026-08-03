"""Re-export of the shim under the name learners will use everywhere else."""

from playwright_lite.sync_api import (
    Error,
    Locator,
    LocatorAssertions,
    Page,
    PageAssertions,
    TimeoutError,
    expect,
)

__all__ = [
    "Error", "Locator", "LocatorAssertions", "Page", "PageAssertions",
    "TimeoutError", "expect",
]
