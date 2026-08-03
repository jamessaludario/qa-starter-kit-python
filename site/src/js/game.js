/* XP, levels, badges, and which zones are open.
 *
 * The rule this file is built around: reward effort, never punish
 * slowness. There are no lives, no timers you can lose to, and no way
 * to go backwards. Hints cost XP, but never all of it - struggling for
 * ten minutes and then asking for help still pays better than not
 * trying.
 */

import { Store } from "./store.js";

export const Game = {
  content: null,

  init: function (content) {
    this.content = content;
    return this;
  },

  // -------------------------------------------------------------- levels

  level: function (xp) {
    var levels = this.content.game.levels;
    var current = levels[0];
    var next = null;
    for (var i = 0; i < levels.length; i++) {
      if (xp >= levels[i].xp) { current = levels[i]; next = levels[i + 1] || null; }
    }
    var floor = current.xp;
    var ceiling = next ? next.xp : current.xp;
    return {
      title: current.title,
      index: levels.indexOf(current),
      next: next,
      // 1 at the top level - the bar is full, not stuck.
      progress: next ? (xp - floor) / (ceiling - floor) : 1
    };
  },

  // ------------------------------------------------------------------ xp

  /** What one attempt is worth. `outcome` comes from the runner. */
  scoreFor: function (challenge, record, outcome) {
    if (!outcome.passed) return 0;
    var rules = this.content.game.xp;
    var base = challenge.xp || 20;
    var total = base;
    var reasons = [{ label: "Challenge cleared", xp: base }];

    if (record.attempts <= 1) {
      var bonus = Math.round(base * rules.firstTryBonus);
      total += bonus;
      reasons.push({ label: "First try", xp: bonus });
    }
    if (outcome.clean) {
      var clean = Math.round(base * rules.cleanBonus);
      total += clean;
      reasons.push({ label: "Clean review - no advisory findings", xp: clean });
    }
    var spent = (record.hints || []).reduce(function (sum, hint) {
      return sum + (hint.cost || 0);
    }, 0);
    if (spent) {
      total -= spent;
      reasons.push({ label: "Hints used", xp: -spent });
    }
    // The floor: asking for every hint still pays. Nobody should end a
    // challenge they solved with nothing to show for it.
    var floor = Math.round(base * rules.hintFloor);
    if (total < floor) {
      reasons.push({ label: "Minimum award", xp: floor - total });
      total = floor;
    }
    return { total: total, reasons: reasons };
  },

  // --------------------------------------------------------------- zones

  zoneChallenges: function (zoneId) {
    var zone = this.content.zones.filter(function (z) { return z.id === zoneId; })[0];
    return zone ? zone.challenges : [];
  },

  zoneProgress: function (zoneId) {
    var challenges = this.zoneChallenges(zoneId);
    var passed = challenges.filter(function (challenge) {
      return Store.isPassed(zoneId, challenge.id);
    });
    return {
      passed: passed.length,
      total: challenges.length,
      complete: challenges.length > 0 && passed.length === challenges.length
    };
  },

  isUnlocked: function (zone) {
    if (!zone.requires || !zone.requires.length) return true;
    var self = this;
    return zone.requires.every(function (required) {
      return self.zoneProgress(required).complete;
    });
  },

  lockReason: function (zone) {
    var self = this;
    var missing = (zone.requires || []).filter(function (required) {
      return !self.zoneProgress(required).complete;
    });
    var names = missing.map(function (id) {
      var found = self.content.zones.filter(function (z) { return z.id === id; })[0];
      return found ? found.title : id;
    });
    return names.length ? "Clear " + names.join(" and ") + " first." : "";
  },

  // -------------------------------------------------------------- badges

  BADGE_RULES: {
    challengesPassed: function (rule) {
      return Object.keys(Store.data.challenges).filter(function (key) {
        return Store.data.challenges[key].status === "passed";
      }).length >= rule.value;
    },
    firstTryPasses: function (rule) {
      return Object.keys(Store.data.challenges).filter(function (key) {
        var record = Store.data.challenges[key];
        return record.status === "passed" && record.attempts <= 1;
      }).length >= rule.value;
    },
    passedWithoutHints: function (rule) {
      return Object.keys(Store.data.challenges).filter(function (key) {
        var record = Store.data.challenges[key];
        return record.status === "passed" && !(record.hints || []).length;
      }).length >= rule.value;
    },
    statAtLeast: function (rule) {
      return (Store.data.stats[rule.stat] || 0) >= rule.value;
    },
    zoneCleared: function (rule, game) {
      return game.zoneProgress(rule.zone).complete;
    },
    zoneCleanOfSleep: function (rule, game) {
      var progress = game.zoneProgress(rule.zone);
      if (!progress.complete) return false;
      return game.zoneChallenges(rule.zone).every(function (challenge) {
        return !Store.record(rule.zone, challenge.id).sleepFlagged;
      });
    },
    bossesCleared: function (rule, game) {
      var count = 0;
      game.content.zones.forEach(function (zone) {
        zone.challenges.forEach(function (challenge) {
          if (challenge.boss && Store.isPassed(zone.id, challenge.id)) count++;
        });
      });
      return count >= rule.value;
    }
  },

  /** Re-check every badge. Returns the ones newly earned, for the toast. */
  refreshBadges: function () {
    var self = this;
    var earned = [];
    this.content.game.badges.forEach(function (badge) {
      if (Store.data.badges[badge.id]) return;
      var check = self.BADGE_RULES[badge.rule.type];
      if (check && check(badge.rule, self) && Store.award(badge.id)) {
        earned.push(badge);
      }
    });
    return earned;
  },

  badgeById: function (id) {
    return this.content.game.badges.filter(function (b) { return b.id === id; })[0];
  }
};
