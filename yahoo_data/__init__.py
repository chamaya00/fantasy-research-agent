"""Data-access layer for Yahoo Fantasy Sports: parsing and the real API client.

See `client.fetch_json` for the single entry point that talks to the real
Yahoo API. Everything in `parsing` and `models` works against plain dicts
(as produced by `json.load`) and has no network dependency, so it can be
exercised entirely against recorded fixture responses.
"""
