/* The synchronous bridge between Pyodide and the app under test.
 *
 * Every method here returns immediately. That is the whole reason the
 * learner can write ordinary blocking Playwright code: Pyodide runs on
 * this thread, the mock app is in a same-origin iframe on this thread,
 * so reading `iframe.contentDocument` needs no await and Python never
 * has to yield. See site/ARCHITECTURE.md for why we did not use a
 * Web Worker.
 *
 * The interface is deliberately made of strings and numbers only - no
 * JS objects cross into Python. Structured values travel as JSON, which
 * keeps object lifetimes (and debugging) simple.
 */

import { SelectorEngine as SE } from "./selector-engine.js";

export function createBridge(getIframe) {
  "use strict";

  var history = [];

  function frame() { return getIframe(); }
  function win() { return frame().contentWindow; }
  function doc() { return frame().contentDocument; }
  function app() { return win().AV; }

  function resolve(chainJson) {
    return SE.resolve(doc(), JSON.parse(chainJson));
  }

  function fail(code, detail) {
    return JSON.stringify({ ok: false, code: code, detail: detail || "" });
  }

  function done(value) {
    return JSON.stringify({ ok: true, value: value === undefined ? null : value });
  }

  // A short, human-readable description of an element, in the style of
  // the snippets Playwright prints in its error call logs.
  function sketch(el) {
    var bits = [el.tagName.toLowerCase()];
    if (el.id) bits.push("#" + el.id);
    if (el.className && typeof el.className === "string") {
      bits.push("." + el.className.trim().split(/\s+/).join("."));
    }
    var text = SE.elementText(el).slice(0, 40);
    return "<" + bits.join("") + ">" + (text ? " " + text : "");
  }

  function dispatch(el, type, init) {
    var Ctor = win()[init && init.ctor ? init.ctor : "Event"];
    var event = new Ctor(type, { bubbles: true, cancelable: true });
    if (init && init.key) event.key = init.key;
    el.dispatchEvent(event);
  }

  function fireInput(el) {
    dispatch(el, "input");
    dispatch(el, "change");
  }

  // Playwright's actionability checks, in the order it applies them.
  // Each failure code is retryable: the Python shim keeps polling (and
  // advancing the virtual clock) until the element becomes actionable
  // or the timeout runs out.
  function checkActionable(el, need) {
    if (!SE.isVisible(el)) return "not_visible";
    if (need.enabled && !SE.isEnabled(el)) return "not_enabled";
    if (need.editable && !SE.isEditable(el)) return "not_editable";
    if (need.hit) {
      el.scrollIntoView({ block: "center", inline: "nearest" });
      var box = el.getBoundingClientRect();
      var hit = doc().elementFromPoint(box.left + box.width / 2, box.top + box.height / 2);
      if (!hit) return "not_visible";
      if (hit !== el && !el.contains(hit)) return "intercepted:" + sketch(hit);
    }
    return null;
  }

  var ACTIONS = {
    click: { need: { enabled: true, hit: true }, run: function (el) { el.click(); } },
    hover: {
      need: { hit: true },
      run: function (el) { dispatch(el, "mouseover"); dispatch(el, "mousemove"); }
    },
    focus: { need: {}, run: function (el) { el.focus(); } },
    scroll_into_view_if_needed: {
      need: {},
      run: function (el) { el.scrollIntoView({ block: "center", inline: "nearest" }); }
    },
    fill: {
      need: { enabled: true, editable: true, hit: false },
      run: function (el, args) {
        el.focus();
        el.value = args[0];
        fireInput(el);
      }
    },
    press: {
      need: { enabled: true },
      run: function (el, args) {
        el.focus();
        dispatch(el, "keydown", { ctor: "KeyboardEvent", key: args[0] });
        dispatch(el, "keyup", { ctor: "KeyboardEvent", key: args[0] });
      }
    },
    check: {
      need: { enabled: true, hit: true },
      run: function (el) { if (!SE.isChecked(el)) el.click(); }
    },
    uncheck: {
      need: { enabled: true, hit: true },
      run: function (el) { if (SE.isChecked(el)) el.click(); }
    },
    select_option: {
      need: { enabled: true },
      run: function (el, args) {
        // args = [value, label] - whichever the learner passed.
        var wanted = args[0];
        var byLabel = args[1];
        var options = Array.prototype.slice.call(el.options);
        var chosen = null;
        options.forEach(function (option) {
          if (chosen) return;
          if (byLabel !== null && byLabel !== undefined) {
            if (SE.norm(option.label || option.text) === SE.norm(byLabel)) chosen = option;
          } else if (option.value === String(wanted)) {
            chosen = option;
          } else if (SE.norm(option.text) === SE.norm(wanted)) {
            chosen = option;
          }
        });
        if (!chosen) return "no_option";
        el.value = chosen.value;
        fireInput(el);
        return null;
      }
    }
  };

  // Reads never change the page, so they skip actionability entirely -
  // matching Playwright, where inner_text() on a hidden element still
  // returns its text.
  var READS = {
    inner_text: function (el) { return SE.elementText(el); },
    text_content: function (el) { return el.textContent; },
    input_value: function (el) { return el.value === undefined ? "" : el.value; },
    get_attribute: function (el, args) { return el.getAttribute(args[0]); },
    is_visible: function (el) { return SE.isVisible(el); },
    is_enabled: function (el) { return SE.isEnabled(el); },
    is_checked: function (el) { return SE.isChecked(el); },
    is_editable: function (el) { return SE.isEditable(el); },
    role_of: function (el) { return SE.roleOf(el); },
    accessible_name: function (el) { return SE.accessibleName(el); }
  };

  return {
    // ------------------------------------------------------------ lifecycle
    reset_app: function (scenarioJson) {
      history = [];
      app().reset(JSON.parse(scenarioJson || "{}"));
      history.push(app().url());
      return app().url();
    },

    snapshot: function () { return JSON.stringify(app().snapshot()); },

    // ----------------------------------------------------------- navigation
    goto_path: function (path) {
      app().navigate(path);
      history.push(app().url());
      return app().url();
    },
    reload: function () { app().navigate(app().url().replace(/^https?:\/\/[^/]+/, "")); return app().url(); },
    go_back: function () {
      if (history.length > 1) {
        history.pop();
        var previous = history[history.length - 1];
        app().navigate(previous.replace(/^https?:\/\/[^/]+/, ""));
      }
      return app().url();
    },
    url: function () { return app().url(); },
    title: function () { return app().title(); },

    // -------------------------------------------------------- virtual clock
    tick: function (ms) { return app().clock.advance(ms); },
    now: function () { return app().clock.now; },

    // ------------------------------------------------------------- locators
    count: function (chainJson) { return resolve(chainJson).length; },

    // What matched, for building a Playwright-shaped error message.
    describe: function (chainJson) {
      var elements = resolve(chainJson);
      return JSON.stringify({
        count: elements.length,
        visible: elements.filter(SE.isVisible).length,
        samples: elements.slice(0, 5).map(sketch),
        texts: elements.slice(0, 5).map(SE.elementText)
      });
    },

    // One action against the nth match. `index` is -1 for "the only
    // match" (strict mode), otherwise a resolved position.
    perform: function (chainJson, action, argsJson, index) {
      var elements = resolve(chainJson);
      if (index === -1) {
        if (elements.length === 0) return fail("not_found");
        if (elements.length > 1) return fail("strict", String(elements.length));
      } else if (!elements[index]) {
        return fail("not_found");
      }
      var el = index === -1 ? elements[0] : elements[index];

      if (READS[action]) {
        var value = READS[action](el, JSON.parse(argsJson || "[]"));
        return done(value === undefined ? null : value);
      }

      var spec = ACTIONS[action];
      if (!spec) return fail("unsupported", action);

      var problem = checkActionable(el, spec.need);
      if (problem) {
        var parts = problem.split(":");
        return fail(parts[0], parts.slice(1).join(":"));
      }
      var outcome = spec.run(el, JSON.parse(argsJson || "[]"));
      if (outcome) return fail(outcome);
      return done(null);
    },

    // Bulk read - .all_inner_texts() is the one method that is happy
    // with any number of matches, including zero.
    all_texts: function (chainJson) {
      return JSON.stringify(resolve(chainJson).map(SE.elementText));
    },

    // Outline whatever a locator matches, so "what does this address
    // actually point at?" has a visible answer.
    highlight: function (chainJson) {
      this.clear_highlight();
      var matches = resolve(chainJson);
      matches.forEach(function (el) { el.classList.add("quest-highlight"); });
      return matches.length;
    },

    clear_highlight: function () {
      Array.prototype.forEach.call(
        doc().querySelectorAll(".quest-highlight"),
        function (el) { el.classList.remove("quest-highlight"); }
      );
    }
  };
}
