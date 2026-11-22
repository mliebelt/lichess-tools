# Ticket 1: Save studies

Ticket: https://github.com/mliebelt/lichess-tools/issues/1

API reference: [../lichess-apis.md](../lichess-apis.md) (endpoints used: `GET /api/account`,
`GET /api/study/by/{username}`, `GET /api/study/{studyId}.pgn`).

## Goal

A script `studydl.py` that downloads the user's Lichess studies to the local file system, restricted by parameters, with an
interactive mode to skip unwanted studies.

## Scope of v1

* Own studies only (`--type own`). The type "contributor" is a follow-up.
* **No topic filter.** None of the documented endpoints exposes a study's topics (list metadata has only `id`, `name`,
  `createdAt`, `updatedAt`; PGN headers have no topics tag). Split into a separate ticket.
* One PGN file per study (all chapters), `<out>/<sanitized-name>-<id>.pgn`.
* Interactive mode: numbered list, answer with e.g. `1,3,5-7`, `all` or `q`.
* CI is postponed. The live tests read `LICHESS_PAT` from the environment only.

## CLI

```
studydl.py [-h] [--user NAME] [--type {own}] [--out DIR]
           [--interactive|-i] [--dry-run|-n] [--overwrite]
```

* `--user` whose studies to list; default: owner of the token (`GET /api/account`, field `username`).
* `--out` target directory, default `./studies`.
* `--interactive/-i` list matches, ask which to save.
* `--dry-run/-n` list what would be saved, write nothing.
* `--overwrite` by default existing files are skipped.
* `--help/-h` description, all options, examples, and how to create `LICHESS_PAT` (scope `study:read`).

## Flow

1. Read `LICHESS_PAT` from the environment; if missing, explain how to create and set it (Linux/Mac, Windows), exit non-zero.
2. Resolve the user name (`--user` or `GET /api/account`).
3. `GET /api/study/by/{username}` (NDJSON) gives the list.
4. If interactive, show the list and parse the selection.
5. `GET /api/study/{id}.pgn` for each selected study, write the file (names sanitized for Windows).
6. Clear messages and non-zero exit for 401/403 (token or scope), 404, 429 (wait and retry), network errors.
7. Summary: saved / skipped / failed.

## Tests

* Unit tests, no network: `tests/test_studydl.py` (selection parser, filename sanitizing, NDJSON parsing, error mapping,
  missing token, `--help`).
* Feature tests: `tests/test_studydl_live.py`, skipped unless `LICHESS_PAT` is set.
* Run locally: `python -m unittest discover -s tests`.

## Later (not v1)

* Topic filter (needs a documented source of topics), contributor type, `--update` using `Last-Modified`.

## Status (2026-11-22)

Implemented: `studydl.py` and the tests (unit tests pass, live tests not run yet). Not committed yet. Open steps and
the findings about topics are in [../TODO.md](../TODO.md).
