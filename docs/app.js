import { MATCHUP_SUMMARY_URL, WAIVER_RECOMMENDATIONS_URL } from "./config.js";
import { matchupSectionHtml, waiverSectionHtml } from "./render.js";

/**
 * Fetches `url`, POSTing an empty JSON body (both routes take a Yahoo
 * payload shaped like the fixtures under tests/fixtures/ - see
 * docs/decisions/0004-fastapi-for-http-endpoints.md's "Consequences" for why
 * this page cannot supply a real one yet), and resolves to the `result`
 * shape `render.js`'s `*SectionHtml` functions expect.
 */
function fetchSection(url) {
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: "{}",
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`${url} responded with status ${response.status}`);
      }
      return response.json();
    })
    .then((data) => ({ status: "loaded", data }))
    .catch(() => ({ status: "error" }));
}

function loadMatchupSummary() {
  const content = document.getElementById("matchup-content");
  content.innerHTML = matchupSectionHtml({ status: "loading" });
  fetchSection(MATCHUP_SUMMARY_URL).then((result) => {
    content.innerHTML = matchupSectionHtml(result);
  });
}

function loadWaiverRecommendations() {
  const content = document.getElementById("waiver-content");
  content.innerHTML = waiverSectionHtml({ status: "loading" });
  fetchSection(WAIVER_RECOMMENDATIONS_URL).then((result) => {
    content.innerHTML = waiverSectionHtml(result);
  });
}

// Event delegation so a Retry button rendered into either section's content
// (replaced wholesale on every load) always has a working click handler,
// without re-attaching listeners after each re-render. Each button only
// re-fires its own section's request - see render.js's `data-retry` values.
document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-retry]");
  if (!button) return;
  if (button.dataset.retry === "matchup") loadMatchupSummary();
  if (button.dataset.retry === "waiver") loadWaiverRecommendations();
});

loadMatchupSummary();
loadWaiverRecommendations();
