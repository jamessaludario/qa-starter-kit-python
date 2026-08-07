/* Six helpers instead of a framework.
 *
 * The whole site is a few thousand lines of vanilla JS. A framework
 * would be more code to download than the app itself, and the one thing
 * we cannot afford to make heavier is the page that already ships a
 * 11 MB Python runtime.
 */

export function h(tag, attrs, children) {
  var element = document.createElement(tag);
  attrs = attrs || {};
  Object.keys(attrs).forEach(function (key) {
    var value = attrs[key];
    if (value === null || value === undefined || value === false) return;
    if (key === "class") element.className = value;
    else if (key === "text") element.textContent = value;
    else if (key === "html") element.innerHTML = value;
    else if (key.indexOf("on") === 0) element.addEventListener(key.slice(2), value);
    else if (key === "dataset") Object.assign(element.dataset, value);
    else element.setAttribute(key, value === true ? "" : value);
  });
  (children || []).forEach(function (child) {
    if (child === null || child === undefined || child === false) return;
    element.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
  });
  return element;
}

export function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
  return node;
}

export function qs(selector, root) {
  return (root || document).querySelector(selector);
}

/** Announce something to screen readers without stealing focus. */
export function announce(message) {
  var region = qs("#live-region");
  if (region) region.textContent = message;
}

/** Read a dotted path out of a plain object: get(state, "cart.0.qty"). */
export function get(object, path) {
  return String(path).split(".").reduce(function (value, key) {
    if (value === null || value === undefined) return undefined;
    return value[key];
  }, object);
}

export function plural(count, one, many) {
  return count + " " + (count === 1 ? one : many);
}
