# Ticket 2 (idea): a study topic API for Lichess

Collection of ideas, research and open questions. Nothing here is decided. Related files:

* [2-support-member-search.md](2-support-member-search.md): draft text of a separate feature request, only about listing the
  studies a user is a member of (no topics).
* Upstream issue: https://github.com/lichess-org/lila/issues/17480 "API: a study topic API" (open since 2025-05-06,
  label `study`). Wish there: (1) ask with a list of study ids and receive the topics of each, (2) set or clear a topic of
  a list of studies by ids. Idea behind it: "a folder structure UI could be built for studies".

> **Source of the facts below:** I read the source of `lichess-org/lila` (branch `master`, files `conf/routes`,
> `app/controllers/Study.scala`, `modules/study/...`, `ui/analyse/...`) on 2026-11-23 via the GitHub API. That is the
> implementation, **not** the official API documentation (`lichess.org/api`). It is used only to prepare a contribution to
> Lichess, not for our tools. The code may change, and it is not tested against production.

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

* **Reading:** a study has `topics: Option[StudyTopics]`. They are sent to the web UI as part of the study data, and
  nowhere else. The API list `GET /api/study/by/:user` (`Study.apiListByOwner` -> `JsonView.metadata`) writes only
  `id`, `name`, `createdAt`, `updatedAt`. Adding `topics` there is a one-line change in `JsonView.metadata`.
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

## Ideas for the API (to discuss, nothing decided)

Scopes: `study:read` for reading, `study:write` for changing. Lichess API style uses mostly `POST` for actions
(`POST /api/study/{id}/import-pgn`), so maintainers may prefer `POST` over `PUT`.

1. **Read the topics of one study:** `GET /api/study/{studyId}/topics` -> `{"topics": ["Endgames", "Club"]}`.
2. **Set (replace) the topics:** `POST /api/study/{studyId}/topics` with `topics=a&topics=b` (form like the other POST
   endpoints) or a JSON list. Same rules as the website: 2 to 50 characters, at most 30, needs `Contribute`.
3. **Add or remove single topics:** `POST /api/study/{studyId}/topics/{topic}` and `DELETE /api/study/{studyId}/topics/{topic}`;
   delete all with `DELETE /api/study/{studyId}/topics`. Does the same as the UI's edit, but without sending the whole list.
4. **Topics in the study list:** add `topics` to `StudyMetadata` (`GET /api/study/by/{username}`). This answers wish (1) of
   issue #17480 for all studies of an owner in one call, without a call per study. Possibly also `visibility` and the
   owner, and a query parameter `topic` to filter.
5. **Bulk for a list of ids (wish of #17480):** `POST /api/study/topics` with a list of ids (read), and a bulk write.
   Probably a later step, because it needs rate limits and a decision about partial failures.
6. **Member listing:** a separate request, see [2-support-member-search.md](2-support-member-search.md).
7. **PGN export:** an extra tag with the topics in `GET /api/study/{id}.pgn`. Probably the least wanted, because tags are
   per chapter.

Open design questions:

* Should writing topics also add them to the user's topic list, like the website does (`userTopicsAdd`)? Probably yes.
* Rate limits (a bulk change would cause `topicApi.recompute()` per study).
* Naming of the topic in URLs (spaces, special characters, case): body or query parameter is safer than a path segment.
* Which of the ideas is the smallest useful step? Suggestion: **4 (topics in the list)** and **1 (read)** first, because they
  are read-only and cause no new write path. Then 2 and 3.

## What it would give our tools

* `studydl.py --topic <name>` (ticket #2, option "Topics"): filter by topics, as soon as the list contains them.
* A new tool, for example `studytopics.py`, to read and set topics in bulk (for the "folder structure" idea of #17480),
  maybe from a local file.
* Not needed, but nice: `--member` listing for the "studies I contribute to" case.

## Steps

1. [ ] Read the contribution rules of `lila` (`CONTRIBUTING.md`, development setup) before writing code.
2. [ ] Comment on lila #17480 with the proposal, ask the maintainers which shape they prefer (smallest step: topics in the
       list and a read endpoint), and say if you would write the pull request. The comment text is not written yet
       (the draft in [2-support-member-search.md](2-support-member-search.md) is only about member search).
3. [ ] If they agree: set up a local `lila` (Scala 3 / Play), implement the smallest step, add the endpoint to
       the OpenAPI documentation (repo `lichess-org/api`), pull request.
4. [ ] Afterwards: use it in `studydl.py` (`--topic`), and copy the new endpoint into `lichess-apis.md` first, as the
       rules say.

## Not clear yet

* Whether a pull request from a first-time contributor is welcome for this, and how long it would take.
* Whether the maintainers consider topics part of the API at all (the discussion in #17480 only has a hint to use the
  API repo, and a reply that this repo is only for documentation).
