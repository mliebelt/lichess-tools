# TODO / Notes

Last updated: 2026-11-23.

## State of the work

* Repository is connected to GitHub (`origin`, branch `main`, tracking is set up).
* Ticket #1 (save studies) is done: `studydl.py` with unit tests and live tests, CI runs on Linux, Windows and Mac
  (Python 3.10 and 3.13) and is green. The `LICHESS_PAT` secret lives in the GitHub environment `test`.
* `studies/` (default output folder of `studydl.py`) is in `.gitignore`.
* Plans: [plans/1-save-studies.md](plans/1-save-studies.md). API facts: [lichess-apis.md](lichess-apis.md).
* Ticket #2 (filter studies by additional parameters): https://github.com/mliebelt/lichess-tools/issues/2.
  Plan and implementation of "created since" / "changed since": [plans/2-filter-studies.md](plans/2-filter-studies.md).
  Ideas for a Lichess feature: [plans/2-study-topic-api.md](plans/2-study-topic-api.md)
  (research of the `lila` source, API ideas, steps).
* Member search request is **posted** (2026-11-23): https://github.com/lichess-org/lila/issues/22625
  "API: list the studies I contribute to (studies where I am a member)", open, no comments yet. The draft text is kept in
  [plans/2-support-member-search.md](plans/2-support-member-search.md) (the posted issue has extra explanations).

## Findings

### Topics (ticket #2, option "Topics") – not possible with the documented API

* Checked with `curl` for one study: neither the headers (`HEAD`/`GET /api/study/{id}.pgn`) nor the PGN tags nor the
  study list (`GET /api/study/by/{username}`: only `id`, `name`, `createdAt`, `updatedAt`) contain the topics.
* The word "Mannschaft" only appeared in chapter `Event` tags and comments, which is not the topic.
* The official API docs have no endpoint for topics (searched for "topic" / "theme").
* Existing upstream issue: https://github.com/lichess-org/lila/issues/17480 "API: a study topic API" (open since
  2025-05-06, label `study`): read the topics of studies by id, and set or clear them. In that issue a commenter said it
  should be opened on the API repo, and the author answered that the API repo is only for documentation, not code.
  So feature requests for the API probably belong to the `lila` repository.
* https://github.com/lichess-org/api/issues/157 ("API for Studies") is **not** related: it asks for creating studies and
  importing PGN into them.

### Type "studies I contribute to" (ticket #2, option 1) – not possible with the documented API

Experiment (2026-11-23), user A = owner account (with the token in `LICHESS_PAT`), user B = my own account, who is a
member of many private studies of A and of others:

* `GET /api/study/by/B` with A's token gave 18 studies, without any token also 18. After deleting one **public** study of B
  the call without token gave 17. So the list only contains the **public** studies; being a member of a non-public study
  does not add it, even though the docs say "If authenticated, then all public, unlisted, and private studies are included".
* Not tested: `GET /api/study/by/A` with a token of B (B is a member of private studies of A). Expected: only public ones.
* Requested at Lichess: https://github.com/lichess-org/lila/issues/22625 (open).
* The Lichess web page does it: "Studies I contribute to" = `GET https://lichess.org/study/search?q=member:<user>&order=hot`
  (`&page=2` for more). The answer is **HTML** (no JSON), rendered for the logged-in session (cookie, not a token). Each card has the
  study id, name, private flag, likes, owner, update time, the first chapters and the member list, but no topics.
  This is not an API, so per `Claude.md` we do not use it.
* The PGN download works for studies of other owners as well (private ones when the token's user is a member). That allows a
  workaround for later: `--id <studyId>` to save specific studies that the user picked in the web UI (not tested yet with
  a private study of another owner).

### Other

* Useful for later: `Last-Modified` header (for an `--update` option that skips unchanged studies).
* Created since / Changed since (ticket #2, options 3 and 4) are doable with `createdAt` / `updatedAt` of the study list.
  Open points: format (`yyyy-mm-dd`, `yyyy-mm-dd-hh-mm`), time zone (suggestion: UTC).

## Next steps

1. [x] Ticket #1 finished, CI set up (see above).
2. [x] Plan file naming rule changed in `Claude.md` to `plans/<NR>-<meaningful-title>.md`.
3. [x] Split ticket #1: the topic filter and more are now in ticket #2.
4. [x] Member search feature request posted as lila #22625 (from the draft in
       [plans/2-support-member-search.md](plans/2-support-member-search.md)).
5. [ ] Watch lila #22625 for answers (maintainers may prefer another shape), and react.
6. [ ] Topics (**start of the next session**): [plans/2-study-topic-api.md](plans/2-study-topic-api.md) is reviewed and
       approved by the owner. Decide how to go on with the existing issue lila #17480 (for example a comment that asks which shape the maintainers prefer; smallest step: topics in the
       study list and a read endpoint). The comment text is not written yet.
7. [x] Plan for ticket #2 in `plans/2-filter-studies.md` (in plan mode first): "created since" and "changed since",
       approved by the owner and implemented 2026-11-24: `--created-since` and `--changed-since` in `studydl.py`
       with unit and live tests. `--id` not taken (stays "later"). Contributor type and topics stay blocked on Lichess.
8. [ ] Optional: look at the Lichess server code (Scala, repo `lila`) to implement the request as a pull request.
9. [ ] Tokens: the token for the tools has more scopes than `study:read`. This is accepted for now (later features will
       need broader scopes).

## Ideas for later (no tickets yet)

* Type "studies I contribute to" and topic filter: blocked on Lichess (see findings).
* `--update`: download only studies changed since the local file (`Last-Modified`).
* `--id`: save studies by id (works for studies of other owners that the token can see).
