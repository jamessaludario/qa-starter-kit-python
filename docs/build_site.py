"""Build a VitePress-style static documentation site from the single-file guide.

Reads docs/qa-automation-guide.html (the source of truth), splits it into
one page per section, and writes a multi-page site to docs/site/:

  - index.html            (hero landing page with feature cards)
  - <section>.html x 11   (top nav + left sidebar + content + right "On this page" TOC)
  - style.css             (shared stylesheet, light + dark via prefers-color-scheme)

Everything is static HTML/CSS. The one exception is the light/dark
switch: remembering your choice across page loads needs a few lines of
JavaScript (localStorage) since this is a plain multi-page site, not a
single-page app - see THEME_INIT_SCRIPT / THEME_SYNC_SCRIPT below. With
JavaScript disabled the site still works and still follows your OS's
light/dark setting; you just lose the manual override.

Re-run after editing the source guide:

  python docs/build_site.py

The build finishes by opening site/index.html in your default browser.
Pass --no-open to skip that (e.g. when running in CI).
"""

import re
import sys
import webbrowser
from pathlib import Path

DOCS = Path(__file__).parent
SOURCE = DOCS / "qa-automation-guide.html"
OUT = DOCS / "site"

# (section id in source, page title, output file, card emoji, card blurb)
SECTIONS = [
    ("about", "About Playwright", "about-playwright.html", "&#127917;",
     "What Playwright is, why teams choose it, and how it compares to Selenium."),
    ("prereq", "Prerequisites", "prerequisites.html", "&#9989;",
     "Everything to install and know before you start."),
    ("install", "Installation &amp; Setup", "installation.html", "&#128230;",
     "Virtual environments, packages, browsers, and project structure."),
    ("config", "Configurations", "configurations.html", "&#9881;&#65039;",
     "pytest.ini, command-line options, conftest.py, and constants."),
    ("scripts", "Creating Test Scripts", "test-scripts.html", "&#128221;",
     "Your first test, the AAA pattern, and the Page Object Model."),
    ("locators", "Locators", "locators.html", "&#127919;",
     "How to find elements on a page - the heart of automation."),
    ("assertions", "Assertions", "assertions.html", "&#129514;",
     "Web-first expect() checks that wait for the page."),
    ("setup-teardown", "Setup &amp; Teardown", "setup-teardown.html", "&#128260;",
     "pytest fixtures, yield, and fixture scopes."),
    ("categorize", "Categorizing Tests", "categorization.html", "&#127991;&#65039;",
     "Markers, smoke vs regression suites, skip and xfail."),
    ("run-reports", "Running Tests &amp; Reports", "run-reports.html", "&#128202;",
     "pytest commands, HTML reports, and Allure."),
    ("extras", "Additional Info", "additional-info.html", "&#128161;",
     "Debugging tools, flaky tests, good habits, and resources."),
    ("desktop", "Testing Desktop Apps", "desktop-apps.html", "&#128421;&#65039;",
     "Driving native Windows apps with pywinauto, when Playwright can't reach them."),
]

# Sidebar groups, mimicking a docs site's grouped navigation.
SIDEBAR_GROUPS = [
    ("Getting Started", ["about", "prereq", "install", "config"]),
    ("Writing Tests", ["scripts", "locators", "assertions", "setup-teardown"]),
    ("Running Tests", ["categorize", "run-reports", "extras"]),
    # Its own group: this one steps outside the browser entirely.
    ("Beyond the Browser", ["desktop"]),
]

BY_ID = {s[0]: s for s in SECTIONS}


def slugify(text: str) -> str:
    """Turn a heading like 'Use expect() - it waits for you' into a URL anchor."""
    text = re.sub(r"<[^>]+>", "", text)          # strip HTML tags
    text = re.sub(r"&[a-z]+;", " ", text)        # strip entities
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text)   # non-alphanumerics -> hyphens
    return text.strip("-").lower() or "section"


def strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def extract_sections(html: str) -> dict:
    """Return {section_id: (title_html, body_html)} from the single-file guide."""
    sections = {}
    # Section bodies run from each <h2 id=...> to the next divider comment.
    parts = re.split(r"<!-- =+ -->", html)
    for part in parts:
        m = re.search(
            r'<h2 id="([^"]+)"><span class="secno">\d+</span>(.*?)</h2>', part, re.DOTALL
        )
        if not m:
            continue
        sec_id, title = m.group(1), m.group(2).strip()
        body = part[m.end():]
        body = body.split("<footer")[0]                       # last section: drop footer
        body = re.sub(r'<a class="backtop"[^>]*>.*?</a>\s*', "", body, flags=re.DOTALL)
        sections[sec_id] = (title, body.strip())
    return sections


def add_h3_ids(body: str):
    """Give every <h3> an id and return (new_body, [(anchor, label), ...])."""
    toc = []

    def repl(m):
        inner = m.group(1)
        anchor = slugify(inner)
        # De-duplicate anchors within a page (e.g. two similar headings).
        base, n = anchor, 2
        while any(a == anchor for a, _ in toc):
            anchor = f"{base}-{n}"
            n += 1
        toc.append((anchor, strip_tags(inner)))
        return f'<h3 id="{anchor}">{inner}</h3>'

    return re.sub(r"<h3>(.*?)</h3>", repl, body, flags=re.DOTALL), toc


# ------------------------------------------------------------------ templates

# Blocking script placed early in <head>, BEFORE the page paints. If the
# visitor has picked a theme before, this applies it immediately - without
# this, the page would flash the wrong theme for a moment on every
# navigation while the (deferred) THEME_SYNC_SCRIPT catches up.
THEME_INIT_SCRIPT = """<script>
(function () {
  try {
    var t = localStorage.getItem("qa-docs-theme");
    if (t === "light" || t === "dark") {
      document.documentElement.setAttribute("data-theme", t);
    }
  } catch (e) { /* localStorage unavailable (e.g. privacy mode) - ignore */ }
})();
</script>"""

# Runs once the checkbox exists (it's placed right before this script tag).
# Syncs the visible switch to the current theme, and remembers any change
# the visitor makes so it carries over to the next page.
THEME_SYNC_SCRIPT = """<script>
(function () {
  var KEY = "qa-docs-theme";
  var box = document.getElementById("theme-toggle");
  if (!box) return;
  var current = document.documentElement.getAttribute("data-theme");
  if (!current) {
    var prefersDark = window.matchMedia
      && window.matchMedia("(prefers-color-scheme: dark)").matches;
    current = prefersDark ? "dark" : "light";
  }
  box.checked = current === "dark";
  box.addEventListener("change", function () {
    var theme = box.checked ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", theme);
    try { localStorage.setItem(KEY, theme); } catch (e) { /* ignore */ }
  });
})();
</script>"""

# Appended once at the end of <body>, but only on pages that actually have
# a <pre> block - no point shipping it to pages with no code to copy.
COPY_BUTTON_SCRIPT = """<script>
(function () {
  document.querySelectorAll("pre").forEach(function (pre) {
    var code = pre.querySelector("code");
    if (!code) return;
    var btn = document.createElement("button");
    btn.className = "copy-btn"; btn.type = "button"; btn.textContent = "Copy";
    btn.addEventListener("click", function () {
      navigator.clipboard.writeText(code.textContent).then(function () {
        btn.textContent = "Copied!"; btn.classList.add("copied");
        setTimeout(function () { btn.textContent = "Copy"; btn.classList.remove("copied"); }, 1600);
      });
    });
    pre.appendChild(btn);
  });
})();
</script>"""


def top_nav(root: str = "") -> str:
    first = SECTIONS[0][2]
    return f"""
<header class="navbar">
  <a class="brand" href="{root}index.html"><span>QA&nbsp;Automation</span></a>
  <div class="navbar-right">
    <nav class="navlinks">
      <a href="{root}{first}">Guide</a>
      <a href="{root}run-reports.html">Reports</a>
      <a href="https://playwright.dev/python/docs/intro">Playwright&nbsp;Docs</a>
      <a href="https://docs.pytest.org/">pytest&nbsp;Docs</a>
    </nav>
    <!-- Light/dark switch. The checkbox comes before the label so the CSS
         sibling selector (~) can style the label from its checked state. -->
    <input type="checkbox" id="theme-toggle" class="theme-toggle-input">
    <label class="theme-toggle" for="theme-toggle" title="Toggle light / dark theme">
      <span class="icon sun" aria-hidden="true">&#9728;</span>
      <span class="track"><span class="knob"></span></span>
      <span class="icon moon" aria-hidden="true">&#127769;</span>
    </label>
    {THEME_SYNC_SCRIPT}
  </div>
</header>"""


def sidebar(active_id: str) -> str:
    out = ['<aside class="sidebar"><nav>']
    for group, ids in SIDEBAR_GROUPS:
        out.append(f'<p class="group">{group}</p><ul>')
        for sid in ids:
            _, title, fname, _, _ = BY_ID[sid]
            cls = ' class="active"' if sid == active_id else ""
            out.append(f'<li><a{cls} href="{fname}">{title}</a></li>')
        out.append("</ul>")
    out.append("</nav></aside>")
    return "".join(out)


def mobile_nav(active_id: str) -> str:
    """A <details> dropdown menu - works with zero JavaScript."""
    items = []
    for _, title, fname, _, _ in SECTIONS:
        mark = " &#10004;" if BY_ID[active_id][2] == fname else ""
        items.append(f'<li><a href="{fname}">{title}{mark}</a></li>')
    return (
        '<details class="mobile-nav"><summary>Menu &#9662;</summary><ul>'
        + "".join(items)
        + "</ul></details>"
    )


def on_this_page(toc) -> str:
    if not toc:
        return ""
    links = "".join(f'<li><a href="#{a}">{label}</a></li>' for a, label in toc)
    return f'<aside class="toc-right"><p>On this page</p><ul>{links}</ul></aside>'


def prev_next(index: int) -> str:
    cells = []
    if index > 0:
        _, t, f, _, _ = SECTIONS[index - 1]
        cells.append(
            f'<a class="pager prev" href="{f}"><span>Previous page</span><strong>{t}</strong></a>'
        )
    else:
        cells.append("<span></span>")
    if index < len(SECTIONS) - 1:
        _, t, f, _, _ = SECTIONS[index + 1]
        cells.append(
            f'<a class="pager next" href="{f}"><span>Next page</span><strong>{t}</strong></a>'
        )
    else:
        cells.append("<span></span>")
    return f'<div class="pager-row">{cells[0]}{cells[1]}</div>'


def page_html(index: int, title: str, body: str, toc) -> str:
    sid = SECTIONS[index][0]
    copy_script = ("\n" + COPY_BUTTON_SCRIPT) if "<pre>" in body else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{strip_tags(title)} | QA Automation Docs</title>
{THEME_INIT_SCRIPT}
<link rel="stylesheet" href="style.css">
</head>
<body>
{top_nav()}
<div class="layout">
{sidebar(sid)}
<main class="content">
{mobile_nav(sid)}
<h1>{title}</h1>
{body}
{prev_next(index)}
<footer class="page-footer">QA Automation with Playwright &amp; Python - beginner's guide.
Static HTML - no build step required.</footer>
</main>
{on_this_page(toc)}
</div>{copy_script}
</body>
</html>
"""


def index_html() -> str:
    first = SECTIONS[0][2]
    cards = "".join(
        f"""
    <a class="card" href="{fname}">
      <span class="card-icon">{emoji}</span>
      <h3>{title}</h3>
      <p>{blurb}</p>
    </a>"""
        for _, title, fname, emoji, blurb in SECTIONS
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QA Automation Docs | Playwright + Python</title>
{THEME_INIT_SCRIPT}
<link rel="stylesheet" href="style.css">
</head>
<body class="home">
{top_nav()}
<main class="hero-wrap">
  <section class="hero">
    <div class="hero-text">
      <h1><span class="accent">QA Automation</span><br>Documentation</h1>
      <p class="tagline">Learn browser test automation from zero with Playwright,
      Python, and pytest - guides, examples, and best practices.</p>
      <div class="hero-actions">
        <a class="btn primary" href="{first}">Get Started</a>
        <a class="btn ghost" href="run-reports.html">Playwright + pytest</a>
      </div>
    </div>
  </section>
  <section class="cards">{cards}
  </section>
  <footer class="page-footer center">Beginner's guide - static HTML, the only script is the light/dark switch.</footer>
</main>
</body>
</html>
"""


# ------------------------------------------------------------------ stylesheet

CSS = """/* QA Automation Docs — v2 "friendly teal" theme.
   Pure CSS except the theme toggle + code copy buttons (tiny scripts in each page). */
:root {
  --brand: #0e7a70;
  --brand-strong: #0a5f57;
  --brand-soft: #dcf1ee;
  --accent-warm: #e8a13c;
  --bg: #fdfcfa;
  --bg-soft: #f4f2ed;
  --text: #29323a;
  --muted: #64707c;
  --border: #e6e2da;
  --code-bg: #f4f2ed;
  --code-text: #37465e;
  --shadow: 0 1px 2px rgba(41,50,58,.05), 0 10px 28px rgba(41,50,58,.06);
  --nav-h: 64px;
  --radius: 12px;
}
@media (prefers-color-scheme: dark) {
  :root {
    --brand: #4cc8b9;
    --brand-strong: #7adcd0;
    --brand-soft: #113632;
    --accent-warm: #e8b565;
    --bg: #16191d;
    --bg-soft: #1d2126;
    --text: #dde1e4;
    --muted: #949ea8;
    --border: #2e343b;
    --code-bg: #21262c;
    --code-text: #ccd6e3;
    --shadow: none;
  }
}
:root[data-theme="light"] {
  --brand: #0e7a70;
  --brand-strong: #0a5f57;
  --brand-soft: #dcf1ee;
  --accent-warm: #e8a13c;
  --bg: #fdfcfa;
  --bg-soft: #f4f2ed;
  --text: #29323a;
  --muted: #64707c;
  --border: #e6e2da;
  --code-bg: #f4f2ed;
  --code-text: #37465e;
  --shadow: 0 1px 2px rgba(41,50,58,.05), 0 10px 28px rgba(41,50,58,.06);
}
:root[data-theme="dark"] {
  --brand: #4cc8b9;
  --brand-strong: #7adcd0;
  --brand-soft: #113632;
  --accent-warm: #e8b565;
  --bg: #16191d;
  --bg-soft: #1d2126;
  --text: #dde1e4;
  --muted: #949ea8;
  --border: #2e343b;
  --code-bg: #21262c;
  --code-text: #ccd6e3;
  --shadow: none;
}
* { box-sizing: border-box; }
html { scroll-padding-top: calc(var(--nav-h) + 16px); }
body {
  margin: 0;
  font-family: "Segoe UI", "Trebuchet MS", -apple-system, "Helvetica Neue", Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.7;
  font-size: 16.5px;
}
a { color: var(--brand); text-decoration: none; }
a:hover { text-decoration: underline; }
:focus-visible { outline: 2px solid var(--brand); outline-offset: 2px; }

/* ---------------- top navigation bar ---------------- */
.navbar {
  position: fixed; top: 0; left: 0; right: 0; height: var(--nav-h);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 28px;
  background: color-mix(in srgb, var(--bg) 86%, transparent);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
  z-index: 10;
}
.brand {
  display: flex; align-items: center; gap: 10px;
  font-weight: 800; font-size: 1.06rem; color: var(--text);
  letter-spacing: -.01em;
}
.brand::before {
  content: "\\2713";
  display: inline-flex; align-items: center; justify-content: center;
  width: 27px; height: 27px; border-radius: 8px;
  background: var(--brand); color: var(--bg);
  font-size: .95rem; font-weight: 800;
}
.brand:hover { text-decoration: none; }
.navlinks { display: flex; gap: 4px; font-size: .92rem; font-weight: 600; }
.navlinks a { color: var(--muted); padding: 5px 12px; border-radius: 999px; }
.navlinks a:hover { color: var(--brand); background: var(--brand-soft); text-decoration: none; }
.navbar-right { display: flex; align-items: center; gap: 20px; }

/* ---------------- light/dark switch ---------------- */
.theme-toggle-input {
  position: absolute; width: 1px; height: 1px; overflow: hidden;
  clip: rect(0 0 0 0); white-space: nowrap;
}
.theme-toggle {
  display: flex; align-items: center; gap: 6px; cursor: pointer; user-select: none;
}
.theme-toggle .icon { font-size: .85rem; line-height: 1; color: var(--muted); }
.theme-toggle .track {
  position: relative; width: 40px; height: 22px; border-radius: 999px;
  background: var(--border); transition: background .2s ease;
}
.theme-toggle .knob {
  position: absolute; top: 2px; left: 2px; width: 18px; height: 18px;
  border-radius: 50%; background: var(--bg); box-shadow: var(--shadow);
  transition: transform .2s ease;
}
#theme-toggle:checked ~ .theme-toggle .track { background: var(--brand); }
#theme-toggle:checked ~ .theme-toggle .knob { transform: translateX(18px); }
#theme-toggle:focus-visible ~ .theme-toggle .track { outline: 2px solid var(--brand); outline-offset: 2px; }

/* ---------------- three-column layout ---------------- */
.layout {
  display: grid;
  grid-template-columns: 264px minmax(0, 1fr) 224px;
  max-width: 1380px;
  margin: 0 auto;
  padding-top: var(--nav-h);
}
.sidebar {
  border-right: 1px solid var(--border);
  padding: 30px 20px 60px 28px;
  position: sticky; top: var(--nav-h);
  height: calc(100vh - var(--nav-h));
  overflow-y: auto;
  font-size: .93rem;
}
.sidebar .group {
  font-weight: 800; font-size: .74rem; margin: 26px 0 8px;
  color: var(--muted); text-transform: uppercase; letter-spacing: .09em;
}
.sidebar .group:first-child { margin-top: 0; }
.sidebar ul { list-style: none; margin: 0; padding: 0; }
.sidebar li a {
  display: block; padding: 5px 12px; border-radius: 8px;
  color: var(--text); font-weight: 500;
}
.sidebar li a:hover { color: var(--brand); background: var(--bg-soft); text-decoration: none; }
.sidebar li a.active {
  color: var(--brand); font-weight: 700; background: var(--brand-soft);
}
.content {
  padding: 44px 52px 90px;
  min-width: 0;
  max-width: 830px;
}
.toc-right {
  position: sticky; top: var(--nav-h);
  height: calc(100vh - var(--nav-h));
  overflow-y: auto;
  padding: 40px 20px 60px 0;
  font-size: .84rem;
}
.toc-right p {
  font-weight: 800; margin: 0 0 10px; font-size: .74rem;
  text-transform: uppercase; letter-spacing: .09em; color: var(--muted);
}
.toc-right ul { list-style: none; margin: 0; padding: 0; border-left: 2px solid var(--border); }
.toc-right li { line-height: 1.4; }
.toc-right a {
  color: var(--muted); display: block; padding: 5px 0 5px 14px;
  border-left: 2px solid transparent; margin-left: -2px;
}
.toc-right a:hover { color: var(--brand); border-left-color: var(--brand); text-decoration: none; }

/* ---------------- content typography ---------------- */
h1 {
  font-size: 2.15rem; line-height: 1.2; margin: 0 0 16px;
  letter-spacing: -.025em; font-weight: 800;
}
h2 {
  font-size: 1.5rem; margin-top: 48px; padding-top: 24px;
  border-top: 1px solid var(--border); letter-spacing: -.015em; font-weight: 800;
}
h3 { font-size: 1.14rem; margin-top: 34px; font-weight: 800; letter-spacing: -.01em; }
h3::before { content: ""; display: inline-block; width: 8px; height: 8px; border-radius: 3px; background: var(--brand); margin-right: 9px; vertical-align: 2px; }
p { margin: 12px 0; text-wrap: pretty; }
ul li, ol li { margin: 5px 0; }
strong { font-weight: 700; }

code {
  font-family: ui-monospace, "Cascadia Code", Consolas, Menlo, monospace;
  background: var(--code-bg);
  border-radius: 5px;
  padding: 2px 6px;
  font-size: .84em;
  color: var(--code-text);
}
pre {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 18px;
  overflow-x: auto;
  line-height: 1.6;
  position: relative;
}
pre code { background: none; border: none; padding: 0; font-size: .85rem; }
.copy-btn {
  position: absolute; top: 8px; right: 8px;
  border: 1px solid var(--border); border-radius: 7px;
  background: var(--bg); color: var(--muted);
  font: 600 .72rem "Segoe UI", sans-serif;
  padding: 4px 10px; cursor: pointer;
  opacity: 0; transition: opacity .15s ease;
}
pre:hover .copy-btn, .copy-btn:focus-visible { opacity: 1; }
.copy-btn:hover { color: var(--brand); border-color: var(--brand); }
.copy-btn.copied { color: var(--brand); border-color: var(--brand); opacity: 1; }
.filename {
  display: inline-block;
  background: var(--brand);
  color: var(--bg);
  font-family: ui-monospace, "Cascadia Code", Consolas, Menlo, monospace;
  font-size: .76rem;
  border-radius: 8px 8px 0 0;
  padding: 3px 14px;
  margin-bottom: -8px;
  position: relative; z-index: 1;
}

/* ---------------- callouts ---------------- */
.tip, .warn, .note {
  border-radius: var(--radius); padding: 15px 18px 15px 46px; margin: 20px 0;
  font-size: .95rem; position: relative;
}
.tip strong:first-child, .warn strong:first-child, .note strong:first-child {
  display: block; margin-bottom: 4px;
}
.tip::before, .warn::before, .note::before {
  position: absolute; left: 16px; top: 15px;
  font-weight: 800; font-size: .9rem; line-height: 1.6;
}
.tip  { background: color-mix(in srgb, #10b981 9%, var(--bg)); }
.tip::before { content: "\\2713"; color: #0d9573; }
.tip strong:first-child { color: #0d9573; }
.warn { background: color-mix(in srgb, var(--accent-warm) 12%, var(--bg)); }
.warn::before { content: "!"; color: #c07f1d; }
.warn strong:first-child { color: #c07f1d; }
.note { background: var(--brand-soft); }
.note::before { content: "i"; color: var(--brand); font-family: Georgia, serif; font-style: italic; }
.note strong:first-child { color: var(--brand); }
:root[data-theme="dark"] .tip::before, :root[data-theme="dark"] .tip strong:first-child { color: #34d399; }
:root[data-theme="dark"] .warn::before, :root[data-theme="dark"] .warn strong:first-child { color: var(--accent-warm); }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .tip::before, :root:not([data-theme="light"]) .tip strong:first-child { color: #34d399; }
  :root:not([data-theme="light"]) .warn::before, :root:not([data-theme="light"]) .warn strong:first-child { color: var(--accent-warm); }
}

/* ---------------- tables ---------------- */
.tablewrap {
  overflow-x: auto; margin: 20px 0;
  border: 1px solid var(--border); border-radius: var(--radius);
}
table { border-collapse: collapse; width: 100%; font-size: .9rem; }
th, td { padding: 10px 14px; text-align: left; vertical-align: top; border-bottom: 1px solid var(--border); }
tr:last-child td { border-bottom: none; }
th {
  background: var(--bg-soft); font-size: .78rem; text-transform: uppercase;
  letter-spacing: .06em; color: var(--muted);
}
td code { white-space: nowrap; }

/* ---------------- prev / next pager ---------------- */
.pager-row {
  display: grid; grid-template-columns: 1fr 1fr; gap: 14px;
  margin-top: 56px;
}
.pager {
  display: block; border: 1px solid var(--border); border-radius: var(--radius);
  padding: 14px 18px; color: var(--text);
  transition: border-color .15s ease, box-shadow .15s ease;
}
.pager:hover { border-color: var(--brand); text-decoration: none; box-shadow: var(--shadow); }
.pager span { display: block; font-size: .76rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: .06em; }
.pager strong { color: var(--brand); font-weight: 700; }
.pager.next { text-align: right; }

.page-footer {
  margin-top: 48px; padding-top: 18px; border-top: 1px solid var(--border);
  color: var(--muted); font-size: .82rem;
}
.page-footer.center { text-align: center; border: none; }

/* ---------------- mobile menu (pure-CSS details dropdown) ---------------- */
.mobile-nav { display: none; }

/* ---------------- landing page ---------------- */
.home { background: var(--bg); }
.hero-wrap { padding: var(--nav-h) 24px 70px; max-width: 1160px; margin: 0 auto; }
.hero {
  display: flex; flex-direction: column; align-items: center; text-align: center;
  gap: 8px; padding: 84px 8px 60px;
  background:
    radial-gradient(46% 64% at 32% 18%, var(--brand-soft) 0%, transparent 70%),
    radial-gradient(36% 52% at 74% 40%, color-mix(in srgb, var(--accent-warm) 16%, transparent) 0%, transparent 70%);
}
.hero-text h1 { font-size: 3.3rem; line-height: 1.08; margin: 0 0 18px; letter-spacing: -.03em; font-weight: 800; }
.hero-text .accent { color: var(--brand); }
.tagline { font-size: 1.18rem; color: var(--muted); max-width: 480px; margin: 0 auto 28px; }
.hero-actions { display: flex; gap: 14px; justify-content: center; }
.btn {
  display: inline-block; border-radius: 999px; padding: 11px 28px;
  font-weight: 700; font-size: .97rem; white-space: nowrap;
  transition: transform .12s ease, box-shadow .12s ease;
}
.btn:hover { text-decoration: none; transform: translateY(-1px); }
.btn.primary { background: var(--brand); color: var(--bg); box-shadow: var(--shadow); }
.btn.primary:hover { background: var(--brand-strong); }
.btn.ghost { border: 1.5px solid var(--brand); color: var(--brand); }
.btn.ghost:hover { background: var(--brand-soft); }

.cards {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px;
  margin-top: 28px;
}
.card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 22px 22px 18px;
  color: var(--text);
  transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
}
.card:hover {
  border-color: var(--brand); text-decoration: none;
  transform: translateY(-3px); box-shadow: var(--shadow);
}
.card-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 46px; height: 46px; border-radius: 12px;
  background: var(--brand-soft); border: 1px solid var(--border);
  font-size: 1.35rem;
}
.card h3 { margin: 14px 0 6px; font-size: 1.03rem; }
.card h3::before { display: none; }
.card p { margin: 0; font-size: .89rem; color: var(--muted); }

/* ---------------- responsive ---------------- */
@media (max-width: 1180px) {
  .layout { grid-template-columns: 250px minmax(0, 1fr); }
  .toc-right { display: none; }
}
@media (max-width: 880px) {
  .layout { grid-template-columns: minmax(0, 1fr); }
  .sidebar { display: none; }
  .content { padding: 28px 22px 60px; }
  .navlinks { gap: 4px; font-size: .85rem; }
  .mobile-nav {
    display: block; margin-bottom: 18px;
    border: 1px solid var(--border); border-radius: 10px;
    background: var(--bg-soft);
  }
  .mobile-nav summary {
    cursor: pointer; padding: 10px 14px; font-weight: 700; list-style: none;
  }
  .mobile-nav ul { list-style: none; margin: 0; padding: 4px 14px 12px; }
  .mobile-nav li { margin: 6px 0; }
  .hero { padding-top: 44px; }
  .hero-text h1 { font-size: 2.3rem; }
  .cards { grid-template-columns: 1fr; }
  .pager-row { grid-template-columns: 1fr; }
}
"""


def main():
    html = SOURCE.read_text(encoding="utf-8")
    sections = extract_sections(html)

    missing = [s[0] for s in SECTIONS if s[0] not in sections]
    if missing:
        raise SystemExit(f"ERROR: sections not found in source guide: {missing}")

    OUT.mkdir(exist_ok=True)
    (OUT / "style.css").write_text(CSS, encoding="utf-8")
    (OUT / "index.html").write_text(index_html(), encoding="utf-8")

    for i, (sid, _, fname, _, _) in enumerate(SECTIONS):
        title, body = sections[sid]
        body, toc = add_h3_ids(body)
        (OUT / fname).write_text(page_html(i, title, body, toc), encoding="utf-8")
        print(f"  wrote site/{fname}")

    index_path = OUT / "index.html"
    print(f"Done. Open {index_path} in a browser.")

    if "--no-open" not in sys.argv:
        # Open the freshly built docs automatically, so there's nothing extra
        # to remember - skip with --no-open (e.g. when running in CI).
        webbrowser.open(index_path.resolve().as_uri())


if __name__ == "__main__":
    main()
