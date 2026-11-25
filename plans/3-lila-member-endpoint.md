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

### Implementation

5. [x] Code written (committed as `cc5411177b`), **12 added lines in 3 files**, compiles green (11 s incremental),
   scalafmt clean:
   * `conf/routes`: `GET /api/study/member controllers.Study.apiListMember` (directly after the `by/:user` line)
   * `modules/study/src/main/StudyRepo.scala`, after `sourceByMember`:

     ```scala
     def sourceContributed(memberId: UserId): Source[Study, ?] =
       sourceByMember(memberId, isMe = true, select = bdoc("ownerId".neq(memberId)))
     ```

   * `app/controllers/Study.scala`, after `apiListByOwner`:

     ```scala
     def apiListMember = Scoped(_.Study.Read) { ctx ?=> me ?=>
       apiC.jsonDownload:
         env.study.studyRepo
           .sourceContributed(me.userId)
           .throttle(50, 1.second)
           .map(lila.study.JsonView.metadata(_, getBool("topics")))
     }
     ```

   Idioms copied from `RelayRound.apiMyRounds` (Scoped + given `Me`) and `StudyPager.mineMember` (the `ownerId != me`
   predicate). Kept minimal: NDJSON `JsonView.metadata` as is, no extra fields (owner/visibility stay a follow-up wish
   on the issue).
   **Design decision from live comparison (2026-11-25):** the first version used plain `sourceByMember` and returned
   owned studies too (user A saw 3 studies); the website tab "Studies I contribute to" shows only the foreign ones
   (2 studies). ornicar said "mirrors Studies I contribute to" → owned are **excluded**, hence `sourceContributed`.
   The edge case "user with only own studies" returns HTTP 200 with zero lines — correct.
   Committed on `study-member-api` as `cc5411177b` after the step-6 re-test, subject
   "GET /api/study/member for the studies the user contributes to".
6. [x] Manual test on the local server passed (2026-11-25), done with `experiments/lila-api.sh` + local tokens from
       `/account/token`: no token → **401 Missing authorization header**; A's token → only A's **foreign** studies (owned
       excluded); `study/by/<user>` contrast verified for public vs unlisted; the website tabs match our result sets
       exactly. Proof material: terminal transcripts + two screenshots of the tabs (owner session 2026-11-25).
7. [x] **PR opened 2026-11-25: https://github.com/lichess-org/lila/pull/22653** — verified after creation: state
       OPEN, **12 additions / 0 deletions / 3 files**, commit `cc5411177b`, author = owner, title = commit subject,
       body = the draft below **plus the AI-assistance section** (AI_POLICY disclosure: Claude Code, extent, main
       prompts) and the "🤖 Generated with Claude Code" footer; the 3 screenshots (`03-mliebelt-member-studies`,
       `03-alice-member-studies`, `02-mliebelt-my-studies`) are embedded via `user-attachments`; **no @-mention**, no
       `Closes` keyword (#22625 gets closed by the maintainer on merge); not a draft. Push went through without rebase
       (upstream had not moved). **Now: waiting for review.** Earlier decision record (superseded): "do not push yet"
       same day, released by the owner hours later. Rest of this step = the pre-push draft, kept for the record.
       Original single-commit note: `cc5411177b` "GET /api/study/member for the studies the user contributes
       to". Commands then: `git -C ~/priv/dev/lila push origin study-member-api` and `gh pr create --repo
       lichess-org/lila --head study-member-api ...` with the title = commit subject and this body:

       > **What** — Adds `GET /api/study/member`, an authenticated endpoint listing the studies the token's user is a
       > member of (excluding ones they own), streamed as NDJSON metadata exactly like `GET /api/study/by/{user}`
       > (`id`, `name`, `createdAt`, `updatedAt`, optional `?topics=true`).
       >
       > **Why** — Feature request #22625: tools cannot find studies a user contributes to, because `study/by/{user}`
       > only ever shows the owner's public studies. The shape is the one chosen in
       > [#22625](https://github.com/lichess-org/lila/issues/22625#issuecomment-7159995161): a new endpoint for the
       > authenticated user.
       >
       > **How** — Route + `Study.apiListMember` mirroring `apiListByOwner` (`Scoped(_.Study.Read)`,
       > `apiC.jsonDownload`, throttle 50/s). One new repo method `sourceContributed` = existing `sourceByMember` +
       > `ownerId != me` — the identical predicate the website's "Studies I contribute to" uses
       > (`StudyPager.mineMember`), so the API and the tab agree by construction. 12 added lines.
       >
       > **Human testing** — local dev instance, several users, owned/member/public/unlisted constellations: no token →
       > `401 Missing authorization header`; member token → foreign studies only, owned excluded; owner-only user →
       > `200` with empty body; results equal the website tab "Studies I contribute to", cross-checked against
       > `study/by/{user}` for public and unlisted visibility; `?topics=true` behaves like on `by/{user}`. Proof
       > attached: terminal transcripts + screenshots of the tabs and the API calls.
       >
       > **AI assistance** (per AI_POLICY.md) — used Claude Code to explore the codebase, draft the code and build the
       > small test tooling. Every line was reviewed, formatted and understood by me; all tests were run by hand.
       > Main prompts: implement `GET /api/study/member` as the authenticated counterpart of `apiListByOwner`; make the
       > result set equal the website's "Studies I contribute to" tab (owned studies excluded); test the auth and
       > visibility edge cases on a local instance.

       Before pushing: `git fetch upstream && git rebase upstream/master` (ornicar is active in this file — keep the diff
       exactly 12 lines against current master; if `JsonView.metadata` changed, adapt our one call site). Attach
       `~/priv/dev/lila-proof/` (with `00-preparation.md` filled) to the PR by drag&drop.
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

## Explanation for the PR (lookup notes, from the Q&A session 2026-11-25)

### Branch naming — CONTRIBUTING says nothing about it

Grepped: CONTRIBUTING.md has **no branch-name rules**. Master's history shows every contribution arrives **squashed** (the
PR title becomes the single commit on master, e.g. "simplify ui/study addChapter, close #22631"), so contributor branch
names never reach master and are never recorded. No ticket-number convention; the PR body carries the `#22625` reference,
which is what GitHub links. Only GitHub's generic syntax rules apply (no spaces, no `~^:?*[\`). → `study-member-api`
stays as it is.

### lila's AI contribution policy — the PR must comply

CONTRIBUTING.md lines 10–17 + `AI_POLICY.md`:

* **disclose the AI usage** (tool + extent) **with the prompts used**, in the PR body or commit message → add an
  "AI assistance" section to the parked draft: *Claude Code drafted the code jointly with the human author, who verified,
  ran and tested it locally; prompt summary attached/inlined*.
* **"Provide proof of human testing of the changes, with screenshots or ideally a video"** — prescriptive wording, so the
  earlier "text proof only" decision should be reconsidered; the tabs screenshot from the local instance is the natural
  proof (it shows only own test data and the own public handle).
* install & run locally (done) and be able to **explain every line** oneself — the walkthrough below is exactly that
  preparation.

### The change, file by file

`conf/routes` — one line, `GET /api/study/member → Study.apiListMember`, placed after the `by/:user` line.

`modules/study/src/main/StudyRepo.scala` — the Mongo access layer for the `study` collection; 3 added lines:

```scala
def sourceContributed(memberId: UserId): Source[Study, ?] =
  sourceByMember(memberId, isMe = true, select = bdoc("ownerId".neq(memberId)))
```

The pre-existing `sourceByMember(memberId, isMe, select)` queries "studies whose member array `uids` contains me, plus
whatever `select` adds, plus — if `isMe` is **false** — `visibility: public`". So:

* `isMe = true` → no public-only restriction; legit because the endpoint is auth-only and always about *one's own*
  memberships — you may see private studies you are a member of.
* `select = bdoc("ownerId".neq(memberId))` → Mongo `ownerId $ne me`, "not studies I own" — the **identical** predicate of
  the website pager `StudyPager.mineMember`, hence API and tab cannot drift apart. `bdoc`/`.neq` is lila's small BSON DSL.
* returns `Source[Study, ?]` — a **stream** (Mongo cursor), not a list.
* Why a repo method: the controller stays free of Mongo vocabulary, the concept gets a name, future callers
  (e.g. a PGN-export variant) can reuse it.

`app/controllers/Study.scala` — the HTTP layer; 7 added lines:

```scala
def apiListMember = Scoped(_.Study.Read) { ctx ?=> me ?=>
  apiC.jsonDownload:
    env.study.studyRepo
      .sourceContributed(me.userId)
      .throttle(50, 1.second)
      .map(lila.study.JsonView.metadata(_, getBool("topics")))
}
```

* `Scoped(_.Study.Read)` — lila's "authenticated OAuth token with scope `study:read`" wrapper; produces the observed
  `401 Missing authorization header` (wrong scope → 403). No manual auth code in the body.
* `{ ctx ?=> me ?=> ... }` — Scala 3 **context functions**: `Scoped` injects the two values it guarantees — `ctx`
  (request: query params, IP) and `me` (the authenticated user). There is no "not logged in" case left to handle.
* `apiC.jsonDownload:` — turns the stream into the HTTP answer: NDJSON, chunked, as an attachment — exactly the style of
  `study/by/{user}`.
* `sourceContributed(me.userId)` — the query starts as a cursor; studies are serialized and sent **while the cursor is
  still reading** → flat memory for any number of studies.
* `.throttle(50, 1.second)` — ≤ 50 studies/s, the same value `apiListByOwner` uses for the owner's own list; server-side
  self-protection.
* `.map(JsonView.metadata(_, getBool("topics")))` — per study emits `{ id, name, createdAt, updatedAt }` (+ `topics` when
  `?topics=true`), mirroring the topics feature lila recently added to `study/by/{user}`.

Deliberately **not** in the diff: pagination (same as the existing list endpoint), owner/visibility fields (follow-up
wish on the issue), tests (lila has no controller-test pattern for these streaming endpoints — the policy's
"human tested" is the substitute).

### Planned final proof run (owner's scenario, before opening the PR)

Local server + lila-ws up; users **mliebelt** (A, handle reused locally) + two new **Alice** (B) and **Bob** (C);
each new user shares one of their studies with mliebelt as contributor.

1. mliebelt owns 1 study (already exists, unlisted) → must NOT appear in the member list.
2. `-l raw GET /api/study/member` **without** `LICHESS_LOCAL_PAT` → expect `401 Missing authorization header`.
3. `-l list alice` / `-l list bob` **with their own tokens** → each shows their owned study (incl. where mliebelt
   contributes). Note: without their tokens only **public** studies show — set the studies public or use their tokens,
   otherwise step 3 looks broken.
4. UI "Studies I contribute to" tab as mliebelt → exactly 2 studies (Alice's + Bob's); **screenshot** (policy proof) →
   save all screenshots + transcripts to `~/priv/dev/lila-proof/` — deliberately **outside** both git repos (verified:
   neither repo root contains it), so proof material with local usernames can never be committed by accident.
5. `-l member` with `LICHESS_LOCAL_PAT` → the same 2 studies; owned one absent.
6. `-l list mliebelt` with the token → only the 1 **owned** study → the contrast that proves the gap the PR fills.
7. Edge case: `-l member` with **Alice's** token → `200` and **zero lines** (owns one, member of none).
8. Optional: `-l raw GET "/api/study/member?topics=true"` → shows the topics field works like on `by/{user}`.

Reminder for repo notes: local usernames stay anonymized (A/B/C) — "Alice/Bob/mliebelt-local" never go into files here.

**Run executed 2026-11-25** — material in `~/priv/dev/lila-proof/` (10 files): transcripts `02-terminal.md`
(`list mliebelt` = 1 owned study; `?topics=true` on `by/{user}`; anonymous `by/{user}` → 200 empty) and
`03-terminal.md` (`member` → exactly the 2 foreign studies; `member?topics=true`; **Alice's token → 200 empty**;
**no token → 401 `{"error":"Missing authorization header"}`**). Screenshots: 01 all-studies ×3, 02 my-studies ×3
(each user's own study), 03 contribute tabs (mliebelt: exactly Alice's + Bob's, own absent; Alice: "None yet.").
Two loose ends before attaching this to the PR: `00-preparation.md` is **still empty** (write the fixture: who owns /
shares what / visibility / tokens) — and note that `01-alice-all-studies.png` also shows the old `member` user's
public "member's Study" (leftover from the first session) → explain it in the prep file or retake that shot.
Minor fidelity point: in `03-terminal.md` the Alice block's echoed URL line says `?topics=true` although the command
was a plain `-l member` (paste artifact) — keep transcripts verbatim if pasted into the PR.

## Notes and findings during the work

* **Websockets / "Reconnecting" (2026-11-25):** the local server first ran **without** the separate websocket server —
  the UI then shows a permanent red "Reconnecting" and study **share/member management does not work** (it runs over the
  socket). Topology: `lila <-> redis <-> lila-ws <-> websocket <-> browser`. Setup: cloned `lichess-org/lila-ws` to
  `~/priv/dev/lila-ws`; its defaults already fit (ports `9664`, `csrf.origin = http://localhost:9663`, localhost
  redis/mongo). **Its README is stale**: it says `~reStart`, but the reStart plugin is gone from `plugins.sbt` →
  `Invalid commands`. Correct: `cd ~/priv/dev/lila-ws && . ~/.zprofile && sbt` then **`run`** (or `stage` once, then
  `target/universal/stage/bin/lila-ws`).
* **Browser URL:** must be `http://localhost:9663`, not `127.0.0.1:9663` — lila's `net.socket.domains` is
  `localhost:9664` and lila-ws's CSRF origin is `http://localhost:9663`; the host must match for cookies and socket.
* First local data (owner session): four local test users registered via signup (works on the dev instance without
  special config), named in these notes only as **A**, **B** and **C**; 3 studies, **all `visibility: "unlisted"`**:
  S1 (owned by A, member B), S2 (owned by B, member A), S3 (owned by C, member A). Users live in the Mongo collection
  `user4`, note `uids` always contains the owner. Good test matrix: A owns 1 study and is a member of 2 foreign ones.
* **API playground**: `experiments/lila-api.sh` in this repo — curl wrapper with `list|member|pgn|whoami|raw`, flag `-l`
  selects the local server. Tokens kept apart on purpose: `LICHESS_PAT` = prod, `LICHESS_LOCAL_PAT` = local; a call
  prints only `token: set/none`, never the value. Tokens are created in the UI at `/account/token`.
* Reproduced on the local server (2026-11-25): `GET /api/study/by/A` **without** token → 200 + **empty** (A's one
  study is unlisted, and non-owners only ever see public ones); **with** A's token → the study appears (own studies
  include unlisted/private — the documented part). `GET /api/study/member` on **prod** → 404 (endpoint does not exist
  there today — the ticket's gap in one call).
* Play dev mode did **not** pick up the new route/ controller while running — a server restart loads it (`compile`
  from a second shell is not enough).
