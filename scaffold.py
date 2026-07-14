"""
scaffold.py — create a test project for YOUR web app
====================================================
Run it from the starter kit folder:

    python scaffold.py

It asks two questions (project name, app URL) and creates a fresh,
independent test project NEXT TO the kit folder:

    ../<project-name>-tests/

The new folder has the full structure (pages/, helpers/, tests/, ...),
a smoke test that should pass immediately, the AI prompts, and a .env
already filled in with your answers. The starter kit itself is never
modified — scaffold as many projects as you like.

Non-interactive use:

    python scaffold.py --name my-app --url https://my-app.example.com
    python scaffold.py --name my-app --url http://localhost:3000 --dest C:/work/my-app-tests
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

KIT = Path(__file__).parent
TEMPLATE = KIT / "template"
PROMPTS = KIT / "prompts"


def ask(question, default=None):
    suffix = f" [{default}]" if default else ""
    try:
        answer = input(f"  {question}{suffix}: ").strip()
    except EOFError:
        answer = ""
    return answer or default or ""


def main():
    parser = argparse.ArgumentParser(description="Scaffold a new test project")
    parser.add_argument("--name", help="short project name, e.g. my-app")
    parser.add_argument("--url", help="the app's address, e.g. https://my-app.example.com")
    parser.add_argument("--dest", help="where to create the project (default: ../<name>-tests)")
    options = parser.parse_args()

    print()
    print("  QA STARTER KIT - scaffold a test project for your web app")
    print()

    name = options.name or ask("Project name (short, no spaces)", "my-app")
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-") or "my-app"

    url = options.url or ask("Your app's URL", "http://localhost:3000")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    dest = Path(options.dest) if options.dest else KIT.parent / f"{name}-tests"
    if dest.exists() and any(dest.iterdir()):
        sys.exit(f"\n  {dest} already exists and is not empty - not touching it.")

    # 1. Copy the template (the project skeleton)...
    shutil.copytree(TEMPLATE, dest, dirs_exist_ok=True)

    # 2. ...and the AI prompts.
    shutil.copytree(PROMPTS, dest / "prompts", dirs_exist_ok=True)

    # 3. Write the .env with the answers (the template's .env.example
    #    stays too, as documentation).
    (dest / ".env").write_text(
        f"PROJECT_NAME={name}\nBASE_URL={url}\n", encoding="utf-8"
    )

    # 4. Personalize the README.
    readme = dest / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace("{{PROJECT_NAME}}", name),
        encoding="utf-8",
    )

    print(f"""
  Created: {dest}

  Next steps:

    cd {dest}
    pip install -r requirements.txt   (skip if already installed)
    playwright install chromium       (skip if already installed)
    pytest tests/test_smoke.py        <- should pass immediately

  Then grow the suite:

    - With an AI agent: open the folder in your agent and feed it
      prompts/00-quick-start.md  (conventions live in CLAUDE.md)
    - By hand: copy pages/example_page.py.template and go

  Happy testing!""")


if __name__ == "__main__":
    main()
