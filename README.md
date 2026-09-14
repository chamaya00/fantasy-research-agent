# fantasy-research-agent

## Yahoo Fantasy Sports data layer

`yahoo_data/parsing.py` turns Yahoo Fantasy Sports API JSON (completed
matchups, waiver-wire/available players) into the `yahoo_data.models`
shapes the rest of the app consumes. It has no network dependency and is
tested entirely against recorded fixtures in `tests/fixtures/`.

`yahoo_data/client.py`'s `fetch_json` is the single entry point for the
real Yahoo API - it handles OAuth token acquisition from
`YAHOO_CLIENT_ID`/`YAHOO_CLIENT_SECRET`/`YAHOO_REFRESH_TOKEN` and returns
the same shape of dict a fixture does, so callers never see the OAuth
handshake.
