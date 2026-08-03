"""The `playwright` package as the learner's code sees it.

This directory is only on sys.path inside Pyodide, never in CPython, so
it can safely share a name with the real Playwright package. Its whole
job is to make this line work in the browser:

    from playwright.sync_api import Page, expect

...which is the same line the kit's learn/ tests use, so a solution
written here runs unchanged against a real browser.
"""
