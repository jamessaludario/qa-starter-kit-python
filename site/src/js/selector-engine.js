/* The selector engine: turns a Playwright locator chain into elements.
 *
 * The Python shim never touches the DOM. It builds a CHAIN - a list of
 * steps like [{k:"css", v:".shop-menu"}, {k:"role", role:"link", name:"Cart"}] -
 * and hands it here. That split matters:
 *
 *   - resolution happens FRESH on every action, so locators stay "lazy
 *     and self-updating" exactly as the guide describes;
 *   - the behaviours learners must internalise (role beats CSS, strict
 *     mode, actionability) are implemented once, here, honestly.
 *
 * This is a faithful subset of Playwright, not a reimplementation. Where
 * it simplifies, it simplifies in the direction of "the real thing would
 * also match this".
 */

export const SelectorEngine = (function () {
  "use strict";

  // ------------------------------------------------------------- text utils

  // Playwright normalises whitespace everywhere it matches text.
  function norm(text) {
    return String(text == null ? "" : text).replace(/\s+/g, " ").trim();
  }

  function matchText(actual, expected, exact) {
    var a = norm(actual);
    var b = norm(expected);
    if (exact) return a === b;
    return a.toLowerCase().indexOf(b.toLowerCase()) !== -1;
  }

  // innerText is layout-aware (it skips hidden text) which is what
  // Playwright reports too. It is undefined for detached nodes, so fall
  // back to textContent.
  function elementText(el) {
    return norm(el.innerText === undefined ? el.textContent : el.innerText);
  }

  // ------------------------------------------------------------------ roles

  var INPUT_TEXT_TYPES = ["text", "email", "password", "tel", "url", "search", ""];

  function roleOf(el) {
    var explicit = el.getAttribute && el.getAttribute("role");
    if (explicit) return explicit.trim().toLowerCase();
    var tag = el.tagName.toLowerCase();
    if (tag === "a") return el.hasAttribute("href") ? "link" : "generic";
    if (tag === "button") return "button";
    if (tag === "input") {
      var type = (el.getAttribute("type") || "").toLowerCase();
      if (type === "button" || type === "submit" || type === "reset") return "button";
      if (type === "checkbox") return "checkbox";
      if (type === "radio") return "radio";
      if (type === "number") return "spinbutton";
      if (INPUT_TEXT_TYPES.indexOf(type) !== -1) return "textbox";
      return "textbox";
    }
    if (tag === "textarea") return "textbox";
    if (tag === "select") return el.multiple ? "listbox" : "combobox";
    if (tag === "option") return "option";
    if (/^h[1-6]$/.test(tag)) return "heading";
    if (tag === "img") return el.getAttribute("alt") === "" ? "presentation" : "img";
    if (tag === "li") return "listitem";
    if (tag === "ul" || tag === "ol") return "list";
    if (tag === "table") return "table";
    if (tag === "tr") return "row";
    if (tag === "td") return "cell";
    if (tag === "th") return "columnheader";
    if (tag === "nav") return "navigation";
    if (tag === "main") return "main";
    if (tag === "dialog") return "dialog";
    if (tag === "form") return "form";
    return "generic";
  }

  // A pragmatic accessible-name computation: the parts of the spec that
  // actually decide matches on pages like this one.
  function accessibleName(el) {
    var aria = el.getAttribute && el.getAttribute("aria-label");
    if (aria) return norm(aria);

    var labelledBy = el.getAttribute && el.getAttribute("aria-labelledby");
    if (labelledBy) {
      var parts = labelledBy.split(/\s+/).map(function (id) {
        var target = el.ownerDocument.getElementById(id);
        return target ? elementText(target) : "";
      });
      var joined = norm(parts.join(" "));
      if (joined) return joined;
    }

    var tag = el.tagName.toLowerCase();
    if (tag === "img") return norm(el.getAttribute("alt") || "");

    if (tag === "input") {
      var type = (el.getAttribute("type") || "").toLowerCase();
      if (type === "button" || type === "submit" || type === "reset") {
        return norm(el.value || type);
      }
    }

    if (tag === "input" || tag === "select" || tag === "textarea") {
      var label = labelFor(el);
      if (label) return label;
      return norm(el.getAttribute("placeholder") || el.getAttribute("title") || "");
    }

    var text = elementText(el);
    if (text) return text;
    return norm(el.getAttribute("title") || "");
  }

  // The label text bound to a form control: <label for="x">, or the
  // <label> the control sits inside.
  function labelFor(el) {
    var doc = el.ownerDocument;
    if (el.id) {
      var explicit = doc.querySelector('label[for="' + cssEscape(el.id) + '"]');
      if (explicit) return norm(explicit.textContent);
    }
    var wrapper = el.closest ? el.closest("label") : null;
    if (wrapper) return norm(wrapper.textContent);
    return "";
  }

  function cssEscape(value) {
    if (window.CSS && window.CSS.escape) return window.CSS.escape(value);
    return String(value).replace(/["\\]/g, "\\$&");
  }

  // -------------------------------------------------------------- visibility

  // Playwright's definition: a non-empty bounding box and not
  // visibility:hidden. Note that an element can be "visible" while
  // scrolled out of view - that is correct, and it is why Playwright
  // scrolls before clicking rather than failing.
  function isVisible(el) {
    if (!el || !el.getClientRects) return false;
    if (!el.getClientRects().length) return false;
    var style = el.ownerDocument.defaultView.getComputedStyle(el);
    return style.visibility !== "hidden" && style.visibility !== "collapse";
  }

  function isEnabled(el) {
    if (el.disabled) return false;
    var fieldset = el.closest ? el.closest("fieldset[disabled]") : null;
    return !fieldset;
  }

  function isChecked(el) {
    if (typeof el.checked === "boolean") return el.checked;
    var aria = el.getAttribute("aria-checked");
    return aria === "true";
  }

  function isEditable(el) {
    var tag = el.tagName.toLowerCase();
    if (tag !== "input" && tag !== "textarea" && !el.isContentEditable) return false;
    return isEnabled(el) && !el.readOnly;
  }

  // ------------------------------------------------------------- resolution

  function descendants(scope) {
    // `scope` may be the document (first step) or an element (chained step).
    return Array.prototype.slice.call(scope.querySelectorAll("*"));
  }

  function inDocumentOrder(elements) {
    var unique = [];
    elements.forEach(function (el) {
      if (unique.indexOf(el) === -1) unique.push(el);
    });
    unique.sort(function (a, b) {
      if (a === b) return 0;
      var position = a.compareDocumentPosition(b);
      // eslint-disable-next-line no-bitwise
      return (position & Node.DOCUMENT_POSITION_FOLLOWING) ? -1 : 1;
    });
    return unique;
  }

  function byXPath(scope, expression) {
    var doc = scope.ownerDocument || scope;
    var found = [];
    var iterator = doc.evaluate(expression, scope, null,
      XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
    for (var i = 0; i < iterator.snapshotLength; i++) {
      var node = iterator.snapshotItem(i);
      if (node.nodeType === 1) found.push(node);
    }
    return found;
  }

  // get_by_text matches the SMALLEST element containing the text: given
  // <li><a>Cart</a></li> you get the <a>, not both. Without this rule
  // every text locator would also match <body>.
  function byText(scope, value, exact) {
    var all = descendants(scope).filter(function (el) {
      var tag = el.tagName.toLowerCase();
      if (tag === "input") {
        var type = (el.getAttribute("type") || "").toLowerCase();
        // Buttons rendered as <input> are matched by their value.
        if (type === "button" || type === "submit" || type === "reset") {
          return matchText(el.value, value, exact);
        }
        return false;
      }
      if (tag === "script" || tag === "style") return false;
      return matchText(el.textContent, value, exact);
    });
    return all.filter(function (el) {
      return !all.some(function (other) {
        return other !== el && el.contains(other);
      });
    });
  }

  function applyStep(scopes, step) {
    var out = [];
    scopes.forEach(function (scope) {
      switch (step.k) {
        case "css":
          out = out.concat(Array.prototype.slice.call(scope.querySelectorAll(step.v)));
          break;
        case "xpath":
          out = out.concat(byXPath(scope, step.v));
          break;
        case "text":
          out = out.concat(byText(scope, step.v, !!step.exact));
          break;
        case "role":
          out = out.concat(descendants(scope).filter(function (el) {
            if (roleOf(el) !== String(step.role).toLowerCase()) return false;
            if (step.name === undefined || step.name === null) return true;
            return matchText(accessibleName(el), step.name, !!step.exact);
          }));
          break;
        case "label":
          out = out.concat(descendants(scope).filter(function (el) {
            var tag = el.tagName.toLowerCase();
            if (tag !== "input" && tag !== "select" && tag !== "textarea") return false;
            return matchText(labelFor(el), step.v, !!step.exact);
          }));
          break;
        case "placeholder":
          out = out.concat(descendants(scope).filter(function (el) {
            var placeholder = el.getAttribute("placeholder");
            return placeholder !== null && matchText(placeholder, step.v, !!step.exact);
          }));
          break;
        case "testid":
          out = out.concat(Array.prototype.slice.call(
            scope.querySelectorAll('[data-testid="' + cssEscape(step.v) + '"]')));
          break;
        case "alttext":
          out = out.concat(descendants(scope).filter(function (el) {
            var alt = el.getAttribute("alt");
            return alt !== null && matchText(alt, step.v, !!step.exact);
          }));
          break;
        case "title":
          out = out.concat(descendants(scope).filter(function (el) {
            var title = el.getAttribute("title");
            return title !== null && matchText(title, step.v, !!step.exact);
          }));
          break;
        default:
          throw new Error("unknown locator step: " + step.k);
      }
    });
    return inDocumentOrder(out);
  }

  // Positional and filtering steps narrow the CURRENT set instead of
  // searching inside it.
  function applyRefinement(elements, step) {
    switch (step.k) {
      case "first": return elements.slice(0, 1);
      case "last": return elements.slice(-1);
      case "nth": {
        var index = step.v < 0 ? elements.length + step.v : step.v;
        return elements[index] ? [elements[index]] : [];
      }
      case "filter":
        return elements.filter(function (el) {
          if (step.hasText !== undefined && step.hasText !== null) {
            if (!matchText(el.textContent, step.hasText, false)) return false;
          }
          if (step.hasNotText !== undefined && step.hasNotText !== null) {
            if (matchText(el.textContent, step.hasNotText, false)) return false;
          }
          if (step.has) {
            if (!resolveIn(el, step.has).length) return false;
          }
          return true;
        });
      case "visible":
        return elements.filter(isVisible);
      default:
        return null;                      // not a refinement
    }
  }

  function resolveFrom(roots, chain) {
    var current = roots;
    for (var i = 0; i < chain.length; i++) {
      var step = chain[i];
      var refined = applyRefinement(current, step);
      current = refined !== null ? refined : applyStep(current, step);
    }
    // A scope is not a match: only elements found by a step count.
    return current.filter(function (node) { return node.nodeType === 1; });
  }

  function resolveIn(root, chain) { return resolveFrom([root], chain); }

  function resolve(doc, chain) { return resolveFrom([doc], chain); }

  return {
    resolve: resolve,
    roleOf: roleOf,
    accessibleName: accessibleName,
    isVisible: isVisible,
    isEnabled: isEnabled,
    isChecked: isChecked,
    isEditable: isEditable,
    elementText: elementText,
    norm: norm
  };
})();
