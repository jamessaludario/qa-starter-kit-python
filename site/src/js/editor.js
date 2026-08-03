/* A small Python editor: a real <textarea> with a highlighted layer behind it.
 *
 * Why not CodeMirror or Monaco? Because a textarea is already a perfect
 * text input - screen readers, IME, spellcheck control, undo, select-all,
 * mobile keyboards - and re-implementing that is how editors become
 * inaccessible. Painting colours on a <pre> underneath costs about a
 * hundred lines and breaks nothing if the highlighter is wrong.
 *
 * Keyboard: Tab indents, Shift+Tab outdents, Ctrl/Cmd+Enter runs, and
 * Escape-then-Tab moves focus out (so the editor is never a keyboard
 * trap).
 */

import { h } from "./dom.js";

var KEYWORDS = ("False None True and as assert async await break class continue def del "
  + "elif else except finally for from global if import in is lambda nonlocal not or "
  + "pass raise return try while with yield").split(" ");

var BUILTINS = ("print len range str int float bool list dict set tuple enumerate zip "
  + "sorted sum min max abs any all isinstance").split(" ");

// The names a learner should recognise as "the Playwright vocabulary".
var API = ("page expect locator get_by_role get_by_text get_by_label get_by_placeholder "
  + "get_by_test_id get_by_alt_text get_by_title goto click fill check uncheck press "
  + "hover select_option inner_text all_inner_texts text_content input_value count "
  + "is_visible is_enabled is_checked get_attribute first last nth filter reload "
  + "go_back title url to_be_visible to_be_hidden not_to_be_visible to_have_text "
  + "to_contain_text to_have_value to_have_count to_have_url to_have_title "
  + "to_have_attribute to_be_enabled to_be_disabled to_be_checked").split(" ");

var TOKEN = new RegExp([
  "(#[^\\n]*)",                                        // 1 comment
  "(\"\"\"[\\s\\S]*?\"\"\"|'''[\\s\\S]*?''')",         // 2 triple-quoted
  "(\"(?:[^\"\\\\\\n]|\\\\.)*\"|'(?:[^'\\\\\\n]|\\\\.)*')",  // 3 string
  "\\b(\\d+(?:\\.\\d+)?)\\b",                          // 4 number
  "\\b([A-Za-z_][A-Za-z0-9_]*)\\b"                     // 5 word
].join("|"), "g");

function escapeHtml(text) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

export function highlight(source) {
  var out = "";
  var last = 0;
  source.replace(TOKEN, function (match, comment, triple, string, number, word, offset) {
    out += escapeHtml(source.slice(last, offset));
    last = offset + match.length;
    if (comment) out += '<span class="tok-comment">' + escapeHtml(match) + "</span>";
    else if (triple || string) out += '<span class="tok-string">' + escapeHtml(match) + "</span>";
    else if (number) out += '<span class="tok-number">' + escapeHtml(match) + "</span>";
    else if (KEYWORDS.indexOf(word) !== -1) out += '<span class="tok-key">' + word + "</span>";
    else if (API.indexOf(word) !== -1) out += '<span class="tok-api">' + word + "</span>";
    else if (BUILTINS.indexOf(word) !== -1) out += '<span class="tok-builtin">' + word + "</span>";
    else out += escapeHtml(match);
    return match;
  });
  out += escapeHtml(source.slice(last));
  // A trailing newline keeps the highlighted layer exactly as tall as
  // the textarea, so the two never drift apart at the bottom.
  return out + "\n";
}

export function createEditor(options) {
  options = options || {};
  var textarea = h("textarea", {
    class: "code-input",
    spellcheck: "false",
    autocapitalize: "off",
    autocomplete: "off",
    "aria-label": options.label || "Python editor",
    rows: String(options.rows || 14)
  });
  var code = h("code", {});
  var pre = h("pre", { class: "code-highlight", "aria-hidden": "true" }, [code]);
  var gutter = h("div", { class: "code-gutter", "aria-hidden": "true" });
  var surface = h("div", { class: "code-surface" }, [pre, textarea]);
  var root = h("div", { class: "code-editor" }, [gutter, surface]);

  var escapePressed = false;

  function paint() {
    code.innerHTML = highlight(textarea.value);
    var lines = textarea.value.split("\n").length;
    var numbers = [];
    for (var i = 1; i <= lines; i++) numbers.push(i);
    gutter.textContent = numbers.join("\n");
    // Grow with the content instead of scrolling in a short box: on a
    // phone, an editor you cannot see the bottom of is unusable.
    textarea.style.height = "auto";
    textarea.style.height = Math.max(textarea.scrollHeight, 120) + "px";
  }

  function replaceSelection(before, text, after, caret) {
    textarea.value = before + text + after;
    textarea.selectionStart = textarea.selectionEnd = caret;
    paint();
    if (options.onChange) options.onChange(textarea.value);
  }

  textarea.addEventListener("input", function () {
    paint();
    if (options.onChange) options.onChange(textarea.value);
  });

  textarea.addEventListener("scroll", function () {
    pre.scrollTop = textarea.scrollTop;
    pre.scrollLeft = textarea.scrollLeft;
  });

  textarea.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      // Next Tab leaves the editor - the standard escape hatch that
      // stops a Tab-indenting textarea from trapping keyboard users.
      escapePressed = true;
      return;
    }
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      if (options.onRun) options.onRun();
      return;
    }
    if (event.key === "Tab") {
      if (escapePressed) { escapePressed = false; return; }
      event.preventDefault();
      var start = textarea.selectionStart;
      var end = textarea.selectionEnd;
      var value = textarea.value;
      if (event.shiftKey || start !== end) {
        // Indent or outdent whole lines.
        var from = value.lastIndexOf("\n", start - 1) + 1;
        var block = value.slice(from, end);
        var shifted = event.shiftKey
          ? block.replace(/^ {1,4}/gm, "")
          : block.replace(/^/gm, "    ");
        replaceSelection(value.slice(0, from), shifted, value.slice(end),
                         from + shifted.length);
      } else {
        replaceSelection(value.slice(0, start), "    ", value.slice(end), start + 4);
      }
      return;
    }
    escapePressed = false;
    if (event.key === "Enter") {
      event.preventDefault();
      var at = textarea.selectionStart;
      var text = textarea.value;
      var lineStart = text.lastIndexOf("\n", at - 1) + 1;
      var line = text.slice(lineStart, at);
      var indent = (line.match(/^\s*/) || [""])[0];
      // A line ending in ':' opens a block, so the next line goes in.
      if (/:\s*$/.test(line)) indent += "    ";
      replaceSelection(text.slice(0, at), "\n" + indent,
                       text.slice(textarea.selectionEnd), at + 1 + indent.length);
    }
  });

  return {
    element: root,
    textarea: textarea,
    get value() { return textarea.value; },
    set value(next) { textarea.value = next; paint(); },
    focus: function () { textarea.focus(); },
    /** Put a red marker on the line an error came from. */
    markLine: function (line) {
      gutter.innerHTML = gutter.textContent.split("\n").map(function (n) {
        return Number(n) === Number(line)
          ? '<span class="gutter-error">' + n + "</span>" : n;
      }).join("\n");
    },
    refresh: paint
  };
}
