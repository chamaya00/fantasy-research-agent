/**
 * Endpoint URLs for the Modal backend's HTTP routes (backend/app.py's `web`
 * function, docs/decisions/0004-fastapi-for-http-endpoints.md). `modal
 * deploy backend/app.py` prints the base URL for `web` on deploy - fill it
 * in below. See CLAUDE.md's Commands section.
 */
const BASE_URL = "https://REPLACE-ME.modal.run";

export const MATCHUP_SUMMARY_URL = `${BASE_URL}/matchup-summary`;
export const WAIVER_RECOMMENDATIONS_URL = `${BASE_URL}/waiver-recommendations`;
