"""
Every solution the site ships actually passes the site's own grading.

This suite exists because a content bug is invisible until somebody
plays the challenge. A `solution` in a JSON file is never shown to a
learner, so nothing else forces it to stay true - and a challenge whose
own answer does not pass is worse than a missing challenge, because the
learner will assume they are the one who is wrong.

It is parametrised over content, so a challenge added tomorrow is
covered tomorrow with no edit here. That is the point.
"""

import json
from pathlib import Path

import pytest
from pages.challenge_page import RUN_TIMEOUT_MS, ChallengePage
from playwright.sync_api import Page, expect

CONTENT = Path(__file__).resolve().parents[1] / "content"

# Quizzes are graded by their `answer` index, not by running Python, so
# they have no solution to execute. They get their own check below.
RUNNABLE_KINDS = {
    "write-the-test", "fill-the-blank", "fix-the-broken-test",
    "spot-the-flake", "refactor-to-pom", "locator-match",
}
QUIZ_KINDS = {"quiz", "predict-the-error", "read-the-trace"}


def load_challenges():
    """Read the authored content straight off disk.

    Deliberately NOT read from the built dist/: the source files are
    what a contributor edits, and reading those means the test fails on
    the file they would have to fix.
    """
    found = []
    for zone_dir in sorted(CONTENT.glob("zones/*")):
        zone_file = zone_dir / "zone.json"
        if not zone_file.exists():
            continue
        zone = json.loads(zone_file.read_text(encoding="utf-8"))
        for path in sorted(zone_dir.glob("challenges/*.json")):
            found.append((zone["id"], json.loads(path.read_text(encoding="utf-8"))))
    return found


ALL_CHALLENGES = load_challenges()

RUNNABLE = [
    pytest.param(zone_id, challenge, id=f"{zone_id}/{challenge['id']}")
    for zone_id, challenge in ALL_CHALLENGES
    if challenge["kind"] in RUNNABLE_KINDS
]

QUIZZES = [
    pytest.param(zone_id, challenge, id=f"{zone_id}/{challenge['id']}")
    for zone_id, challenge in ALL_CHALLENGES
    if challenge["kind"] in QUIZ_KINDS
]


# --------------------------------------------------------------------------
# Content shape - no browser needed, so these run in milliseconds
# --------------------------------------------------------------------------

def test_the_content_actually_loaded():
    """A glob that silently matches nothing would make this file a no-op."""
    assert len(ALL_CHALLENGES) >= 19
    assert RUNNABLE, "No runnable challenges found - check the kind names"


@pytest.mark.parametrize("zone_id, challenge", RUNNABLE)
def test_every_runnable_challenge_ships_a_solution(zone_id, challenge):
    del zone_id
    assert challenge.get("solution"), (
        f"{challenge['id']} has no solution. Without one, nothing can prove "
        "the challenge is solvable at all."
    )


@pytest.mark.parametrize("zone_id, challenge", QUIZZES)
def test_every_quiz_answer_points_at_a_real_option(zone_id, challenge):
    del zone_id
    for index, question in enumerate(challenge["questions"]):
        answer = question["answer"]
        assert 0 <= answer < len(question["options"]), (
            f"{challenge['id']} question {index + 1}: answer index {answer} "
            f"is outside its {len(question['options'])} options"
        )
        assert question.get("why"), (
            f"{challenge['id']} question {index + 1} has no explanation. A "
            "learner who guessed right and does not know why learned nothing."
        )


@pytest.mark.parametrize("zone_id, challenge", RUNNABLE)
def test_every_failing_check_has_something_to_say(zone_id, challenge):
    """A check without feedback is a red X, which is what we promised not
    to ship. The engine has a default message, but it is generic - the
    author knows what went wrong and should say so."""
    del zone_id
    for check in challenge.get("checks", []):
        assert check.get("feedback") or check.get("label"), (
            f"{challenge['id']}: a {check['kind']} check has neither a label "
            "nor feedback, so a learner who fails it is told nothing."
        )


# --------------------------------------------------------------------------
# The real thing: run each solution in the browser
# --------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.parametrize("zone_id, challenge", RUNNABLE)
def test_the_shipped_solution_clears_the_challenge(
    page: Page, python_runtime_available, zone_id, challenge
):
    del python_runtime_available
    view = ChallengePage(page, zone_id, challenge["id"]).open()

    if challenge["kind"] == "locator-match":
        # These take an expression, not a whole test file.
        view.write_locator(challenge["solution"])
    else:
        view.write(challenge["solution"])

    view.run()

    # If this fails, the challenge is unsolvable as written - fix the
    # content, not the test.
    expect(view.success).to_be_visible(timeout=RUN_TIMEOUT_MS)
    expect(view.failed_checks).to_have_count(0)
    expect(view.blocking_findings).to_have_count(0)
