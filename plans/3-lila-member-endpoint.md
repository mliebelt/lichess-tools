# Ticket 3: the Lichess member endpoint — our own pull request

Github ticket: https://github.com/mliebelt/lichess-tools/issues/3. This file is the living log of the work: setup results,
implementation notes, PR links. The work itself happens in the `lila` repository (clone at `~/priv/dev/lila`), not here.

## Goal and decision

We asked Lichess for a way to list the studies a user is a member of: https://github.com/lichess-org/lila/issues/22625
(draft of the request: [2-support-member-search.md](2-support-member-search.md)). On 2026-11-25 the maintainer `ornicar`
answered https://github.com/lichess-org/lila/issues/22625#issuecomment-7159995161:

> I think I'll go with "a new endpoint for the authenticated user, for example GET /api/study/member (mirrors 'Studies I
> contribute to')"

So the shape is fixed: **`GET /api/study/member`**, authenticated only. We write the pull request ourselves (our answer in
the issue: "I will see when I will be able to work on the PR then").

## Facts from the lila source (verified against `master` on 2026-11-25, via the GitHub API)

* Route file `conf/routes`, lines 267 to 275, hold the study API routes. `GET /api/study/member` collides with nothing:
  the id routes require 8 characters (`\w{8}`) or a `.pgn` suffix.
* The pattern to copy is `apiListByOwner` in `app/controllers/Study.scala` (line 528):

  ```scala
  def apiListByOwner(username: UserStr) = OpenOrScoped(_.Study.Read, _.Web.Mobile): ctx ?=>
    val isMe = ctx.is(username)
    apiC.jsonDownload:
      env.study.studyRepo
        .sourceByOwner(username.id, isMe)
        .throttle(if isMe then 50 else 20, 1.second)
        .map(lila.study.JsonView.metadata(_, getBool("topics")))
  ```

  The new action uses `Scoped(_.Study.Read)` (no open path, the caller must be authenticated) and
  `sourceByMember(me.id, isMe = true)`.
* `StudyRepo.sourceByMember(memberId, isMe, select)` already exists (`modules/study/src/main/StudyRepo.scala:104`); with
  `isMe = true` it does not add `selectPublic`, so it returns studies of all visibilities. The website's
  "Studies I contribute to" goes through `env.study.pager.mineMember` (controller `mineMember`, line 108) — during
  implementation check whether that pager excludes owned studies, and mirror whatever the website tab shows.
* CONTRIBUTING.md asks for: small focused PRs, an explanation why the change is needed, "proof of human testing", and a
  draft PR if the code was not run. Formatting: `scalafmtAll` in the sbt console, `pnpm format` / `pnpm lint`, `pnpm
  add-hooks` for pre-commit hooks.

## Development environment (setup in this session, results below)

Prerequisites per the lila wiki: JDK >= 21, coursier >= 2 (provides sbt), node >= 24, pnpm (corepack), MongoDB 6 to 8,
Redis, >= 8 GB RAM. On this machine node 24.16 and pnpm 11.3 are already present, 30 GB RAM, docker available; java, sbt,
mongod and redis were missing.

## Steps

### Setup (done in the first session, 2026-11-25)

1. [ ] Toolchain, user-local without sudo: coursier to `~/.local/bin/cs`, `cs java --jvm temurin:21 --setup`, sbt via
       coursier.
2. [ ] Fork `lichess-org/lila` to `mliebelt/lila` (`gh repo fork`), `git clone --recursive` to `~/priv/dev/lila`
       (recursive for the scalachess submodule), remotes `origin` (fork) and `upstream` (push disabled), branch
       `study-member-api`, `pnpm add-hooks`.
3. [ ] MongoDB 8 and Redis 7 via docker compose, kept **outside** the clone in `~/priv/dev/lila-dev-services/` with
       `start`/`stop` helpers; load `bin/mongodb/indexes.js` into the `lichess` database.
4. [ ] `ui/build`, then `./lila.sh compile` until green; `scalafmtAll` once.

### Implementation (next sessions)

5. [ ] Route + action `apiListMember` as described above; keep the diff small (no owner/visibility fields in the first
       PR, that is `JsonView.metadata` as is — extra fields stay a follow-up wish on the issue).
6. [ ] Manual test on the local server: two users, a private study where user B is member of a study of user A, PAT from
       `/account/token`, `curl -H "Authorization: Bearer ..." http://127.0.0.1:9663/api/study/member` as B (must see the
       study) and check the answer without a token is 401.
7. [ ] Pull request `mliebelt/lila:study-member-api` to `lichess-org/lila`, referencing lila #22625.
8. [ ] Documentation PR in `lichess-org/api` (the OpenAPI description) once the endpoint is settled.

### Afterwards in our tools

9. [ ] Copy the new endpoint into `lichess-apis.md` first (project rule: new endpoints go there before they are used).
10. [ ] `studydl.py --member` to save "all studies I contribute to"; unit tests (mocked) and live test (needs a second
       account with a membership — decide how to cover this with the single `LICHESS_PAT`).

## What it would give our tools

* `studydl.py --member`: the original use case of ticket #2 option 1 — save all studies a user contributes to, which is
  impossible with today's API (see [2-support-member-search.md](2-support-member-search.md)).
* `--id` becomes a lot less painful: the user no longer needs to pick ids by hand for contributed studies.
* Nothing in the tools may use the endpoint before it is merged and deployed (rule: authoritative source is
  `lichess.org/api`; keep a feature branch or a "not released yet" note until then).

## Notes and findings during the work

(to be filled)
