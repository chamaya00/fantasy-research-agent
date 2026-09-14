import { test } from "node:test";
import assert from "node:assert/strict";

import { matchupSectionHtml, waiverSectionHtml } from "../render.js";

// Criterion 1: happy-path rendering, with data shaped like a completed
// matchup and a non-empty waiver wire.

test("matchup summary: loaded state shows team names, final score, and the AI summary", () => {
  const html = matchupSectionHtml({
    status: "loaded",
    data: {
      status: "ok",
      home_team: "Gridiron Gurus",
      away_team: "Fumble Fanatics",
      home_score: 112.4,
      away_score: 97.8,
      summary:
        "The Gridiron Gurus edged out the Fumble Fanatics 112.4 to 97.8, powered by Patrick Mahomes' big day.",
    },
  });

  assert.match(html, /Gridiron Gurus/);
  assert.match(html, /Fumble Fanatics/);
  assert.match(html, /112\.4/);
  assert.match(html, /97\.8/);
  assert.match(html, /Patrick Mahomes/);
});

test("waiver wire: loaded state shows a ranked, reasoned list in the backend's order", () => {
  const html = waiverSectionHtml({
    status: "loaded",
    data: {
      recommendations: [
        { player_id: "1", name: "Jaylen Warren", position: "RB", reason: "Lead back with a soft next matchup." },
        { player_id: "2", name: "Rome Odunze", position: "WR", reason: "Target share trending up three weeks running." },
      ],
    },
  });

  const warrenIndex = html.indexOf("Jaylen Warren");
  const odunzeIndex = html.indexOf("Rome Odunze");
  assert.ok(warrenIndex !== -1 && odunzeIndex !== -1);
  assert.ok(warrenIndex < odunzeIndex, "list order must match the backend's order, not be re-sorted");
  assert.match(html, /RB/);
  assert.match(html, /Lead back with a soft next matchup\./);
  assert.match(html, /1\./);
  assert.match(html, /2\./);
});

// Criterion 2: one test per non-happy-path state.

test("matchup summary: loading state shows a labeled in-progress indicator", () => {
  const html = matchupSectionHtml({ status: "loading" });

  assert.match(html, /Loading/i);
  assert.match(html, /matchup summary/i);
});

test("waiver wire: loading state shows a labeled in-progress indicator", () => {
  const html = waiverSectionHtml({ status: "loading" });

  assert.match(html, /Loading/i);
  assert.match(html, /waiver/i);
});

test("matchup summary: no-matchup-yet state shows an explicit message, not a blank section", () => {
  const html = matchupSectionHtml({ status: "loaded", data: { status: "no_matchup" } });

  assert.match(html, /No matchup has finished yet this week/);
});

test("waiver wire: empty state shows an explicit message, not a blank section", () => {
  const html = waiverSectionHtml({ status: "loaded", data: { recommendations: [] } });

  assert.match(html, /No waiver-wire pickups worth recommending this week\./);
});

test("matchup summary: error state shows a plain-language failure message and a Retry control scoped to this section", () => {
  const html = matchupSectionHtml({ status: "error" });

  assert.match(html, /failed to load/i);
  assert.doesNotMatch(html, /Traceback|Error:|status \d\d\d/);
  assert.match(html, /data-retry="matchup"/);
});

test("waiver wire: error state shows a plain-language failure message and a Retry control scoped to this section", () => {
  const html = waiverSectionHtml({ status: "error" });

  assert.match(html, /failed to load/i);
  assert.doesNotMatch(html, /Traceback|Error:|status \d\d\d/);
  assert.match(html, /data-retry="waiver"/);
});
