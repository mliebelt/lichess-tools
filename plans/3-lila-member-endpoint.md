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

1. [x] Done 2026-11-25: coursier launcher at `~/.local/bin/cs`, then `cs setup --yes --jvm temurin:21 --apps sbt` →
       Temurin **JDK 21.0.13.1** at `~/.cache/coursier/arc/.../jdk-21.0.13.1+2` and **sbt** at
       `~/.local/share/coursier/bin/sbt`. cs setup wrote the PATH/JAVA_HOME exports to `~/.zprofile` (login shells only —
       `~/.zshrc` does not source it and we did not change that). So **every build command must start with
       `. ~/.zprofile &&`** (or open a login shell). `sbt --version` and `java -version` verified.
2. [x] Done 2026-11-25: fork https://github.com/mliebelt/lila, clone at `~/priv/dev/lila` (no git submodules anymore on
       master). Branch `study-member-api` from master (47948db658). Remotes: `origin` = fork, `upstream` =
       `https://github.com/lichess-org/lila` with **push URL DISABLED**. Hooks active: `core.hooksPath=bin/git-hooks`
       (the lila `add-hooks` equivalent; its `pre-commit` runs `pnpm exec lint-staged` on staged files, a no-op for our
       Scala-only diff). lila pins `pnpm@12.9.0`: **solved** — after the node upgrade below, `corepack enable` was run
       on the default node, so bare `pnpm` in the clone resolves to the pinned 12.9.0 automatically.
       **Node update 2026-11-25:** `ui/build` needs node >= 24.20.0 (from `.node-version`; installed was nvm's
       24.16.0). Fixed with the owner's own tool: `nvm install 24` → **v24.22.3**, `nvm alias default 24`. In
       **already open** terminals run `nvm use default` first; new terminals get it automatically.
       **git-lfs:** the LFS filter problem is **solved** — owner installed `git-lfs 3.8.1` via pacman on 2026-11-25;
       plain `git status` in the clone is exit 0 and clean. The LFS image files are still **pointer stubs** in the
       working tree (fine for Scala/API work); run `git lfs pull` only if the real images are ever wanted.
3. [x] Done 2026-11-25: MongoDB 8 + Redis 7 up (containers `lila-dev-mongo`, `lila-dev-redis`, ports bound to
       127.0.0.1 only), compose file + `start`/`stop` helpers in `~/priv/dev/lila-dev-services/`, indexes from
       `bin/mongodb/indexes.js` loaded into the `lichess` database (exit 0). lila `conf/base.conf` expects exactly
       `mongodb://127.0.0.1:27017` and `redis://127.0.0.1` — matches.
4. [x] Done 2026-11-25: `./lila.sh compile` → **`[success] elapsed time: 98 s`**, 0 errors (the disk cache made it
       fast). `ui/build` does exist and is the UI asset build (a wrapper doing `pnpm install` in `ui/.build` and
       bundling) — **not needed for `compile`**, but expected once before `run` to serve the web pages; not yet run.
       (An earlier "the wiki is stale" note here was wrong: it came from the broken first checkout missing `ui/`.) `corepack pnpm install` → green in 3 s with the pinned pnpm 12.9.0. `./lila.sh scalafmtAll` → success
       in 7 s, 100% cache, **no file changed** (master is formatted per its own `.scalafmt.conf`; our future diff will
       contain only our changes).
       Note for all later sessions: build commands need `. ~/.zprofile &&` first (see step 1). Git in the clone is
       fully normal now (git-lfs installed, see step 2).

Environment summary at the end of the setup session (2026-11-25): **compile is green**, the branch `study-member-api`
is checked out and untouched, everything above is verified. The docker services were **stopped** at session end
(`~/priv/dev/lila-dev-services/stop`) — start them again with `~/priv/dev/lila-dev-services/start` before running the
server (not needed for `compile`). **Next session: start at step 5** (implement the endpoint), remembering
`. ~/.zprofile &&` before java/sbt commands (node/pnpm need nothing, nvm default is current).

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

* **Websockets / "Reconnecting" (2026-11-25):** the local server first ran **without** the separate websocket server —
  the UI then shows a permanent red "Reconnecting" and study **share/member management does not work** (it runs over the
  socket). Topology: `lila <-> redis <-> lila-ws <-> websocket <-> browser`. Setup: cloned `lichess-org/lila-ws` to
  `~/priv/dev/lila-ws`; its defaults already fit (ports `9664`, `csrf.origin = http://localhost:9663`, localhost
  redis/mongo). Start: `cd ~/priv/dev/lila-ws && . ~/.zprofile && sbt` then `~reStart`.
* **Browser URL:** must be `http://localhost:9663`, not `127.0.0.1:9663` — lila's `net.socket.domains` is
  `localhost:9664` and lila-ws's CSRF origin is `http://localhost:9663`; the host must match for cookies and socket.
* First local data (owner session): two users registered via signup, studies created in the UI. Signup works on the dev
  instance without special config.
