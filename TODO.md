# TODO / Notes

Last updated: 2026-11-22. Notes to continue the work on the next day.

## State of the work

* Repository is connected to GitHub (`origin`, branch `main`, tracking is set up).
* Ticket #1 (save studies): `studydl.py` is implemented and the unit tests pass (`python -m unittest discover -s tests`).
  The live tests (`tests/test_studydl_live.py`) are skipped without `LICHESS_PAT`. They were **not run yet**.
* **Nothing is committed yet.** Changed or new: `Claude.md`, `README.md`, `lichess-apis.md`, `plans/`, `studydl.py`,
  `tests/`, `TODO.md`.
* Plan and decisions: [plans/1-save-studies.md](plans/1-save-studies.md). API facts: [lichess-apis.md](lichess-apis.md).

## Findings of the topic experiment (why there is no `--topic`)

* Checked with `curl` for the study `GFzdt4yP`: neither the headers (`HEAD`/`GET /api/study/{id}.pgn`) nor the PGN tags
  nor the study list (`GET /api/study/by/{username}`: only `id`, `name`, `createdAt`, `updatedAt`) contain the topics.
* The word "Mannschaft" only appeared in chapter `Event` tags and comments, which is not the topic.
* The official API docs have no endpoint for topics (searched for "topic" / "theme"). Looks like a missing feature.
* Related upstream issue (overlapping, but no topics in the metadata): https://github.com/lichess-org/api/issues/157
* Useful for later: `Last-Modified` header (for an `--update` option that skips unchanged studies); the PGN download also
  works for studies of other users.

## Next steps

1. [ ] Try the tool with a real token: `python studydl.py --dry-run`, then `python studydl.py -i --out /tmp/studies`.
   * A `studies/` folder (default output of `studydl.py`) now exists in the repo. It may hold private studies: add
     `studies/` to `.gitignore` **before** the first commit, and do not `git add` it.
2. [ ] Run all tests including the live ones: `LICHESS_PAT=... python -m unittest discover -s tests`.
3. [ ] Use a separate token with **only** the scope `study:read` for the tools (the current one has many more scopes).
4. [ ] Split ticket #1 (by the owner): move the topic filter into a new ticket, "blocked: Lichess does not expose topics".
       Update the text of #1 (v1 = own studies, list, interactive, dry-run, no topics). The type "studies I contribute to"
       is also not in v1.
5. [ ] Decide: `Claude.md` says plans are named `plans/ticket-<NR>.md`, the file is `plans/1-save-studies.md`.
       Change the rule or rename the file.
6. [ ] Commit (project commit conventions) and push: `git push`. Suggestion: one commit for docs and API reference, one
       for the tool and the tests.
7. [ ] Set up GitHub CI (postponed on purpose, only now):
   * `.github/workflows/test.yml` on push and pull request, matrix ubuntu / windows / macos, run
     `python -m unittest discover -s tests`.
   * GitHub repo → Settings → Secrets and variables → Actions → new secret `LICHESS_PAT` (token with `study:read` only).
     Pass it in the workflow as `env: LICHESS_PAT: ${{ secrets.LICHESS_PAT }}`. Secrets are not available to pull
     requests from forks, the live tests skip themselves then.
8. [ ] Optional: raise a feature request at Lichess ("add `topics` to the studies list metadata", see issue 157 above), or
       look at the server code (Scala, repo `lila`) to implement it. Check the existing issues for duplicates first.

## Ideas for later (no tickets yet)

* Type "studies I contribute to" (needs a documented way to list them).
* Topic filter (needs topics in the API, see above).
* `--update`: download only studies changed since the local file (`Last-Modified`).
