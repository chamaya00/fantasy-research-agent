# ADR 0001: Use pytest as the test runner

Date: 2026-09-14
Status: accepted

## Context

This pull request adds the first tests in the repository (fixture-backed
parsing of Yahoo Fantasy Sports API responses), which forces a choice of
test runner. `CLAUDE.md`'s Commands section already names `pytest` as what
`.github/workflows/ci.yml`'s placeholder gate is meant to be replaced with
once product code lands, so this decision was effectively pre-committed by
that file; this ADR records it formally because it is this repository's
first non-stdlib dependency of any kind.

## Decision

Use `pytest` as the test runner, added to `requirements.txt`, with
configuration in `pyproject.toml` (`pythonpath = ["."]` so `tests/` can
import the top-level `yahoo_data` package without an install step,
`testpaths = ["tests"]`). The library code under `yahoo_data/` itself stays
standard-library only (`urllib.request` for HTTP/OAuth) - this dependency is
for the test suite, not for talking to Yahoo, so it is orthogonal to
whether the real Yahoo client ever needs its own ADR.

## Consequences

Running the suite requires `pip install -r requirements.txt` first. Test
files can use plain `assert` and `pytest.raises` instead of
`unittest.TestCase` boilerplate. A human still needs to push the real
`pytest` check onto this pull request's branch and re-point branch
protection before merge, per the comment at the top of
`.github/workflows/ci.yml` - no agent may edit that file.

## Alternatives rejected

- **`unittest` (stdlib, no new dependency).** Would keep the repository at
  zero dependencies, but `CLAUDE.md` already commits the CI replacement to
  `pytest`; using `unittest` here would mean rewriting these tests again the
  moment that gate is wired up.
