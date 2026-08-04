"""
The code editor: does the caret sit where the text is?

The editor is a real <textarea> with transparent text, and a
syntax-coloured copy painted on a <pre> directly behind it. That trick
buys a proper accessible, IME-friendly, undo-able text input for about a
hundred lines of code - and it has exactly one failure mode: if the two
layers lay text out even slightly differently, the caret drifts away
from the glyphs and editing becomes guesswork.

It is invisible to every other test in this suite, because fill() and
the grader do not care where pixels landed. So it gets its own file.

These are fast: the editor renders long before Pyodide is asked for, so
nothing here waits on the Python runtime.
"""

from pages.challenge_page import ChallengePage
from playwright.sync_api import Page, expect

# Long enough that a small per-character error becomes an obvious one:
# the bug this file exists to catch was under 1 px per character, which
# is invisible on "x = 1" and half a word wide by the end of this line.
LONG_LINE = '    expect(page.get_by_role("heading", name="All Products")).to_be_visible()'

# One line per zone kind, so the assertions below speak for every editor
# the site puts in front of a learner, not just the first one.
FIRST_TEST = "base-camp", "first-test"


def test_the_caret_lands_on_the_character_being_edited(page: Page):
    """The symptom test: measure the drift, insist it is zero.

    Deliberately measured rather than reasoned about. The cause last
    time was a rule four hundred lines away in the stylesheet
    (`code { font-size: .88em }`, correct for prose, fatal here), and no
    amount of reading the editor's own CSS would have found it.
    """
    challenge = ChallengePage(page, *FIRST_TEST).open()
    expect(challenge.editor).to_be_visible()

    # Sub-pixel tolerance, not exact equality: browsers round text
    # measurements, and a fifth of a pixel over 76 characters is not
    # something a human can see.
    assert challenge.paint_drift(LONG_LINE) < 0.2


def test_the_painted_layer_and_the_textarea_share_their_text_metrics(page: Page):
    """The cause test: say WHICH property drifted.

    The measurement above proves something is wrong; this one names it,
    so the next person to break it reads "fontSize: 11.968px !=
    13.6px" instead of "assert 45.2 < 0.2".
    """
    challenge = ChallengePage(page, *FIRST_TEST).open()
    expect(challenge.editor).to_be_visible()

    # How each character is drawn - read off the <code> that actually
    # renders the text.
    assert (challenge.text_metrics(challenge.highlight_layer)
            == challenge.text_metrics(challenge.editor))

    # Where the first character starts - that belongs to the <pre>
    # wrapping it, which is the element stretched over the textarea.
    assert (challenge.box_metrics(challenge.highlight_box)
            == challenge.box_metrics(challenge.editor))


def test_the_line_numbers_line_up_with_the_lines(page: Page):
    """The gutter is a third element that has to agree with the other two.

    It only shares two properties with them - the size of a line and
    where the first one starts - but getting either wrong points every
    number at the wrong row, which is worse than having no numbers.
    """
    challenge = ChallengePage(page, *FIRST_TEST).open()
    expect(challenge.editor).to_be_visible()

    gutter = challenge.text_metrics(challenge.line_numbers)
    editor = challenge.text_metrics(challenge.editor)
    assert gutter["lineHeight"] == editor["lineHeight"]
    assert gutter["fontSize"] == editor["fontSize"]

    # Same first baseline, so line 1's number is beside line 1.
    assert (challenge.box_metrics(challenge.line_numbers)["paddingTop"]
            == challenge.box_metrics(challenge.editor)["paddingTop"])


def test_the_editor_still_reads_back_what_was_typed_into_it(page: Page):
    """A guard on the whole trick.

    Everything above is about pixels. This is the reminder that the
    thing underneath is an ordinary textarea: if the painted layer ever
    became the real input, fill() would still appear to work and every
    challenge in the suite would start failing for no visible reason.
    """
    challenge = ChallengePage(page, *FIRST_TEST).open()

    challenge.write("# typed by a test\nx = 1\n")

    expect(challenge.editor).to_have_value("# typed by a test\nx = 1\n")
    # The painted copy follows the input, and is only a copy.
    expect(challenge.highlight_layer).to_contain_text("typed by a test")
