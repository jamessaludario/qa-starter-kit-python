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
import re
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


# --------------------------------------------------------------------------
# Fonts
# --------------------------------------------------------------------------

# IBM Plex, the three families the design is built on: a serif for
# headings and lesson prose, a mono for the small uppercase labels and
# all code, a sans for the interface.
#
# LATIN SUBSETS ONLY. Google serves this family in 38 slices (Cyrillic,
# Greek, Vietnamese, ...) totalling ~700 KB; the seven Latin ones are
# ~113 KB, and Plex Sans is a variable font so its three weights are one
# file. Everything is font-display:swap, so text paints immediately in
# the fallback stack and swaps when the font lands - fonts must never be
# the reason a lesson is blank.
#
# Optional by design: skip this and the site uses the system stack. It
# looks plainer and works identically.
FONT_CSS = (
    "https://fonts.googleapis.com/css2?"
    "family=IBM+Plex+Mono:wght@400;600"
    "&family=IBM+Plex+Sans:wght@400;600;700"
    "&family=IBM+Plex+Serif:wght@400;600"
    "&display=swap"
)
# Without a browser-shaped User-Agent Google returns TrueType instead of
# woff2, which is roughly three times the bytes for the same glyphs.
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
FACE = re.compile(r"/\*\s*([\w\-\[\]]+)\s*\*/\s*@font-face\s*\{(.*?)\}", re.DOTALL)


def get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def fetch_fonts(out: Path, force: bool) -> int:
    """Vendor the Latin IBM Plex faces and a stylesheet pointing at them."""
    out.mkdir(parents=True, exist_ok=True)
    css = get(FONT_CSS).decode("utf-8")

    rules = []
    seen = {}
    total = 0
    for subset, body in FACE.findall(css):
        if subset != "latin":
            continue
        family = re.search(r"font-family:\s*'([^']+)'", body).group(1)
        weight = re.search(r"font-weight:\s*(\d+)", body).group(1)
        remote = re.search(r"url\(([^)]+)\)", body).group(1)

        # Plex Sans is variable: one file serves 400, 600 and 700, so
        # key the download on the URL and let the weights share it.
        name = seen.get(remote)
        if name is None:
            name = f"{family.replace(' ', '')}-{weight}.woff2"
            seen[remote] = name
            target = out / name
            if target.exists() and not force:
                total += target.stat().st_size
                print(f"  cached  {name:26} {target.stat().st_size / 1024:8.0f} KB")
            else:
                blob = get(remote)
                target.write_bytes(blob)
                total += len(blob)
                print(f"  fetched {name:26} {len(blob) / 1024:8.0f} KB")

        rules.append(
            f"@font-face{{font-family:'{family}';font-style:normal;"
            f"font-weight:{weight};font-display:swap;"
            f"src:url('{name}') format('woff2');}}"
        )

    (out / "fonts.css").write_text(
        "/* Vendored by site/fetch_vendor.py - do not edit. IBM Plex is\n"
        "   licensed under the SIL Open Font License 1.1. */\n"
        + "\n".join(rules) + "\n",
        encoding="utf-8")
    return total


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

    # Fonts are a nice-to-have, so a failure here is a warning, not an
    # exit code: the site falls back to the system stack and works.
    print(f"\nIBM Plex (Latin subsets) -> {VENDOR / 'fonts'}")
    try:
        total += fetch_fonts(VENDOR / "fonts", force)
    except Exception as error:                           # noqa: BLE001
        print(f"  SKIPPED: {error}")
        print("  The site will use the system font stack instead.")

    print(f"\nTotal {total / 1024 / 1024:.1f} MB. Manifest: site/vendor/MANIFEST.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
