# Draft: feature request for Lichess (not posted yet)

> **Notes for the author (delete this block before posting):**
>
> * Existing issue: https://github.com/lichess-org/lila/issues/17480 "API: a study topic API" (open, label `study`) asks
>   for reading the topics of studies by id (and setting them). Check it first. Options: (a) post the "Proposal" below as a
>   comment there, (b) open a new issue in `lichess-org/lila` that links to it. This text is written to work as a new issue.
> * In that issue a commenter said it belongs to the API repo, the author answered that the API repo is only for
>   documentation. I also found no open issue about listing studies by membership. Please search once more yourself.
> * The text contains no real user names or study ids. Please keep it that way, studies may be private.
> * Items in `[brackets]` are for you to fill in or delete.

---

## Title

API: list the studies I contribute to, and include topics in the study list

## Summary

The API cannot list the studies where a user is a member (the web page "Studies I contribute to"), and the study list
does not contain topics. Both exist on the website. Because of that, tools cannot back up or organize the studies a user
works on together with others, or find studies by topic.

## Use case

[I am writing a small command line tool that saves a user's studies as PGN files, with filters.] A user who edits studies
of a club account, or of friends, wants to save "all studies I contribute to", and only those with a given topic. With the
current API this is impossible, and the only way is to copy study ids by hand from the website.

## What I checked (current behaviour)

1. `GET /api/study/by/{username}` returns per study only `id`, `name`, `createdAt`, `updatedAt` (as documented).
   There are no topics, no owner, no visibility and no members.
2. The documentation says: "If authenticated, then all public, unlisted, and private studies are included."
   In my test this applies only to the studies **owned** by the authenticated user. I called the list for a user `alice`
   with the token of a user `bob`, who is a member of many private studies of `alice`. The answer was the same as without a
   token (only the public studies of `alice`). I confirmed that by deleting one public study of `alice`: the count
   without a token went from 18 to 17. So membership does not make a non-public study appear in the list.
3. `GET /api/study/{studyId}.pgn` works for studies of other users when the token's user is a member, but the PGN
   has no topics tag (tags are `Event`, `StudyName`, `ChapterName`, `ChapterURL`, `Annotator`, ...), and
   `HEAD /api/study/{studyId}.pgn` only adds `Last-Modified`.
4. The website can do it: "Studies I contribute to", and the search `https://lichess.org/study/search?q=member:bob`
   list these studies, with owner, private flag, update time, chapters and members. The topics are visible in the
   web UI as well (topic chips, "Topics" menu). That answer is HTML for the logged-in session, there is no JSON, and it is
   not documented as an API. I did not want to scrape it.

## Proposal

The exact shape is up to the maintainers. A minimal version would be:

1. **Topics in the study list:** add `topics` (array of strings) to the `StudyMetadata` schema of
   `GET /api/study/by/{username}`. This also helps issue #17480 (reading topics), at least for the studies of one user.
2. **Studies of which a user is a member:** one of
   * a parameter on the list endpoint, for example `GET /api/study/by/{username}?member=true`, or
   * a new endpoint for the authenticated user, for example `GET /api/study/member` (mirrors "Studies I contribute to"), or
   * a documented JSON version of the study search (`q`, `order`) with the `member:` and `owner:` terms that the website
     already understands.

   Scope `study:read`, streamed as NDJSON like the existing list, with at least `id`, `name`, `createdAt`, `updatedAt`
   and, to be useful, the `owner` (id or name), the visibility (`public` / `unlisted` / `private`) and the `topics`.
3. **Documentation:** clarify in `studyListMetadata` which studies an authenticated call returns (only the studies owned by
   the authenticated user, as far as I can see), so that nobody expects the studies they contribute to.

## Alternatives considered

* Parsing the HTML of the web search: fragile, needs a session cookie, and is not an API.
* Asking users for study ids and downloading them one by one with `GET /api/study/{studyId}.pgn`: works, but the user has to
  find all ids by hand.

## Related

* https://github.com/lichess-org/lila/issues/17480 – "API: a study topic API" (reading and setting topics by study id).

## Offer

[Optional: I am willing to try a pull request for this if a maintainer tells me which shape of the API is preferred.]
