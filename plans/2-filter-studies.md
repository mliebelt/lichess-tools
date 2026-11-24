# Ticket 2: Filter studies

Ticket: https://github.com/mliebelt/lichess-tools/issues/2

API reference: [../lichess-apis.md](../lichess-apis.md). No new endpoint: the filter uses the `createdAt` and
`updatedAt` fields of `GET /api/study/by/{username}`, which are already documented there (epoch milliseconds, UTC).

## Goal

Let the user download only the studies that were **created** or **changed** since a given date, with two new
command line options for `studydl.py`.

This plan covers the ticket options "Created since" and "Changed since" only. The options "Type of studies" and
"Topics" are **out of scope**: they are blocked on Lichess (lila #22625 and lila #17480, see
[../TODO.md](../TODO.md)).

## Timestamp format and time zone

* Accepted value: a date as `yyyy-mm-dd`, for example `2026-11-24` — exactly 4-2-2 digits, so `2026-1-5` is
  rejected. No time part is accepted: the date means **00:00:00 UTC** of that day.
* Minute precision (`yyyy-mm-dd-hh-mm`, which the ticket called "normally sufficient") is deliberately **not**
  implemented (owner decision, 2026-11-24: day precision is sufficient). It can be added later without breaking
  any accepted value.
* Time zone: **UTC**, on every machine, no matter where the computer runs. The dates from Lichess are epoch
  milliseconds (UTC); reading the filter as UTC makes every result reproducible on every computer, in tests and
  in CI. The help text and the error message both say "UTC".
* "Since" is **inclusive**: a study whose `createdAt` / `updatedAt` is exactly at or after
  `yyyy-mm-dd 00:00:00 UTC` is kept.
* Both options together: a study must satisfy **both** conditions (AND). A date in the future is not an error;
  it simply matches nothing.

## CLI

```
studydl.py [-h] [--user NAME] [--type {own}] [--out DIR]
           [--created-since DATE] [--changed-since DATE]
           [--interactive|-i] [--dry-run|-n] [--overwrite]
```

New options (`metavar="DATE"`, stored as epoch milliseconds UTC), with the help text as shown by `--help`:

* `--created-since DATE`  only studies created on this date or later (yyyy-mm-dd, UTC)
* `--changed-since DATE`  only studies updated on this date or later, using the study list field `updatedAt`
  (yyyy-mm-dd, UTC)

New examples for the `--help` epilog:

```
Only the studies created since the year 2026 (UTC):
  studydl.py --created-since 2026-01-01

Only the studies that changed since 2026-11-01, without saving anything:
  studydl.py --changed-since 2026-11-01 --dry-run
```

A value like `2026-11-24` starts with a digit, so argparse never mistakes it for an option; the plain
`--created-since 2026-11-24` form works.

## Error messages for wrong input

The conversion happens in an argparse `type` function that raises `argparse.ArgumentTypeError`; argparse prints
the message below and exits with code 2 (the usage-error code `studydl.py` already uses for unknown options):

```
studydl.py: error: argument --created-since: expected a date as yyyy-mm-dd (for example 2026-11-24), got '2026-13-99'
```

The same text is used for `--changed-since` (argparse names the option itself). Rejected values include:
empty string, `2026-11`, `2026-1-5`, `2026-11-24-09-15`, `2026-11-24T09:00`, `24-11-2026`, `2026-13-01`,
`2026-02-30`, `today`. A wrong calendar day such as `2026-02-30` is caught by `datetime.strptime` after the
strict `^\d{4}-\d{2}-\d{2}$` regex check.

A correct date that matches nothing is **not** an error — see flow step 4 (exit code 0 with a clear message).

## Flow

1. New pure function `parse_since_date(text) -> int`: strict regex `^\d{4}-\d{2}-\d{2}$`, then
   `datetime.strptime`, the day is interpreted as 00:00:00 UTC, returned as epoch milliseconds; on failure it
   raises `argparse.ArgumentTypeError` with the message from the section above.
2. Two `parser.add_argument` calls with `type=parse_since_date` and `metavar="DATE"` (default `None`).
3. New pure function `filter_studies(studies, created_since=None, changed_since=None) -> list`: keeps the
   studies with `createdAt >= created_since` and `updatedAt >= changed_since` (skipping a `None` condition), in
   the original API order. A study whose relevant field is missing or not a number drops out of a filtered run
   (defensive; the API documents both fields as required).
4. In `run()`, directly after `list_studies`: if at least one option is given, apply the filter and print
   `Found {n} of {total} studies of {username} matching the since filter.` (without a filter the current
   `Found {n} studies of {username}.` stays as it is). If the filter matches nothing:
   `No studies of {username} match the since filter.` and exit code 0 — nothing is downloaded.
5. Everything after stays unchanged: interactive mode and dry run show only the matches, download, skip and
   summary logic are as before. `--user` works together with the filters as usual.

## Tests

### Unit tests (offline) — `tests/test_studydl.py`

* New `SinceDateTest` for `parse_since_date`:
  * `2026-11-24` -> `1795478400000` (exact epoch milliseconds for 2026-11-24T00:00:00Z).
  * For every wrong input (`""`, `2026-11`, `2026-1-5`, `2026-11-24-09-15`, `2026-11-24T09:00`, `24-11-2026`,
    `2026-13-01`, `2026-02-30`, `today`) an `ArgumentTypeError` whose message contains `yyyy-mm-dd`.
* New `FilterStudiesTest` for `filter_studies` (small local fixture, direct calls):
  * created filter keeps the boundary value and later, drops earlier;
  * changed filter likewise with `>=`;
  * both options together behave as AND;
  * no option returns the list unchanged (same order);
  * a study without `updatedAt` drops out of a changed-filter run.
* Parser tests: `--created-since 2026-01-01` stores `1767225600000`; a wrong value raises `SystemExit` with
  code 2 and prints `yyyy-mm-dd` and the option name on stderr.
* `RunTest` additions (with `FakeApi`): the fixture studies in `STUDIES` get **different** `createdAt` values
  (today all three share one; `updatedAt` values already differ) so that one cutoff date matches only the newest
  studies. No existing test asserts anything about `createdAt`, so none breaks. New cases:
  * `--created-since` matching only some studies -> only those `.pgn` files are written, no call for the others;
  * `--changed-since` between two `updatedAt` values -> only the newer ones are saved;
  * a future date -> exit code 0, no `.pgn` call, output mentions the filter miss;
  * `--dry-run` with a filter lists only the matches.
* `test_help` also expects `--created-since` and `--changed-since` in the `--help` output.

### Feature tests (live) — `tests/test_studydl_live.py`

Skipped unless `LICHESS_PAT` is set; output is silenced as today (study titles must not reach the CI log). All
fixed dates, never "now", so the tests are not time dependent:

* `--created-since 2000-01-01` with `--dry-run`: the count of "Would save" lines equals the number of studies
  from `list_studies` (a very old date keeps everything); skip if the account has no studies.
* `--created-since 2099-01-01`, `--changed-since 2099-01-01`, and both together: exit code 0, no "Would save"
  lines, no files written.
* Inclusive boundary against the real API: take one study from the list, pass its `createdAt` day as
  `--created-since` (UTC) and check in the dry-run output that exactly this study is among the matches.

Invalid input needs no live test — argparse rejects it before any network call (covered by the unit tests).

## Files that change

| File | Change |
|---|---|
| `plans/2-filter-studies.md` | this plan |
| `studydl.py` | `parse_since_date`, `filter_studies`, the two new options, epilog examples, filter step and the two messages in `run()` |
| `tests/test_studydl.py` | `SinceDateTest`, `FilterStudiesTest`, parser/`RunTest`/`test_help` additions, `createdAt` values in the `STUDIES` fixture |
| `tests/test_studydl_live.py` | the three live tests above |
| `README.md` | examples for the new options; the "not yet available" sentence then lists only topics and contribute |
| `TODO.md` | next step 7 done, link to this plan |

`lichess-apis.md` does not change (no new endpoint). `LICENSE`, CI and `.gitignore` do not change.

## Open questions

1. The numbered list (interactive mode and `--dry-run`) shows id and update date but no creation date
   (`format_study_line`). Should it also show the creation date when `--created-since` is used?
   (Suggestion: yes, as a small extra step — needs a decision before implementation.)
2. Relative values like `today` or `-7d` would be convenient but are not in scope; add them later if wanted?
3. Minute precision can be reintroduced later without breaking accepted values — reopen only if day precision
   turns out to be too coarse.

## Later (not this ticket)

* `--id`, `--update` (via `Last-Modified`), topic filter, "studies I contribute to" — see [../TODO.md](../TODO.md).

## Status (2026-11-24)

Plan approved by the owner (UTC, `yyyy-mm-dd` only, inclusive boundary). Implemented 2026-11-24 as specified
here; open question 1 (showing the creation date in the numbered list) got no decision, so `format_study_line`
stayed unchanged.
