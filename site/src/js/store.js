/* Progress: one object, in localStorage, exportable as a file.
 *
 * No accounts, ever. That is a deliberate constraint, not a shortcut -
 * it means the site can be a folder of static files, a learner needs no
 * permission from anyone to start, and there is no database of
 * children's names to lose. The cost is that progress is per-browser,
 * which the export/import buttons exist to solve.
 */

var KEY = "quest-for-automation.v1";

var EMPTY = {
  version: 1,
  xp: 0,
  challenges: {},        // "zone/challenge" -> record
  badges: {},            // badge id -> ISO date earned
  stats: { runs: 0, roleLocators: 0, sleepAttempts: 0, cleanRuns: 0 },
  streak: { days: 0, last: null },
  startedAt: null
};

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

export const Store = {
  data: clone(EMPTY),

  load: function () {
    try {
      var raw = window.localStorage.getItem(KEY);
      if (raw) {
        var parsed = JSON.parse(raw);
        // Merge rather than replace, so a save written by an older
        // version of the site still opens instead of throwing.
        this.data = Object.assign(clone(EMPTY), parsed);
        this.data.stats = Object.assign(clone(EMPTY.stats), parsed.stats || {});
        this.data.streak = Object.assign(clone(EMPTY.streak), parsed.streak || {});
      }
    } catch (error) {
      // Private mode, disabled storage, corrupt JSON: play anyway.
      this.data = clone(EMPTY);
    }
    if (!this.data.startedAt) this.data.startedAt = new Date().toISOString();
    this.touchStreak();
    return this.data;
  },

  save: function () {
    try {
      window.localStorage.setItem(KEY, JSON.stringify(this.data));
    } catch (error) {
      /* Nothing sensible to do - never break the lesson over storage. */
    }
    window.dispatchEvent(new CustomEvent("quest:progress"));
  },

  reset: function () {
    this.data = clone(EMPTY);
    this.data.startedAt = new Date().toISOString();
    this.save();
  },

  // ----------------------------------------------------------- challenges

  key: function (zoneId, challengeId) { return zoneId + "/" + challengeId; },

  record: function (zoneId, challengeId) {
    var key = this.key(zoneId, challengeId);
    if (!this.data.challenges[key]) {
      this.data.challenges[key] = {
        status: "todo", attempts: 0, hints: [], xp: 0, clean: false, virtualMs: 0
      };
    }
    return this.data.challenges[key];
  },

  isPassed: function (zoneId, challengeId) {
    return this.record(zoneId, challengeId).status === "passed";
  },

  // ---------------------------------------------------------------- badges

  award: function (badgeId) {
    if (this.data.badges[badgeId]) return false;
    this.data.badges[badgeId] = today();
    return true;
  },

  // ---------------------------------------------------------------- streak

  touchStreak: function () {
    var last = this.data.streak.last;
    var now = today();
    if (last === now) return;
    var yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
    this.data.streak.days = last === yesterday ? this.data.streak.days + 1 : 1;
    this.data.streak.last = now;
  },

  // ------------------------------------------------------- export / import

  exportBlob: function () {
    var payload = JSON.stringify(this.data, null, 2);
    return new Blob([payload], { type: "application/json" });
  },

  importText: function (text) {
    var parsed = JSON.parse(text);
    if (!parsed || typeof parsed !== "object" || !parsed.challenges) {
      throw new Error("That file does not look like a Quest progress export.");
    }
    this.data = Object.assign(clone(EMPTY), parsed);
    this.save();
    return this.data;
  }
};
