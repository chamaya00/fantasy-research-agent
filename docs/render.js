/**
 * Pure, DOM-free rendering functions for the single-page flow's two sections
 * (docs/design/5-matchup-and-waiver-page.md). Each `*SectionHtml` function
 * takes a plain-data `result` describing what happened and returns the HTML
 * string `docs/app.js` assigns to that section's content element - kept
 * separate from `app.js` so the four states each section can be in are
 * testable without a browser (see docs/tests/render.test.mjs).
 */

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function loadingHtml(label) {
  return `<p class="status status-loading" role="status">${escapeHtml(label)}</p>`;
}

function errorHtml(message, retryTarget) {
  return (
    `<p class="status status-error" role="alert">${escapeHtml(message)}</p>` +
    `<button type="button" class="retry" data-retry="${retryTarget}">Retry</button>`
  );
}

function matchupLoadedHtml(data) {
  const home = `${escapeHtml(data.home_team)} ${escapeHtml(String(data.home_score))}`;
  const away = `${escapeHtml(String(data.away_score))} ${escapeHtml(data.away_team)}`;
  return (
    `<p class="matchup-score">${home} &mdash; ${away}</p>` +
    `<p class="matchup-summary">${escapeHtml(data.summary)}</p>`
  );
}

function waiverLoadedHtml(recommendations) {
  const rows = recommendations
    .map(
      (rec, index) =>
        `<li>` +
        `<span class="rank">${index + 1}.</span> ` +
        `<span class="player-name">${escapeHtml(rec.name)}</span> ` +
        `<span class="player-position">${escapeHtml(rec.position)}</span>` +
        `<p class="reason">${escapeHtml(rec.reason)}</p>` +
        `</li>`
    )
    .join("");
  return `<ol class="waiver-list">${rows}</ol>`;
}

/**
 * `result` is one of:
 *   {status: "loading"}
 *   {status: "error"}
 *   {status: "loaded", data: <the matchup-summary endpoint's JSON body>}
 * where `data.status` is "no_matchup" or "ok" (see backend/app.py's `web`).
 */
export function matchupSectionHtml(result) {
  if (result.status === "loading") {
    return loadingHtml("Loading this week's matchup summary…");
  }
  if (result.status === "error") {
    return errorHtml("This section failed to load.", "matchup");
  }
  if (result.data.status === "no_matchup") {
    return `<p class="status status-empty">No matchup has finished yet this week — check back after games wrap up.</p>`;
  }
  return matchupLoadedHtml(result.data);
}

/**
 * `result` is one of:
 *   {status: "loading"}
 *   {status: "error"}
 *   {status: "loaded", data: <the waiver-recommendations endpoint's JSON body>}
 * where `data.recommendations` is a list, possibly empty.
 */
export function waiverSectionHtml(result) {
  if (result.status === "loading") {
    return loadingHtml("Loading waiver recommendations…");
  }
  if (result.status === "error") {
    return errorHtml("This section failed to load.", "waiver");
  }
  const recommendations = result.data.recommendations || [];
  if (recommendations.length === 0) {
    return `<p class="status status-empty">No waiver-wire pickups worth recommending this week.</p>`;
  }
  return waiverLoadedHtml(recommendations);
}
