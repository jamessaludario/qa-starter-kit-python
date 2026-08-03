"""Build the Quest for Automation site from content/ and src/ into dist/.

Same spirit as docs/build_site.py: plain Python, no dependencies, no npm,
readable top to bottom. The difference is what it compiles:

    content/game.json          XP curve, levels, badges
    content/about.md           the About page
    content/zones/<n>/         zone.json + lesson.md + challenges/*.json
    src/                       the app itself (CSS, ES modules, mock shop)
    src/pylib/                 the Playwright shim, rubric and harness
    vendor/pyodide/            the Python runtime (see fetch_vendor.py)

...into dist/, a folder of static files you can drop on GitHub Pages.

    python site/build_site.py               build, serve, open a browser
    python site/build_site.py --no-open     build and serve, stay quiet
    python site/build_site.py --build-only  just write dist/

The site needs a real HTTP server (WebAssembly will not load over
file://), which is why serving is the default rather than an extra step.
"""

import hashlib
import html
import http.server
import json
import re
import shutil
import socketserver
import sys
import webbrowser
from functools import partial
from pathlib import Path

SITE = Path(__file__).parent
CONTENT = SITE / "content"
SRC = SITE / "src"
VENDOR = SITE / "vendor"
DIST = SITE / "dist"

REQUIRED_ZONE_KEYS = ["id", "order", "title", "tagline"]
REQUIRED_CHALLENGE_KEYS = ["id", "title", "kind", "xp"]


# ---------------------------------------------------------------- markdown

FENCE = re.compile(r"^```(\w*)\s*$")
CALLOUT = re.compile(r"^:::(tip|warn|note)\s*(.*)$")


def inline(text: str) -> str:
    """Inline markdown. Order matters: code first, so `**x**` inside
    backticks is left alone."""
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            out.append(f"<code>{html.escape(part[1:-1])}</code>")
            continue
        piece = html.escape(part)
        piece = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', piece)
        piece = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", piece)
        piece = re.sub(r"(?<![*\w])\*([^*]+)\*(?!\w)", r"<em>\1</em>", piece)
        out.append(piece)
    return "".join(out)


def markdown(text: str) -> str:
    """A deliberately small Markdown subset: headings, paragraphs, lists,
    fenced code, and :::tip callouts. Enough to author a lesson, small
    enough to read."""
    lines = text.replace("\r\n", "\n").split("\n")
    out = []
    index = 0
    list_tag = None

    def close_list():
        nonlocal list_tag
        if list_tag:
            out.append(f"</{list_tag}>")
            list_tag = None

    while index < len(lines):
        line = lines[index]

        fence = FENCE.match(line)
        if fence:
            close_list()
            index += 1
            body = []
            while index < len(lines) and not FENCE.match(lines[index]):
                body.append(lines[index])
                index += 1
            index += 1
            language = fence.group(1) or "text"
            out.append(f'<pre class="lang-{language}"><code>'
                       f"{html.escape(chr(10).join(body))}</code></pre>")
            continue

        callout = CALLOUT.match(line)
        if callout:
            close_list()
            kind, title = callout.group(1), callout.group(2)
            index += 1
            body = []
            while index < len(lines) and not lines[index].startswith(":::"):
                body.append(lines[index])
                index += 1
            index += 1
            heading = f"<strong>{inline(title)}</strong>" if title else ""
            out.append(f'<div class="callout {kind}">{heading}'
                       f"{markdown(chr(10).join(body))}</div>")
            continue

        if not line.strip():
            close_list()
            index += 1
            continue

        heading = re.match(r"^(#{2,4})\s+(.*)$", line)
        if heading:
            close_list()
            level = len(heading.group(1))
            out.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            index += 1
            continue

        bullet = re.match(r"^[-*]\s+(.*)$", line)
        number = re.match(r"^\d+\.\s+(.*)$", line)
        if bullet or number:
            wanted = "ul" if bullet else "ol"
            if list_tag != wanted:
                close_list()
                out.append(f"<{wanted}>")
                list_tag = wanted
            out.append(f"<li>{inline((bullet or number).group(1))}</li>")
            index += 1
            continue

        close_list()
        paragraph = [line]
        index += 1
        while index < len(lines) and lines[index].strip() and \
                not FENCE.match(lines[index]) and not lines[index].startswith(":::") and \
                not re.match(r"^(#{2,4}\s|[-*]\s|\d+\.\s)", lines[index]):
            paragraph.append(lines[index])
            index += 1
        out.append(f"<p>{inline(' '.join(part.strip() for part in paragraph))}</p>")

    close_list()
    return "".join(out)


# ----------------------------------------------------------------- content

def load_challenge(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = [key for key in REQUIRED_CHALLENGE_KEYS if key not in data]
    if missing:
        raise SystemExit(f"ERROR: {path} is missing {missing}")
    # Prose is authored as Markdown and rendered here, so a lesson author
    # never writes HTML and the runtime never ships a Markdown parser.
    for key in ("brief", "reveal"):
        if data.get(key):
            data[key] = markdown(data[key])
    for question in data.get("questions", []):
        question["prompt"] = markdown(question["prompt"])
    return data


def load_zone(folder: Path) -> dict:
    zone = json.loads((folder / "zone.json").read_text(encoding="utf-8"))
    missing = [key for key in REQUIRED_ZONE_KEYS if key not in zone]
    if missing:
        raise SystemExit(f"ERROR: {folder/'zone.json'} is missing {missing}")

    lesson = folder / "lesson.md"
    zone["lesson"] = markdown(lesson.read_text(encoding="utf-8")) if lesson.exists() else ""

    challenges_dir = folder / "challenges"
    files = sorted(challenges_dir.glob("*.json")) if challenges_dir.exists() else []
    zone["challenges"] = [load_challenge(path) for path in files]
    zone.setdefault("map", {"x": 50, "y": 50})
    zone.setdefault("objectives", [])
    zone.setdefault("requires", [])
    return zone


# Measured, not guessed. At the narrowest width the map is drawn at
# (1100px, see app.css) a zone card is 210px wide in a ~1040px board and
# up to 175px tall in a 660px board - about 20% x 27% of the map. Two
# cards closer than that in BOTH axes visibly overlap, so these
# thresholds sit just above the real card, leaving room for a tagline
# that wraps onto a third line.
MIN_MAP_GAP_X = 22
MIN_MAP_GAP_Y = 29


def check_map_spacing(zones: list):
    """Refuse to build a map whose zone cards would sit on top of each other.

    Zone positions are hand-authored percentages, which is lovely until
    somebody adds the thirteenth zone and discovers the overlap by
    screenshot. Failing the build names both zones and the fix.
    """
    clashes = []
    for index, first in enumerate(zones):
        for second in zones[index + 1:]:
            gap_x = abs(first["map"]["x"] - second["map"]["x"])
            gap_y = abs(first["map"]["y"] - second["map"]["y"])
            if gap_x < MIN_MAP_GAP_X and gap_y < MIN_MAP_GAP_Y:
                clashes.append(
                    f"  '{first['id']}' at ({first['map']['x']},{first['map']['y']}) "
                    f"and '{second['id']}' at ({second['map']['x']},{second['map']['y']})"
                    f" - only {gap_x} apart in x and {gap_y} in y"
                )
    if clashes:
        raise SystemExit(
            "ERROR: these zone cards would overlap on the quest map:\n"
            + "\n".join(clashes)
            + f"\nMove one of each pair: centres need to differ by at least "
            f"{MIN_MAP_GAP_X} in x OR {MIN_MAP_GAP_Y} in y.\n"
            "The map is laid out as a serpentine - see site/CONTRIBUTING-CONTENT.md."
        )


def load_content() -> dict:
    game = json.loads((CONTENT / "game.json").read_text(encoding="utf-8"))
    zones = [load_zone(folder) for folder in sorted(CONTENT.glob("zones/*")) if folder.is_dir()]
    zones.sort(key=lambda zone: zone["order"])

    known = {zone["id"] for zone in zones}
    for zone in zones:
        unknown = [need for need in zone["requires"] if need not in known]
        if unknown:
            raise SystemExit(f"ERROR: zone '{zone['id']}' requires unknown zone(s) {unknown}")

    check_map_spacing(zones)

    about = (CONTENT / "about.md")
    return {
        "game": game,
        "zones": zones,
        "about": markdown(about.read_text(encoding="utf-8")) if about.exists() else "",
    }


def collect_pylib() -> dict:
    """The Python that runs inside Pyodide, embedded as one JS file.

    One request instead of a dozen, and it means the shim is available
    the moment the runtime starts - including offline, before the
    service worker has seen those paths.
    """
    files = {}
    for path in sorted((SRC / "pylib").rglob("*.py")):
        relative = path.relative_to(SRC / "pylib").as_posix()
        files[relative] = path.read_text(encoding="utf-8")
    return files


# ---------------------------------------------------------------- the page

def index_html(build_id: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Quest for Automation | Learn Playwright + pytest by playing</title>
<meta name="description" content="A gamified, browser-based adventure that
teaches Playwright and pytest. Write real Python, watch it drive a real shop,
earn XP. No install, no account.">
<link rel="stylesheet" href="app.css?v={build_id}">
<link rel="icon" href="data:image/svg+xml,&lt;svg xmlns='http://www.w3.org/2000/svg'
 viewBox='0 0 16 16'&gt;&lt;text y='14' font-size='14'&gt;&#9650;&lt;/text&gt;&lt;/svg&gt;">
</head>
<body>
<a class="sr-only" href="#main">Skip to content</a>
<div id="app"></div>
<div id="live-region" class="sr-only" role="status" aria-live="polite"></div>

<noscript>
  <p style="padding:24px">This quest runs entirely in your browser, so it needs
  JavaScript. The same material is available as a written guide in
  <code>docs/qa-automation-guide.html</code> and as a terminal tour
  (<code>python tour.py</code>).</p>
</noscript>

<!-- Content and the Python sources are plain data, generated by
     site/build_site.py. Loading them before the app means no fetch and
     no loading flash. -->
<script src="content.js?v={build_id}"></script>
<script src="pylib.js?v={build_id}"></script>
<script type="module" src="js/main.js?v={build_id}"></script>
</body>
</html>
"""


# ------------------------------------------------------------------- build

def copy_tree(source: Path, target: Path, skip=()):
    for path in source.rglob("*"):
        if path.is_dir():
            continue
        relative = path.relative_to(source)
        if relative.parts and relative.parts[0] in skip:
            continue
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Skip files that have not changed: the vendored runtime alone is
        # 11 MB, and a build should not take a second to do nothing.
        if destination.exists() and destination.stat().st_mtime >= path.stat().st_mtime \
                and destination.stat().st_size == path.stat().st_size:
            continue
        shutil.copy2(path, destination)


def build() -> str:
    content = load_content()
    pylib = collect_pylib()

    payload = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
    build_id = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:10]

    DIST.mkdir(exist_ok=True)
    # src/, minus the Python sources, which are embedded instead.
    copy_tree(SRC, DIST, skip=("pylib",))

    (DIST / "content.js").write_text(
        "/* Generated by site/build_site.py - do not edit. */\n"
        f"window.QUEST_CONTENT = {payload};\n", encoding="utf-8")
    (DIST / "pylib.js").write_text(
        "/* Generated by site/build_site.py from site/src/pylib/. */\n"
        f"window.QUEST_PYLIB = {json.dumps(pylib, ensure_ascii=False)};\n",
        encoding="utf-8")
    (DIST / "index.html").write_text(index_html(build_id), encoding="utf-8")
    (DIST / "sw.js").write_text(
        (SRC / "sw.js").read_text(encoding="utf-8").replace("__BUILD_ID__", build_id),
        encoding="utf-8")

    pyodide = VENDOR / "pyodide"
    if pyodide.exists():
        copy_tree(pyodide, DIST / "vendor" / "pyodide")
    else:
        print("  WARNING: site/vendor/pyodide is missing - coding challenges will")
        print("           not run. Fix it with: python site/fetch_vendor.py")

    zones = content["zones"]
    built = sum(len(zone["challenges"]) for zone in zones)
    ready = [zone for zone in zones if zone["challenges"]]
    print(f"  {len(zones)} zones ({len(ready)} with content), {built} challenges")
    print(f"  {len(pylib)} Python files embedded for the browser runtime")
    print(f"  build id {build_id} -> {DIST}")
    return build_id


PREFERRED_PORT = 8000


def open_server(handler):
    """Bind port 8000, or the next thing the OS will give us.

    Something is often already on 8000 - another copy of this script, a
    dev server, a leftover from an editor. Falling back beats greeting a
    learner with a WinError 10048 traceback for a problem that is not
    theirs and not interesting.
    """
    try:
        return socketserver.TCPServer(("127.0.0.1", PREFERRED_PORT), handler)
    except OSError:
        # Port 0 = "any free port"; the OS picks and tells us which.
        server = socketserver.TCPServer(("127.0.0.1", 0), handler)
        print(f"  (port {PREFERRED_PORT} is busy - using "
              f"{server.server_address[1]} instead)")
        return server


def serve(open_browser: bool):
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
    with open_server(handler) as httpd:
        url = f"http://127.0.0.1:{httpd.server_address[1]}/"
        print(f"\nServing {DIST} at {url}  (Ctrl+C to stop)")
        if open_browser:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


def main():
    print("Building the Quest for Automation site...")
    build()
    if "--build-only" in sys.argv:
        return
    serve(open_browser="--no-open" not in sys.argv)


if __name__ == "__main__":
    main()
