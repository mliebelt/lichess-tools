# Feature request for Lichess: member search

**Posted on 2026-11-23 as https://github.com/lichess-org/lila/issues/22625** (the posted issue has additional explanations; this
file is the original draft and stays as a record).

**Decision (2026-11-25):** the maintainer `ornicar` answered
[issuecomment-7159995161](https://github.com/lichess-org/lila/issues/22625#issuecomment-7159995161) that he will go with
the second proposal: **a new endpoint for the authenticated user, `GET /api/study/member`** (mirrors "Studies I contribute
to"). We write the pull request ourselves; the work is tracked in ticket #3 and
[3-lila-member-endpoint.md](3-lila-member-endpoint.md). The text below stays unchanged as a record of the request.

> **Notes for the author (removed before posting):**
>
> * This request is only about **listing the studies a user is a member of**. Topics are a different topic and are already
>   tracked in https://github.com/lichess-org/lila/issues/17480 "API: a study topic API" (see
>   [2-study-topic-api.md](2-study-topic-api.md)). They are not part of this text on purpose.
> * I found no open issue about listing studies by membership (my `gh` searches in `lichess-org/api` and `lichess-org/lila`
>   returned nothing). Please search once more yourself. Feature requests for the API probably belong in `lichess-org/lila`,
>   because the `api` repository is documentation (see the comments in #17480).
> * From the `lila` source (read 2026-11-23, not the official docs): `GET /api/study/by/:user` uses `sourceByOwner`, which
>   restricts the result to public studies when the caller is not the owner. The website's "Studies I contribute to" uses a
>   separate member query (`Study.mineMember`, `sourceByMember`). An API version of that may therefore be a small change.
> * The text contains no real user names or study ids. Please keep it that way, studies may be private.
> * Items in `[brackets]` are for you to fill in or delete.

---

## Title

API: list the studies I contribute to (studies where I am a member)

## Summary

The API cannot list the studies where a user is a member, which the website shows as "Studies I contribute to". Because of
that, tools cannot back up or organize the studies that a user works on together with others.

## Use case

[I am writing a small command line tool that saves a user's studies as PGN files.] A user who edits studies of a club
account, or of friends, wants to save "all studies I contribute to". With the current API this is impossible, and the only
way is to copy the study ids by hand from the website.

## What I checked (current behaviour)

1. `GET /api/study/by/{username}` returns per study only `id`, `name`, `createdAt`, `updatedAt` (as documented). There is
   no owner, no visibility and no members.
2. The documentation says: "If authenticated, then all public, unlisted, and private studies are included."
   In my test this applies only to the studies **owned** by the authenticated user. I called the list for a user `alice`
   with the token of a user `bob`, who is a member of many private studies of `alice`. The answer was the same as without a
   token (only the public studies of `alice`). I confirmed that by deleting one public study of `alice`: the count
   without a token went from 18 to 17. So membership does not make a non-public study appear in the list.
3. `GET /api/study/{studyId}.pgn` works for studies of other users when the token's user is a member, so the download is not
   the problem. Finding the ids of these studies is.
4. The website can do it: "Studies I contribute to", and the search `https://lichess.org/study/search?q=member:bob`
   list these studies, with owner, private flag, update time, chapters and members. That answer is HTML for the logged-in
   session, there is no JSON, and it is not documented as an API. I did not want to scrape it.

## Proposal

The exact shape is up to the maintainers. One of:

* a parameter on the list endpoint, for example `GET /api/study/by/{username}?member=true`, or
* a new endpoint for the authenticated user, for example `GET /api/study/member` (mirrors "Studies I contribute to"), or
* a documented JSON version of the study search (`q`, `order`) with the `member:` and `owner:` terms that the website
  already understands.

Scope `study:read`, streamed as NDJSON like the existing list, with at least `id`, `name`, `createdAt`, `updatedAt`
and, to be useful for this case, the `owner` (id or name) and the visibility (`public` / `unlisted` / `private`).

Also, please clarify in the documentation of `studyListMetadata` which studies an authenticated call returns (only the
studies owned by the authenticated user, as far as I can see), so that nobody expects the studies they contribute to.

## Alternatives considered

* Parsing the HTML of the web search: fragile, needs a session cookie, and is not an API.
* Asking users for study ids and downloading them one by one with `GET /api/study/{studyId}.pgn`: works, but the user has to
  find all ids by hand.

## Related

* Topics of studies are a separate request: https://github.com/lichess-org/lila/issues/17480

## Offer

[Optional: I am willing to try a pull request for this if a maintainer tells me which shape of the API is preferred.]
