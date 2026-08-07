/* Booting Python in the browser, and running one attempt.
 *
 * Pyodide is ~11 MB, so it is NOT loaded when the site opens - the quest
 * map, the lessons and the quizzes all work without it. It downloads the
 * first time a learner opens a coding challenge, behind an honest
 * progress bar that shows real bytes, not a fake spinner.
 *
 * Everything runs on the main thread. That is a deliberate decision with
 * real trade-offs; site/ARCHITECTURE.md explains them.
 */

import { createBridge } from "./bridge.js";

var PYODIDE_URL = "vendor/pyodide/pyodide.js";
var PYODIDE_INDEX = "vendor/pyodide/";

// Prefetched so the progress bar can show real numbers. loadPyodide then
// reads them straight from the HTTP cache.
var BIG_FILES = ["pyodide.asm.wasm", "python_stdlib.zip"];

var BOOT_PYTHON = [
  "import sys",
  "sys.path.insert(0, '/lib')",
  "sys.path.insert(0, '/lib/learner_env')",
  "import _quest_bridge",
  "from playwright_lite import _runtime",
  "_runtime.bind(_quest_bridge)",
  "from quest import harness",
  "harness.install_guards()"
].join("\n");

export const Runner = {
  status: "idle",              // idle | loading | ready | failed
  pyodide: null,
  bridge: null,
  error: null,
  _booting: null,
  _getIframe: null,

  /**
   * Tell the runner which iframe holds the app under test.
   *
   * Every challenge view builds its own iframe, so the bridge must look
   * the current one up each time rather than capture the first: after a
   * hash navigation the old frame is detached and its contentWindow is
   * null.
   */
  useIframe: function (getIframe) {
    var self = this;
    this._getIframe = getIframe;
    if (!this.bridge) {
      this.bridge = createBridge(function () { return self._getIframe(); });
    }
  },

  isReady: function () { return this.status === "ready"; },

  /** Boot once; concurrent callers share the same promise. */
  boot: function (onProgress) {
    if (this.status === "ready") return Promise.resolve(this);
    if (this._booting) return this._booting;
    this.status = "loading";
    var self = this;
    this._booting = this._boot(onProgress || function () {}).then(function () {
      self.status = "ready";
      return self;
    }).catch(function (error) {
      self.status = "failed";
      self.error = error;
      self._booting = null;
      throw error;
    });
    return this._booting;
  },

  _boot: async function (report) {
    report({ phase: "download", loaded: 0, total: 0, note: "Fetching the Python runtime" });
    await this._prefetch(report);

    report({ phase: "start", note: "Starting Python" });
    await loadScript(PYODIDE_URL);
    this.pyodide = await window.loadPyodide({ indexURL: PYODIDE_INDEX });

    report({ phase: "shim", note: "Loading the Playwright shim" });
    this._writePylib();

    if (!this.bridge) throw new Error("Runner.useIframe() must be called before boot().");
    this.pyodide.registerJsModule("_quest_bridge", this.bridge);
    this.pyodide.runPython(BOOT_PYTHON);
    report({ phase: "ready", note: "Ready" });
  },

  /** Stream the two big files so the progress bar can be truthful. */
  _prefetch: async function (report) {
    var sizes = [];
    var loaded = [];
    var responses = await Promise.all(BIG_FILES.map(function (name) {
      return fetch(PYODIDE_INDEX + name);
    }));
    responses.forEach(function (response, index) {
      sizes[index] = Number(response.headers.get("content-length") || 0);
      loaded[index] = 0;
    });
    var total = sizes.reduce(function (a, b) { return a + b; }, 0);

    await Promise.all(responses.map(async function (response, index) {
      if (!response.body) { await response.arrayBuffer(); return; }
      var reader = response.body.getReader();
      for (;;) {
        var chunk = await reader.read();
        if (chunk.done) break;
        loaded[index] += chunk.value.length;
        report({
          phase: "download",
          loaded: loaded.reduce(function (a, b) { return a + b; }, 0),
          total: total,
          note: "Downloading the Python runtime"
        });
      }
    }));
  },

  /** Copy the shim, the rubric and the harness into Pyodide's filesystem. */
  _writePylib: function () {
    var files = window.QUEST_PYLIB || {};
    var FS = this.pyodide.FS;
    Object.keys(files).forEach(function (path) {
      var full = "/lib/" + path;
      var parts = full.split("/").slice(1, -1);
      var walked = "";
      parts.forEach(function (part) {
        walked += "/" + part;
        try { FS.mkdir(walked); } catch (error) { /* already there */ }
      });
      FS.writeFile(full, files[path], { encoding: "utf8" });
    });
  },

  /**
   * Run one attempt.
   *
   * Resets the app to the challenge's scenario first, so a run never
   * inherits the state of the run before it - the same discipline the
   * kit asks of its own tests.
   */
  run: function (challenge, sources) {
    this.bridge.reset_app(JSON.stringify(challenge.scenario || {}));
    var payload = JSON.stringify({
      source: sources.main,
      cells: sources.cells || [],
      rubric: challenge.rubric || []
    });
    this.pyodide.globals.set("_quest_payload", payload);
    var raw = this.pyodide.runPython("harness.run(_quest_payload)");
    var result = JSON.parse(raw);
    result.snapshot = JSON.parse(this.bridge.snapshot());
    return result;
  },

  /** Ask the bridge what a recorded locator chain matches right now. */
  describeChain: function (chain) {
    return JSON.parse(this.bridge.describe(JSON.stringify(chain)));
  },

  /** Count elements for a plain CSS selector (used by the dom checks). */
  countCss: function (selector) {
    return this.bridge.count(JSON.stringify([{ k: "css", v: selector }]));
  }
};

function loadScript(url) {
  return new Promise(function (resolve, reject) {
    if (window.loadPyodide) { resolve(); return; }
    var script = document.createElement("script");
    script.src = url;
    script.onload = resolve;
    script.onerror = function () {
      reject(new Error(
        "Could not load " + url + ".\n" +
        "The Python runtime is not vendored yet - run:\n" +
        "    python site/fetch_vendor.py"
      ));
    };
    document.head.appendChild(script);
  });
}
