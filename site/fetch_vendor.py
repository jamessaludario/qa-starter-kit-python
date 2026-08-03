"""Download the third-party runtime files the quest site serves itself.

The site must not call a third-party CDN at runtime (offline-first, and a
CDN outage should never break a lesson). So we fetch Pyodide once, into
site/vendor/, and the build copies it into dist/. vendor/ is git-ignored:
~16 MB of WebAssembly does not belong in a teaching repo's history.

    python site/fetch_vendor.py            # fetch if missing
    python site/fetch_vendor.py --force    # re-fetch even if present

Everything here is stdlib only - no pip install, on purpose.
"""

import hashlib
import sys
import urllib.request
from pathlib import Path

SITE = Path(__file__).parent
VENDOR = SITE / "vendor"

# Pin an exact version. An unpinned "latest" would silently change the
# Python running the learner's code between two builds of the same site.
PYODIDE_VERSION = "0.28.3"
PYODIDE_BASE = f"https://cdn.jsdelivr.net/pyodide/v{PYODIDE_VERSION}/full/"

# Only the core runtime. We deliberately do NOT fetch the package bundle
# (numpy, pandas, ...): the lessons need `ast` and `time`, both of which
# live in python_stdlib.zip, and skipping packages saves ~100 MB.
PYODIDE_FILES = [
    "pyodide.js",           # the loader (UMD - defines globalThis.loadPyodide)
    "pyodide.asm.js",       # the Emscripten glue
    "pyodide.asm.wasm",     # CPython itself, compiled to WebAssembly
    "python_stdlib.zip",    # the standard library
    "pyodide-lock.json",    # package index; loadPyodide reads it at startup
]


def fetch(url: str, target: Path) -> int:
    """Download one file, writing it whole only once it arrived intact."""
    with urllib.request.urlopen(url, timeout=120) as response:
        data = response.read()
    # Write to a temp name first, then rename: an interrupted download
    # must never leave a half-file that looks like a good cached copy.
    temp = target.with_suffix(target.suffix + ".part")
    temp.write_bytes(data)
    temp.replace(target)
    return len(data)


def main() -> int:
    force = "--force" in sys.argv
    out = VENDOR / "pyodide"
    out.mkdir(parents=True, exist_ok=True)

    print(f"Pyodide {PYODIDE_VERSION} -> {out}")
    total = 0
    for name in PYODIDE_FILES:
        target = out / name
        if target.exists() and not force:
            size = target.stat().st_size
            total += size
            print(f"  cached  {name:22} {size / 1024:9.0f} KB")
            continue
        try:
            size = fetch(PYODIDE_BASE + name, target)
        except Exception as error:                       # noqa: BLE001
            print(f"  FAILED  {name}: {error}")
            print("\nNo network? The site still builds; it will show an honest")
            print("'Python runtime not available' message instead of an editor.")
            return 1
        total += size
        print(f"  fetched {name:22} {size / 1024:9.0f} KB")

    # A tiny manifest so the build (and a curious learner) can see exactly
    # what is being served, without trusting the folder to be complete.
    lines = [f"pyodide {PYODIDE_VERSION}", f"source {PYODIDE_BASE}", ""]
    for name in PYODIDE_FILES:
        blob = (out / name).read_bytes()
        digest = hashlib.sha256(blob).hexdigest()[:16]
        lines.append(f"{digest}  {len(blob):>10}  {name}")
    (VENDOR / "MANIFEST.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\nTotal {total / 1024 / 1024:.1f} MB. Manifest: site/vendor/MANIFEST.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
