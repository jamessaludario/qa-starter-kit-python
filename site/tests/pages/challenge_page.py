"""
pages/challenge_page.py
=======================
One challenge: the brief, the editor, the shop under test, and the
verdict.

The verdict has four distinct shapes, and telling them apart is most of
what this page object is for - because "it went red" is exactly the
feedback the site exists to avoid, and a test that only checks for red
would be blind to the difference between these:

    syntax     Python could not parse it
    review     the AST rubric blocked it, and it was NEVER RUN
    error      it ran, and an assertion failed
    checks     it ran, and the behavioural checks disagreed

Running one attempt boots an 11 MB Python runtime the first time, which
is why the waits here take an explicit, generous timeout instead of the
5-second default.
"""

from pages.base_page import BasePage

# Downloading and starting Pyodide, then running the attempt. Slow on a
# cold cache, and a flake here would be a real bug, so the number is
# generous on purpose rather than tuned to the fastest machine we own.
RUN_TIMEOUT_MS = 120_000


class ChallengePage(BasePage):

    def __init__(self, page, zone_id: str, challenge_id: str):
        super().__init__(page)
        self.route = "/zone/" + zone_id + "/" + challenge_id

    # ------------------------------------------------------------------
    # The task
    # ------------------------------------------------------------------

    @property
    def title(self):
        return self.page.get_by_role("heading", level=1)

    @property
    def brief(self):
        return self.page.locator(".brief")

    # ------------------------------------------------------------------
    # The work area
    # ------------------------------------------------------------------

    @property
    def editor(self):
        """The main code box.

        It is a real <textarea> with the highlighted layer painted
        behind it, so it has a proper accessible name and fill() works
        on it like any other input.
        """
        return self.page.get_by_label("Your test code")

    def cell(self, label: str):
        """An extra editor - a page object or conftest.py cell."""
        return self.page.get_by_label(label)

    @property
    def highlight_layer(self):
        """The syntax-coloured text painted BEHIND the textarea.

        It is aria-hidden - a screen reader should hear the textarea and
        not a duplicate copy of the code - so there is no accessible name
        to grab it by, and a CSS locator is the honest way in.
        """
        return self.page.locator(".code-highlight code")

    @property
    def highlight_box(self):
        """The <pre> the painted layer sits in.

        Distinct from highlight_layer on purpose: the BOX (padding, and
        therefore where the first character starts) belongs to the pre,
        while the TEXT metrics belong to the <code> inside it. Comparing
        the wrong one against the textarea proves nothing.
        """
        return self.page.locator(".code-highlight")

    @property
    def line_numbers(self):
        return self.page.locator(".code-gutter")

    # What decides the SHAPE of a character: get any of these wrong
    # between the two layers and the caret slides off the glyph.
    TEXT_METRICS = (
        "fontFamily", "fontSize", "fontWeight", "fontStyle", "fontStretch",
        "fontVariantLigatures", "fontFeatureSettings", "lineHeight",
        "letterSpacing", "wordSpacing", "tabSize", "whiteSpace", "textIndent",
    )

    # What decides WHERE the first character starts.
    BOX_METRICS = (
        "paddingTop", "paddingLeft", "borderTopWidth", "borderLeftWidth",
        "boxSizing",
    )

    def text_metrics(self, locator) -> dict:
        """Read the font styles that decide how a character is drawn."""
        return self._styles(locator, self.TEXT_METRICS)

    def box_metrics(self, locator) -> dict:
        """Read the styles that decide where the text block begins."""
        return self._styles(locator, self.BOX_METRICS)

    @staticmethod
    def _styles(locator, keys) -> dict:
        return locator.evaluate(
            """(el, keys) => {
                 const style = getComputedStyle(el);
                 return Object.fromEntries(keys.map((k) => [k, style[k]]));
               }""",
            list(keys),
        )

    def paint_drift(self, sample: str) -> float:
        """How far the painted text and the caret disagree, in pixels.

        Lays the same string out twice - once in the painted layer's
        font, once in the textarea's - and returns the gap at the end of
        it. 0 means the caret sits exactly on the character a learner is
        editing; anything else is drift you can see and feel, and it
        grows the further along the line you type.
        """
        return self.page.locator(".code-surface").evaluate(
            """(surface, sample) => {
                 const copied = ["fontFamily", "fontSize", "fontWeight",
                   "fontStyle", "fontStretch", "fontVariantLigatures",
                   "fontFeatureSettings", "letterSpacing", "wordSpacing"];
                 const widthIn = (source) => {
                   const style = getComputedStyle(source);
                   const probe = document.createElement("span");
                   copied.forEach((k) => { probe.style[k] = style[k]; });
                   probe.style.whiteSpace = "pre";
                   probe.style.position = "absolute";
                   probe.textContent = sample;
                   surface.appendChild(probe);
                   const width = probe.getBoundingClientRect().width;
                   probe.remove();
                   return width;
                 };
                 return Math.abs(widthIn(surface.querySelector(".code-highlight code"))
                               - widthIn(surface.querySelector(".code-input")));
               }""",
            sample,
        )

    @property
    def locator_box(self):
        """The single-line input used by locator-match challenges."""
        return self.page.get_by_label("Locator expression, written after page.")

    @property
    def shop(self):
        """The iframe holding AutomationVille, the app under test."""
        return self.page.frame_locator(".app-frame")

    def write(self, source: str):
        """Replace the editor's contents with a whole solution."""
        self.editor.fill(source)
        return self

    def write_locator(self, expression: str):
        self.locator_box.fill(expression)
        return self

    # ------------------------------------------------------------------
    # Running
    # ------------------------------------------------------------------

    @property
    def run_button(self):
        return self.page.get_by_role("button", name="Run test")

    @property
    def reset_button(self):
        return self.page.get_by_role("button", name="Reset the shop")

    def run(self):
        """Submit one attempt.

        Deliberately does NOT wait for a verdict: which verdict to wait
        for is the test's business, and a generic "wait for anything"
        here would let a test pass while looking at the wrong outcome.
        """
        self.run_button.click()
        return self

    # ------------------------------------------------------------------
    # The verdict
    # ------------------------------------------------------------------

    @property
    def success(self):
        """The green card. Its heading starts "Cleared"."""
        return self.page.locator(".verdict.good")

    @property
    def failure(self):
        """The red card shown when the test ran and failed."""
        return self.page.locator(".verdict.bad")

    @property
    def crash_output(self):
        """The traceback, verbatim - the same text a terminal would show."""
        return self.page.locator("pre.crash")

    @property
    def review(self):
        """The code-review panel produced by the AST rubric."""
        return self.page.locator(".review")

    @property
    def blocking_findings(self):
        """Findings a reviewer would not approve. These stop the run."""
        return self.page.locator(".finding.error")

    @property
    def advisory_findings(self):
        """Findings that pass but cost the clean-run bonus."""
        return self.page.locator(".finding.advice")

    @property
    def checks(self):
        return self.page.locator("li.check")

    @property
    def failed_checks(self):
        return self.page.locator("li.check.bad")

    @property
    def check_feedback(self):
        """The coaching line under a check that did not pass."""
        return self.page.locator(".check-feedback")

    @property
    def xp_awarded(self):
        """"+53 XP" on the success card."""
        return self.page.locator(".xp-total")

    @property
    def printed_output(self):
        return self.page.locator("details.stdout")

    # ------------------------------------------------------------------
    # Hints
    # ------------------------------------------------------------------

    def reveal_hint(self, label: str):
        """Open a tiered hint. The button says what it will cost."""
        self.page.get_by_role("button", name=label).click()

    @property
    def hint_bodies(self):
        return self.page.locator(".hint-body")
