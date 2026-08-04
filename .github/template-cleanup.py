"""Turn a fresh "Use this template" copy into a clean test project.

GitHub's template feature copies a repository WHOLE. There is no way to
mark a folder as "template only", so a new copy arrives carrying the
entire learning kit: the 26 commented practice tests, the quest site,
the guide, the desktop track and the tour. None of that belongs in a
suite for somebody's own app.

So the exclusion happens after the copy instead of during it. This
script promotes template/ - the generic, app-agnostic skeleton - to the
repository root and deletes everything that exists only to teach. What
it leaves behind is exactly what `python scaffold.py` produces, because
that is the one definition of "a clean project" this repo has and two
definitions would drift apart within a month.

    .github/workflows/template-cleanup.yml runs this automatically on
    the first push to a generated repo, commits the result, and removes
    itself. Nothing to remember.

If Actions are disabled, or you cloned rather than templated, run it by
hand from the repository root:

    python .github/template-cleanup.py --yes

It refuses to do anything without --yes, so nobody deletes their
checkout of the learning kit by opening the wrong file.
"""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "template"

# A KEEP list, not a delete list, and that direction is the whole point.
#
# A delete list has to name every piece of learning material, so the day
# somebody adds a fourth track and forgets to add a line here, it
# silently ships to everyone's project. With a keep list the same
# mistake deletes the new folder instead - annoying, obvious, and caught
# the first time anyone looks. The failure mode should be a missing
# folder, never a leaked one.
#
# `template` is handled separately: it is promoted, not kept.
KEEP_AT_ROOT = {
    ".git",        # not ours to touch
    ".github",     # pruned below - the kit's CI goes, the template's arrives
    "prompts",     # the AI prompts, which a real project does want
    "template",
}

# This script and the workflow that calls it, removed last of all.
SELF = [
    ".github/template-cleanup.py",
    ".github/workflows/template-cleanup.yml",
]


def remove(relative: str) -> bool:
    """Delete a file or folder under the repo root. Missing is fine."""
    target = ROOT / relative
    if not target.exists():
        return False
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()
    return True


def promote_template() -> int:
    """Move template/* up to the repository root, dotfiles included."""
    moved = 0
    for source in sorted(TEMPLATE.iterdir()):
        destination = ROOT / source.name
        # The learning versions are already gone by this point, but a
        # merge is still needed for .github/, which the template also
        # ships a workflow into.
        if source.is_dir() and destination.exists():
            for item in source.rglob("*"):
                if item.is_dir():
                    continue
                target = destination / item.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(item), str(target))
                moved += 1
            shutil.rmtree(source)
        else:
            shutil.move(str(source), str(destination))
            moved += 1
    TEMPLATE.rmdir()
    return moved


def main() -> int:
    if "--yes" not in sys.argv:
        print(__doc__)
        print("Refusing to run without --yes.")
        return 1

    # The one reliable signal that cleanup has already happened, and the
    # guard that stops this running twice.
    if not TEMPLATE.is_dir():
        print("No template/ folder - this repository is already clean.")
        return 0

    print("Removing the learning material...")
    for entry in sorted(ROOT.iterdir()):
        if entry.name in KEEP_AT_ROOT:
            continue
        if remove(entry.name):
            print(f"  removed  {entry.name}")

    # The kit's own CI tests the kit. The template ships the workflow a
    # real project wants, and it arrives with the promotion below.
    for workflow in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        if workflow.name != "template-cleanup.yml":
            workflow.unlink()
            print(f"  removed  .github/workflows/{workflow.name}")

    print("\nPromoting template/ to the repository root...")
    print(f"  moved {promote_template()} files")

    for relative in SELF:
        remove(relative)
    print("  removed the cleanup script and its workflow")

    print(
        "\nDone. This is now a plain Playwright + pytest project:\n"
        "    pip install -r requirements.txt\n"
        "    playwright install chromium\n"
        "    pytest\n\n"
        "The learning kit stays where it was, at\n"
        "    https://github.com/jamessaludario/qa-starter-kit-python"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
