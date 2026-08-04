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

THIS DELETES THINGS, so it defends itself three ways:

  * --yes is required, so opening the wrong file does nothing;
  * it refuses outright when the checkout is the learning kit itself,
    which it works out from the git remote;
  * run by a human it prints what will go and waits for you to type
    "delete" (the workflow passes --ci to skip that, having already
    checked is_template).

The second guard exists because the first one was not enough: --yes is
exactly what somebody copies out of the README while reading it.
"""

import shutil
import subprocess
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


# The kit itself, and anything forked from it. A copy made with "Use
# this template" has its OWN remote, so this never matches there.
UPSTREAM = "qa-starter-kit-python"


def is_the_learning_kit() -> bool:
    """Is this checkout the kit rather than a project made from it?

    Asked of the git remote, because the file tree cannot answer it: a
    fresh template copy is byte-for-byte identical to the original until
    the moment this script runs.
    """
    try:
        remote = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=ROOT, capture_output=True, text=True, timeout=10,
            # No remote at all exits non-zero, and that is a fine answer
            # here - it just means "cannot tell", handled below.
            check=False,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return False        # no git, no remote - cannot tell, do not block
    return UPSTREAM in remote


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

    if is_the_learning_kit() and "--force" not in sys.argv:
        print(
            "Refusing: this checkout IS the learning kit.\n\n"
            "  origin points at " + UPSTREAM + ", so deleting learn/, site/,\n"
            "  docs/, desktop/ and the rest is almost certainly not what you\n"
            "  meant. This script is for a repository made with GitHub's\n"
            "  \"Use this template\" button, which has its own remote.\n\n"
            "  If you really do mean it here, pass --force. Everything it\n"
            "  removes is committed, so `git restore .` brings it back -\n"
            "  except site/vendor/ and site/dist/, which are git-ignored\n"
            "  and need `python site/fetch_vendor.py` again."
        )
        return 1

    # A human gets one more chance to notice. The workflow passes --ci,
    # having already established is_template == false.
    if "--ci" not in sys.argv:
        print("This will permanently delete, from " + str(ROOT) + ":\n")
        for entry in sorted(ROOT.iterdir()):
            if entry.name not in KEEP_AT_ROOT:
                print("    " + entry.name + ("/" if entry.is_dir() else ""))
        print("\nand promote template/ to the root in their place.")
        try:
            if input('\nType "delete" to go ahead: ').strip().lower() != "delete":
                print("Nothing was changed.")
                return 1
        except (EOFError, KeyboardInterrupt):
            print("\nNothing was changed.")
            return 1

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
