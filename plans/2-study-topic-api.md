# Ticket 2 (idea): a study topic API for Lichess

Collection of ideas, research and open questions. **The read half has since landed upstream — see "Current state"
below; the write half is still only ideas.** Related files:

* [2-support-member-search.md](2-support-member-search.md): draft text of a separate feature request, only about listing the
  studies a user is a member of (no topics).
* Upstream issue: https://github.com/lichess-org/lila/issues/17480 "API: a study topic API" (open since 2025-05-06,
  label `study`, still open on 2026-11-26). Wish there: (1) ask with a list of study ids and receive the topics of each,
  (2) set or clear a topic of a list of studies by ids. Idea behind it: "a folder structure UI could be built for
  studies". Wish (1) is partially served today via `?topics=true` on the two list endpoints (see below); wish (2) —
  writing — still has no API.

> **Source of the facts below:** I read the source of `lichess-org/lila` (branch `master`, files `conf/routes`,
> `app/controllers/Study.scala`, `modules/study/...`, `ui/analyse/...`) on 2026-11-23 via the GitHub API. That is the
> implementation, **not** the official API documentation (`lichess.org/api`). It is used only to prepare a contribution to
> Lichess, not for our tools. The code may change, and it is not tested against production.
> **Update 2026-11-26:** the facts after 2026-11-25 come from the local clone at `~/priv/dev/lila` (git log, diffs,
> `modules/study/src/main/StudyTopic.scala`), from our running dev server, and from anonymous prod API probes the same
> day — still source/probing, still **not** the official docs.

## Current state (2026-11-26): the read side has landed

* **2026-11-24** — we commented on lila #17480, proposing the two read-only first steps (topics in the study list =
  idea **4** below, plus a per-study read endpoint = idea 1) and asking whether an outside PR would be welcome.
* **2026-11-25** — the maintainer `ornicar` answered **with code**: commit
  https://github.com/lichess-org/lila/commit/47948db658a1678d14e97d41c1bcf82958e70ded "/api/study/by/{user} topics query
  param — for #17480", directly on master. `apiListByOwner` now passes `getBool("topics")` into `JsonView.metadata`,
  which appends `topics -> study.topicsOrEmpty`. So today on `master`:

  ```
  GET /api/study/by/{username}?topics=true
  {"id":"...","name":"...","createdAt":...,"updatedAt":...,"topics":["Endgames","Club"]}
  ```

  From the diff: an **opt-in query param** — without it the output is exactly as before; `topics` is a plain JSON
  **list of strings** (`StudyTopic` is an opaque `String`, 2 to 50 chars trimmed); with the param on, a study without
  topics gets `"topics": []`; with it off/absent the key is omitted. Works the same anonymous (public studies) and
  authenticated (own studies incl. unlisted/private) — one param on one route, no new scope, no per-study endpoint,
  and **nothing for writing**. Issue #17480 stays open.
* **Our member endpoint PR carries it too** — https://github.com/lichess-org/lila/pull/22653 (ticket 3,
  [3-lila-member-endpoint.md](3-lila-member-endpoint.md)): the branch is based on `47948db658` and `apiListMember`
  calls the same `JsonView.metadata(_, getBool("topics"))`, so **`GET /api/study/member?topics=true`** behaves exactly
  like on `by/{user}` — our diff does not touch `JsonView.scala`, the topics support comes free from master. Verified
  on the local dev instance (proof run 2026-11-25, confirmed again 2026-11-26):

  ```
  ./experiments/lila-api.sh -l raw GET "/api/study/member?topics=true"
  ```

  PR status on 2026-11-26: **OPEN, mergeable, no review yet**.
* **Docs caveat resolved 2026-11-26 — the param IS officially documented.** ornicar had documented it in the docs repo
  43 seconds **before** committing the code: https://github.com/lichess-org/api/commit/fd0c43efd7 "document new study
  metadata ?topics=1 param" (2026-11-25T11:00:07Z). `api-study-by-username.yaml` gained `in: query, name: topics,
  default: false` and the `StudyMetadata` schema gained the optional `topics: string[]`. Only our local mirror
  [../lichess-apis.md](../lichess-apis.md) is stale — it can be updated. (The old "docs do not mention it" note here
  came from the stale mirror, not from checking the docs repo.)
* **Prod rollout: confirmed NOT yet live (2026-11-26).** The confirming call ran (owner session, token of the club
  account `scstetten`), fixture `sIIGw2ry` with topics set in the web UI right before the call (its `updatedAt` is
  minutes old at call time):

  ```
  ./experiments/lila-api.sh raw GET "/api/study/by/scstetten?topics=true"
  -> HTTP 200, every study line in the OLD shape, e.g.
  {"id":"sIIGw2ry","name":"Schach-AG Springerdiplom >= S16","createdAt":...,"updatedAt":...}   # no topics key
  ```

  So prod runs a build older than `47948db658`: **the docs at `lichess.org/api` are ~1 day ahead of the server.**
  Three side findings: (1) the unknown query parameter is **silently ignored — nothing breaks**, so sending it is
  forward-compatible; (2) the ownership question is settled — `sIIGw2ry`, and the example study `nEP3M7IP` from the
  "Starting point" section, belong to `scstetten`, which is why the anonymous probes under `mliebelt` could not find
  them; (3) `/api/study/member` stays the clear half: not merged, so `member?topics=true` remains gated on #22653.
  **Next: repeat this one call in a few days to catch the rollout** — first `topics` line = green light, then refresh
  `lichess-apis.md` and `--topic` becomes usable.
* **What this unblocks:** a topic filter needs **no new endpoint at all** — fetch `by/{user}?topics=true` (and
  `member?topics=true` once #22653 ships) and keep the studies whose `topics` list contains the wanted name. That is a
  purely client-side filter in `studydl.py` (`--topic`), see [2-filter-studies.md](2-filter-studies.md) which so far
  lists "Topics" as blocked on Lichess.

## Starting point: the shape of the route

The example `https://lichess.org/study/nEP3M7IP/topics` shows the idea: topics are a sub-resource of a study, so the
REST API is `/api/study/{studyId}/topics`, and from there we can read, add, change and delete topics. That route does
**not** exist yet (it is not in `conf/routes`), so it is what we would propose. What exists today:

| Route (web, not documented API) | What it does |
|---|---|
| `POST /study/topic` (`Study.setTopics`) | Sets **my own** topic list (the user's favourite topics, `topicApi.userTopics(me, topics)`). It does **not** set the topics of a study. |
| `GET /study/topic` | HTML page: popular topics and my topics |
| `GET /study/topic/:topic/:order` | HTML: studies with this topic |
| `GET /study/topic/autocomplete` | JSON: topics matching a term (`term`, optional `user`) |

## How study topics work today (from the source)

* **Reading:** a study has `topics: Option[StudyTopics]`. Until 2026-11-25 they went to the web UI as part of the study
  data, and nowhere else — the API list `GET /api/study/by/:user` wrote only `id`, `name`, `createdAt`, `updatedAt`,
  and we noted "adding `topics` there is a one-line change in `JsonView.metadata`". That is precisely what ornicar's
  commit then did (as opt-in `?topics=true`, see "Current state" above).
* **Writing:** only through the **websocket** of the study page. The UI sends the message `setTopics` with a list of strings
  (`ui/analyse/src/study/studyCtrl.ts`, `StudySocket.scala`), which calls `StudyApi.setTopics(studyId, topics)(who)`:
  * needs the permission `Contribute` for the study (owner and members with contribute rights),
  * `StudyTopics.fromStrs(topics, studyMax)`: each topic 2 to 50 characters (trimmed), duplicates removed, at most
    **30 per study** (`studyMax`), at most 200 per user (`userMax`),
  * saves the study, adds the new topics to the **user's** topic list (`userTopicsAdd`), tells the other viewers
    (`setTopics` message) and recomputes the global topic list (`topicApi.recompute()`).
* **Visibility in lists:** `StudyRepo.sourceByOwner(ownerId, isMe)` adds `selectPublic` when the caller is not the owner.
  This confirms our experiment: a member of private studies of another user does not see them in `/api/study/by/<owner>`.
  There is also `sourceByMember(memberId, isMe, select)`, which the website uses for "Studies I contribute to"
  (`Study.mineMember`), so a member listing for the API could reuse it.
* **Pattern for a write endpoint:** existing API routes such as `DELETE /api/study/:id/:chapterId`
  (`Study.apiChapterDelete`) use `ScopedBody(_.Study.Write, _.Web.Mobile)` and call the study API with
  `Who(me.userId, Sri("api"))`. `Study.apiImportPgn` does the same. A topic endpoint can follow that pattern.

## Ideas for the API (status 2026-11-26: 4 landed upstream, 6 is our open PR, the rest are still ideas)

Scopes: `study:read` for reading, `study:write` for changing. Lichess API style uses mostly `POST` for actions
(`POST /api/study/{id}/import-pgn`), so maintainers may prefer `POST` over `PUT`.

1. **Read the topics of one study:** `GET /api/study/{studyId}/topics` -> `{"topics": ["Endgames", "Club"]}`. Not built;
   the list endpoints with `?topics=true` now cover the main use case, so this lost urgency.
2. **Set (replace) the topics:** `POST /api/study/{studyId}/topics` with `topics=a&topics=b` (form like the other POST
   endpoints) or a JSON list. Same rules as the website: 2 to 50 characters, at most 30, needs `Contribute`.
3. **Add or remove single topics:** `POST /api/study/{studyId}/topics/{topic}` and `DELETE /api/study/{studyId}/topics/{topic}`;
   delete all with `DELETE /api/study/{studyId}/topics`. Does the same as the UI's edit, but without sending the whole list.
4. **Topics in the study list:** **DONE upstream 2026-11-25** (commit `47948db658`), as opt-in `?topics=true` on
   `GET /api/study/by/{username}` rather than a default field. This answers wish (1) of issue #17480 for all studies of
   an owner in one call, without a call per study. Still open from the old wish list: `visibility` and the owner in the
   metadata, and a server-side `topic` query parameter to filter (our own client-side filter makes that one less needed).
5. **Bulk for a list of ids (wish of #17480):** `POST /api/study/topics` with a list of ids (read), and a bulk write.
   Probably a later step, because it needs rate limits and a decision about partial failures.
6. **Member listing:** our own pull request https://github.com/lichess-org/lila/pull/22653 (`GET /api/study/member`,
   ticket 3), open since 2026-11-25 — it reuses the new `?topics=true` on top. Background:
   [2-support-member-search.md](2-support-member-search.md).
7. **PGN export:** an extra tag with the topics in `GET /api/study/{id}.pgn`. Probably the least wanted, because tags are
   per chapter.

Open design questions:

* Should writing topics also add them to the user's topic list, like the website does (`userTopicsAdd`)? Probably yes.
* Rate limits (a bulk change would cause `topicApi.recompute()` per study).
* Naming of the topic in URLs (spaces, special characters, case): body or query parameter is safer than a path segment.
* Which of the ideas is the smallest useful step? Suggestion was: **4 (topics in the list)** and **1 (read)** first,
  because they are read-only and cause no new write path. — Answered by the maintainer on 2026-11-25: he built 4 (as an
  opt-in `?topics=true`), skipped 1, and left the write ideas (2, 3, 5) untouched. The three write-related questions
  above are still open.

## What it would give our tools

* `studydl.py --topic <name>` (ticket #2, option "Topics"): **feasible now, client-side** — request
  `by/{user}?topics=true` (and `member?topics=true` once #22653 ships) and keep the studies whose `topics` list contains
  the wanted name; no new endpoint needed. Docs are already in, prod is pending (the param is ignored there today
  without breaking anything — see "Current state"), so `--topic` must refuse to trust a silent miss: while the
  server ignores the param, every study reads as "no topics" and a filter would match **nothing** — the tool should
  detect that case (asked for `--topic` but zero of N studies have a `topics` key at all) and warn instead of
  reporting "no match". Matching detail: topics are free text (2 to 50 chars, trimmed, case kept as typed), so the
  filter should compare case-insensitively and probably trimmed.
* A new tool, for example `studytopics.py`, to read and set topics in bulk (for the "folder structure" idea of #17480),
  maybe from a local file: the **read** part is feasible like above; the **set** part still needs a write endpoint that
  does not exist yet.
* Not needed, but nice: `--member` listing for the "studies I contribute to" case — that is our own PR #22653 (ticket
  3), and it supports `?topics=true` from the start.

## Steps

1. [x] Read the contribution rules of `lila` (`CONTRIBUTING.md`, development setup) before writing code.
2. [x] Comment on lila #17480 — done 2026-11-24: proposed topics-in-the-list plus a per-study read endpoint, asked
       which shape they prefer and whether an outside PR is welcome. The maintainers answered with code: ornicar
       committed `?topics=true` on `by/{user}` to master on 2026-11-25 (`47948db658`, "for #17480").
3. [ ] Nothing to implement here for the read field — ornicar built it **and documented it** (docs commit
       `fd0c43efd7`, see "Current state"). Waiting on: (a) the prod rollout itself — the confirming call ran
       2026-11-26 and prod still ignores the param (old build); repeat that one call until a line shows `topics`,
       (b) the review and docs of our `GET /api/study/member` PR #22653 (tracked in ticket 3). If a **write**
       endpoint (ideas 2/3/5) is still wanted, that needs a new follow-up comment on #17480.
4. [ ] Afterwards: copy the `topics` param (and the member endpoint) into `lichess-apis.md` first, as the rules say,
       then implement `studydl.py --topic` as a client-side filter over the fetched list.

## Not clear yet

* ~~Whether a pull request from a first-time contributor is welcome~~ — answered: #22653 was opened without pushback
  (mergeable, review pending), and the read feature was built by the maintainer himself. How long the **review** of
  #22653 takes is still open.
* ~~Whether the maintainers consider topics part of the API at all~~ — answered for **reading**, twice on 2026-11-25:
  the code commit and the docs commit 43 seconds apart. Open: whether they ever want the **write** side (wish 2 of
  #17480 — set/clear via API), and **when the prod rollout lands** — confirmed still pending on 2026-11-26; lichess
  normally rolls master out within a day, so the test call should start working soon.
