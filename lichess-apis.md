# Lichess APIs

The following are extracted APIs from the API website, by copying the markdown.


Each endpoint appears once. Add new endpoints here first; tools and plans refer to this file.

| Tag | Endpoint | Operation ID |
|---|---|---|
| Account | `GET /api/account` | `accountMe` |
| Studies | `GET /api/study/by/{username}` | `studyListMetadata` |
| Studies | `GET /api/study/{studyId}.pgn` | `studyAllChaptersPgn` |
| Studies | `HEAD /api/study/{studyId}.pgn` | `studyAllChaptersHead` |


# Get my profile

- **Method:** `GET`
- **Path:** `/api/account`
- **Operation ID:** `accountMe`
- **Tags:** Account

Public information about the logged in user.

## Effective servers

- `https://lichess.org`
- `https://lichess.dev`
- `http://localhost:{port}`
  - port: `8080`
- `http://l.org`

## Authentication

- **OAuth2**: OAuth 2.0: authorization code, authorize `https://lichess.org/oauth`, token `https://lichess.org/api/token`

  Read [the introduction for how to make authenticated requests](#description/authentication).

## Responses

### 200 The public information about the logged in user.

**Headers:**

- **`Access-Control-Allow-Origin`**

  `string`, default: `"'*'"`

**Content type:** `application/json`

**All of:**

- `object`, schema: `User`
  - **`id` (required)**: `string`
  - **`username` (required)**: `string`
  - **`createdAt`**: `integer`, format: `int64`
  - **`disabled`**: `boolean`

    only appears if a user's account is closed
  - **`flair`**: `string`

    See [available flair list and images](https://github.com/lichess-org/lila/tree/master/public/flair)
  - **`patron`**: `boolean`, deprecated

    Use patronColor value instead to determine if player is a patron.
  - **`patronColor`**: `integer`, minimum: `1`, maximum: `10`

    Players can choose a color for their Patron wings.
    See [here for the color mappings](https://github.com/lichess-org/lila/blob/master/ui/lib/css/abstract/_patron-colors.scss).

    The presence of this field indicates the player is an active Patron.
  - **`perfs`**: `object`, schema: `Perfs`
    - **`antichess`**: `object`, schema: `Perf`
      - **`games` (required)**: `integer`
      - **`prog` (required)**: `integer`
      - **`rating` (required)**: `integer`
      - **`rd` (required)**: `integer`

        rating deviation
      - **`prov`**: `boolean`

        only appears if a user's perf rating are [provisional](https://lichess.org/faq#provisional)
      - **`rank`**: `integer`

        global lichess ranking, only appears for recently active players
    - **`atomic`**: `object`, schema: `Perf`

      *Schema `Perf` is shown above.*
    - **`blitz`**: `object`, schema: `Perf`

      *Schema `Perf` is shown above.*
    - **`bullet`**: `object`, schema: `Perf`

      *Schema `Perf` is shown above.*
    - **`chess960`**: `object`, schema: `Perf`

      *Schema `Perf` is shown above.*
    - **`classical`**: `object`, schema: `Perf`

      *Schema `Perf` is shown above.*
    - **`correspondence`**: `object`, schema: `Perf`

      *Schema `Perf` is shown above.*
    - **`crazyhouse`**: `object`, schema: `Perf`

      *Schema `Perf` is shown above.*
    - **`horde`**: `object`, schema: `Perf`

      *Schema `Perf` is shown above.*
    - **`kingOfTheHill`**: `object`, schema: `Perf`

      *Schema `Perf` is shown above.*
    - **`puzzle`**: `object`, schema: `Perf`

      *Schema `Perf` is shown above.*
    - **`racer`**: `object`, schema: `PuzzleModePerf`
      - **`runs` (required)**: `integer`
      - **`score` (required)**: `integer`
    - **`racingKings`**: `object`, schema: `Perf`

      *Schema `Perf` is shown above.*
    - **`rapid`**: `object`, schema: `Perf`

      *Schema `Perf` is shown above.*
    - **`storm`**: `object`, schema: `PuzzleModePerf`

      *Schema `PuzzleModePerf` is shown above.*
    - **`streak`**: `object`, schema: `PuzzleModePerf`

      *Schema `PuzzleModePerf` is shown above.*
    - **`threeCheck`**: `object`, schema: `Perf`

      *Schema `Perf` is shown above.*
    - **`ultraBullet`**: `object`, schema: `Perf`

      *Schema `Perf` is shown above.*
  - **`playTime`**: `object`, schema: `PlayTime`
    - **`total` (required)**: `integer`
    - **`tv` (required)**: `integer`
    - **`human`**: `integer`
  - **`profile`**: `object`, schema: `Profile`
    - **`bio`**: `string`
    - **`cfcRating`**: `integer`

      only appears if a user has set them
    - **`dsbRating`**: `integer`

      only appears if a user has set them
    - **`ecfRating`**: `integer`

      only appears if a user has set them
    - **`fideRating`**: `integer`

      only appears if a user has set them
    - **`flag`**: `string`
    - **`links`**: `string`
    - **`location`**: `string`
    - **`rcfRating`**: `integer`

      only appears if a user has set them
    - **`realName`**: `string`
    - **`uscfRating`**: `integer`

      only appears if a user has set them
  - **`seenAt`**: `integer`, format: `int64`
  - **`title`**: `string`, possible values: `"GM", "WGM", "IM", "WIM", "FM", "WFM", "NM", "CM", "WCM", "WNM", "LM", "BOT"`

    only appears if the user is a titled player or a bot user
  - **`tosViolation`**: `boolean`

    only appears if a user's account is marked for the violation of [Lichess TOS](https://lichess.org/terms-of-service)
  - **`verified`**: `boolean`
- `object`
  - **`url` (required)**: `string`, format: `uri`
  - **`blocking`**: `boolean`

    only appears if the request is [authenticated with OAuth2](#description/authentication)
  - **`count`**: `object`, schema: `Count`
    - **`all` (required)**: `integer`
    - **`bookmark` (required)**: `integer`
    - **`draw` (required)**: `integer`
    - **`import` (required)**: `integer`
    - **`loss` (required)**: `integer`
    - **`me` (required)**: `integer`
    - **`playing` (required)**: `integer`
    - **`rated` (required)**: `integer`
    - **`win` (required)**: `integer`
    - **`ai`**: `integer`
    - **`drawH`**: `integer`
    - **`lossH`**: `integer`
    - **`winH`**: `integer`
  - **`fideId`**: `number`
  - **`followable`**: `boolean`

    only appears if the request is [authenticated with OAuth2](#description/authentication)
  - **`following`**: `boolean`

    only appears if the request is [authenticated with OAuth2](#description/authentication)
  - **`playing`**: `string`, format: `uri`
  - **`streamer`**: `object`, schema: `UserStreamer`
    - **`twitch`**: `object`
      - **`channel`**: `string`, format: `uri`
    - **`youtube`**: `object`
      - **`channel`**: `string`, format: `uri`
  - **`streaming`**: `boolean`

schema: `UserExtended`

**Example: default**

```json
{
  "id": "bobby",
  "username": "Bobby",
  "perfs": {
    "bullet": {
      "games": 203,
      "rating": 1755,
      "rd": 90,
      "prog": -8
    },
    "blitz": {
      "games": 674,
      "rating": 1623,
      "rd": 64,
      "prog": 43
    },
    "rapid": {
      "games": 337,
      "rating": 1824,
      "rd": 56,
      "prog": 20
    },
    "classical": {
      "games": 253,
      "rating": 1756,
      "rd": 45,
      "prog": -45
    },
    "correspondence": {
      "games": 115,
      "rating": 1648,
      "rd": 56,
      "prog": 7
    },
    "chess960": {
      "games": 174,
      "rating": 1649,
      "rd": 48,
      "prog": 16
    },
    "kingOfTheHill": {
      "games": 291,
      "rating": 1781,
      "rd": 90,
      "prog": -1
    },
    "threeCheck": {
      "games": 59,
      "rating": 1622,
      "rd": 76,
      "prog": 26
    },
    "antichess": {
      "games": 481,
      "rating": 1650,
      "rd": 79,
      "prog": 42
    },
    "atomic": {
      "games": 609,
      "rating": 1759,
      "rd": 80,
      "prog": 17
    },
    "horde": {
      "games": 57,
      "rating": 1785,
      "rd": 106,
      "prog": -20
    },
    "crazyhouse": {
      "games": 11,
      "rating": 1795,
      "rd": 45,
      "prog": 3
    },
    "puzzle": {
      "games": 334,
      "rating": 1815,
      "rd": 75,
      "prog": 44
    }
  },
  "flair": "symbols.left-luggage",
  "createdAt": 1792561760182,
  "profile": {
    "flag": "MZ",
    "location": "Bobby City",
    "bio": "In proportion as exchange bursts its local bonds, and the value of commodities more and more expands into an embodiment of human labour in the abstract, in the same proportion the character of money attaches itself to commodities that are by nature fitted to perform the social function of a universal equivalent. Those commodities are the precious m",
    "fideRating": 1725,
    "uscfRating": 1566,
    "ecfRating": 1641,
    "rcfRating": 1832,
    "cfcRating": 1913,
    "dsbRating": 1839,
    "links": ""
  },
  "seenAt": 1792914495578,
  "playTime": {
    "total": 13467,
    "tv": 0
  },
  "url": "https://lichess.org/@/Bobby",
  "count": {
    "all": 6417,
    "rated": 5133,
    "draw": 685,
    "loss": 2833,
    "win": 2899,
    "bookmark": 0,
    "playing": 0,
    "import": 0,
    "me": 0
  }
}
```

## Schemas

### Flair

**Type:** `string`

See [available flair list and images](https://github.com/lichess-org/lila/tree/master/public/flair)

### Title

**Type:** `string`, possible values: `"GM", "WGM", "IM", "WIM", "FM", "WFM", "NM", "CM", "WCM", "WNM", "LM", "BOT"`

only appears if the user is a titled player or a bot user

### Patron

**Type:** `boolean`, deprecated

Use patronColor value instead to determine if player is a patron.

### PatronColor

**Type:** `integer`, minimum: `1`, maximum: `10`

Players can choose a color for their Patron wings.
See [here for the color mappings](https://github.com/lichess-org/lila/blob/master/ui/lib/css/abstract/_patron-colors.scss).

The presence of this field indicates the player is an active Patron.

### Perf

**Type:** `object`

- **`games` (required)**: `integer`
- **`prog` (required)**: `integer`
- **`rating` (required)**: `integer`
- **`rd` (required)**: `integer`

  rating deviation
- **`prov`**: `boolean`

  only appears if a user's perf rating are [provisional](https://lichess.org/faq#provisional)
- **`rank`**: `integer`

  global lichess ranking, only appears for recently active players

**Example:**

```json
{
  "games": 1,
  "rating": 1,
  "rd": 1,
  "prog": 1,
  "prov": true,
  "rank": 1
}
```

### PuzzleModePerf

**Type:** `object`

- **`runs` (required)**: `integer`
- **`score` (required)**: `integer`

**Example:**

```json
{
  "runs": 1,
  "score": 1
}
```

### Perfs

**Type:** `object`

- **`antichess`**: `object`, schema: `Perf`

  *Schema `Perf` is shown above.*
- **`atomic`**: `object`, schema: `Perf`

  *Schema `Perf` is shown above.*
- **`blitz`**: `object`, schema: `Perf`

  *Schema `Perf` is shown above.*
- **`bullet`**: `object`, schema: `Perf`

  *Schema `Perf` is shown above.*
- **`chess960`**: `object`, schema: `Perf`

  *Schema `Perf` is shown above.*
- **`classical`**: `object`, schema: `Perf`

  *Schema `Perf` is shown above.*
- **`correspondence`**: `object`, schema: `Perf`

  *Schema `Perf` is shown above.*
- **`crazyhouse`**: `object`, schema: `Perf`

  *Schema `Perf` is shown above.*
- **`horde`**: `object`, schema: `Perf`

  *Schema `Perf` is shown above.*
- **`kingOfTheHill`**: `object`, schema: `Perf`

  *Schema `Perf` is shown above.*
- **`puzzle`**: `object`, schema: `Perf`

  *Schema `Perf` is shown above.*
- **`racer`**: `object`, schema: `PuzzleModePerf`

  *Schema `PuzzleModePerf` is shown above.*
- **`racingKings`**: `object`, schema: `Perf`

  *Schema `Perf` is shown above.*
- **`rapid`**: `object`, schema: `Perf`

  *Schema `Perf` is shown above.*
- **`storm`**: `object`, schema: `PuzzleModePerf`

  *Schema `PuzzleModePerf` is shown above.*
- **`streak`**: `object`, schema: `PuzzleModePerf`

  *Schema `PuzzleModePerf` is shown above.*
- **`threeCheck`**: `object`, schema: `Perf`

  *Schema `Perf` is shown above.*
- **`ultraBullet`**: `object`, schema: `Perf`

  *Schema `Perf` is shown above.*

**Example:**

```json
{
  "chess960": {
    "games": 1,
    "rating": 1,
    "rd": 1,
    "prog": 1,
    "prov": true,
    "rank": 1
  },
  "atomic": {
    "games": 1,
    "rating": 1,
    "rd": 1,
    "prog": 1,
    "prov": true,
    "rank": 1
  },
  "racingKings": {
    "games": 1,
    "rating": 1,
    "rd": 1,
    "prog": 1,
    "prov": true,
    "rank": 1
  },
  "ultraBullet": {
    "games": 1,
    "rating": 1,
    "rd": 1,
    "prog": 1,
    "prov": true,
    "rank": 1
  },
  "blitz": {
    "games": 1,
    "rating": 1,
    "rd": 1,
    "prog": 1,
    "prov": true,
    "rank": 1
  },
  "kingOfTheHill": {
    "games": 1,
    "rating": 1,
    "rd": 1,
    "prog": 1,
    "prov": true,
    "rank": 1
  },
  "threeCheck": {
    "games": 1,
    "rating": 1,
    "rd": 1,
    "prog": 1,
    "prov": true,
    "rank": 1
  },
  "antichess": {
    "games": 1,
    "rating": 1,
    "rd": 1,
    "prog": 1,
    "prov": true,
    "rank": 1
  },
  "crazyhouse": {
    "games": 1,
    "rating": 1,
    "rd": 1,
    "prog": 1,
    "prov": true,
    "rank": 1
  },
  "bullet": {
    "games": 1,
    "rating": 1,
    "rd": 1,
    "prog": 1,
    "prov": true,
    "rank": 1
  },
  "correspondence": {
    "games": 1,
    "rating": 1,
    "rd": 1,
    "prog": 1,
    "prov": true,
    "rank": 1
  },
  "horde": {
    "games": 1,
    "rating": 1,
    "rd": 1,
    "prog": 1,
    "prov": true,
    "rank": 1
  },
  "puzzle": {
    "games": 1,
    "rating": 1,
    "rd": 1,
    "prog": 1,
    "prov": true,
    "rank": 1
  },
  "classical": {
    "games": 1,
    "rating": 1,
    "rd": 1,
    "prog": 1,
    "prov": true,
    "rank": 1
  },
  "rapid": {
    "games": 1,
    "rating": 1,
    "rd": 1,
    "prog": 1,
    "prov": true,
    "rank": 1
  },
  "storm": {
    "runs": 1,
    "score": 1
  },
  "racer": {
    "runs": 1,
    "score": 1
  },
  "streak": {
    "runs": 1,
    "score": 1
  }
}
```

### Profile

**Type:** `object`

- **`bio`**: `string`
- **`cfcRating`**: `integer`

  only appears if a user has set them
- **`dsbRating`**: `integer`

  only appears if a user has set them
- **`ecfRating`**: `integer`

  only appears if a user has set them
- **`fideRating`**: `integer`

  only appears if a user has set them
- **`flag`**: `string`
- **`links`**: `string`
- **`location`**: `string`
- **`rcfRating`**: `integer`

  only appears if a user has set them
- **`realName`**: `string`
- **`uscfRating`**: `integer`

  only appears if a user has set them

**Example:**

```json
{
  "flag": "",
  "location": "",
  "bio": "",
  "realName": "",
  "fideRating": 1,
  "uscfRating": 1,
  "ecfRating": 1,
  "cfcRating": 1,
  "rcfRating": 1,
  "dsbRating": 1,
  "links": ""
}
```

### PlayTime

**Type:** `object`

- **`total` (required)**: `integer`
- **`tv` (required)**: `integer`
- **`human`**: `integer`

**Example:**

```json
{
  "total": 1,
  "tv": 1,
  "human": 1
}
```

### User

**Type:** `object`

- **`id` (required)**: `string`
- **`username` (required)**: `string`
- **`createdAt`**: `integer`, format: `int64`
- **`disabled`**: `boolean`

  only appears if a user's account is closed
- **`flair`**: `string`

  See [available flair list and images](https://github.com/lichess-org/lila/tree/master/public/flair)
- **`patron`**: `boolean`, deprecated

  Use patronColor value instead to determine if player is a patron.
- **`patronColor`**: `integer`, minimum: `1`, maximum: `10`

  Players can choose a color for their Patron wings.
  See [here for the color mappings](https://github.com/lichess-org/lila/blob/master/ui/lib/css/abstract/_patron-colors.scss).

  The presence of this field indicates the player is an active Patron.
- **`perfs`**: `object`, schema: `Perfs`

  *Schema `Perfs` is shown above.*
- **`playTime`**: `object`, schema: `PlayTime`

  *Schema `PlayTime` is shown above.*
- **`profile`**: `object`, schema: `Profile`

  *Schema `Profile` is shown above.*
- **`seenAt`**: `integer`, format: `int64`
- **`title`**: `string`, possible values: `"GM", "WGM", "IM", "WIM", "FM", "WFM", "NM", "CM", "WCM", "WNM", "LM", "BOT"`

  only appears if the user is a titled player or a bot user
- **`tosViolation`**: `boolean`

  only appears if a user's account is marked for the violation of [Lichess TOS](https://lichess.org/terms-of-service)
- **`verified`**: `boolean`

**Example:**

```json
{
  "id": "",
  "username": "",
  "perfs": {
    "chess960": null,
    "atomic": null,
    "racingKings": null,
    "ultraBullet": null,
    "blitz": null,
    "kingOfTheHill": null,
    "threeCheck": null,
    "antichess": null,
    "crazyhouse": null,
    "bullet": null,
    "correspondence": null,
    "horde": null,
    "puzzle": null,
    "classical": null,
    "rapid": null,
    "storm": null,
    "racer": null,
    "streak": null
  },
  "title": "GM",
  "flair": "",
  "createdAt": 1,
  "disabled": true,
  "tosViolation": true,
  "profile": {
    "flag": "",
    "location": "",
    "bio": "",
    "realName": "",
    "fideRating": 1,
    "uscfRating": 1,
    "ecfRating": 1,
    "cfcRating": 1,
    "rcfRating": 1,
    "dsbRating": 1,
    "links": ""
  },
  "seenAt": 1,
  "playTime": {
    "total": 1,
    "tv": 1,
    "human": 1
  },
  "patron": true,
  "patronColor": 1,
  "verified": true
}
```

### Count

**Type:** `object`

- **`all` (required)**: `integer`
- **`bookmark` (required)**: `integer`
- **`draw` (required)**: `integer`
- **`import` (required)**: `integer`
- **`loss` (required)**: `integer`
- **`me` (required)**: `integer`
- **`playing` (required)**: `integer`
- **`rated` (required)**: `integer`
- **`win` (required)**: `integer`
- **`ai`**: `integer`
- **`drawH`**: `integer`
- **`lossH`**: `integer`
- **`winH`**: `integer`

**Example:**

```json
{
  "all": 1,
  "rated": 1,
  "ai": 1,
  "draw": 1,
  "drawH": 1,
  "loss": 1,
  "lossH": 1,
  "win": 1,
  "winH": 1,
  "bookmark": 1,
  "playing": 1,
  "import": 1,
  "me": 1
}
```

### UserStreamer

**Type:** `object`

- **`twitch`**: `object`
  - **`channel`**: `string`, format: `uri`
- **`youtube`**: `object`
  - **`channel`**: `string`, format: `uri`

**Example:**

```json
{
  "twitch": {
    "channel": "https://example.com"
  },
  "youtube": {
    "channel": "https://example.com"
  }
}
```

- `UserExtended` — shown above.


# List studies of a user

- **Method:** `GET`
- **Path:** `/api/study/by/{username}`
- **Operation ID:** `studyListMetadata`
- **Tags:** Studies

Get metadata (name and dates) of all studies of a user.
If authenticated, then all public, unlisted, and private studies are included.
If not, only public (non-unlisted) studies are included.
Studies are streamed as [ndjson](#description/streaming-with-nd-json).

## Effective servers

- `https://lichess.org`
- `https://lichess.dev`
- `http://localhost:{port}`
  - port: `8080`
- `http://l.org`

## Authentication

- **OAuth2**: OAuth 2.0: authorization code, authorize `https://lichess.org/oauth`, token `https://lichess.org/api/token`, scopes: `study:read`

  Read [the introduction for how to make authenticated requests](#description/authentication).

## Path parameters

- **`username` (required)**: `string`

  The user whose studies we list

## Responses

### 200 The list of studies.

**Headers:**

- **`Access-Control-Allow-Origin`**

  `string`, default: `"'*'"`

**Content type:** `application/x-ndjson`

schema: `StudyMetadata`

- **`createdAt` (required)**: `integer`, format: `int64`

  The study creation date
- **`id` (required)**: `string`

  The study ID
- **`name` (required)**: `string`

  The study name
- **`updatedAt` (required)**: `integer`, format: `int64`

  The study last update date

**Example: default**

```json
{
  "id": "keq5vaIF",
  "name": "Example study",
  "createdAt": 1793058160478,
  "updatedAt": 1793058160499
}
```

## Schemas

- `StudyMetadata` — shown above.

----

# Export all chapters

- **Method:** `GET`
- **Path:** `/api/study/{studyId}.pgn`
- **Operation ID:** `studyAllChaptersPgn`
- **Tags:** Studies

Download all chapters of a study in PGN format.
If authenticated, then all public, unlisted, and private study chapters are read.
If not, only public (non-unlisted) study chapters are read.

## Effective servers

- `https://lichess.org`
- `https://lichess.dev`
- `http://localhost:{port}`
  - port: `8080`
- `http://l.org`

## Authentication

- **OAuth2**: OAuth 2.0: authorization code, authorize `https://lichess.org/oauth`, token `https://lichess.org/api/token`, scopes: `study:read`

  Read [the introduction for how to make authenticated requests](#description/authentication).

## Path parameters

- **`studyId` (required)**: `string`, minLength: `8`, maxLength: `8`

  The study ID

## Query parameters

- **`clocks`**: `boolean`, default: `true`

  Include clock comments in the PGN moves, when available.
  Example: `2. exd5 { [%clk 1:01:27] } e5 { [%clk 1:01:28] }`
- **`comments`**: `boolean`, default: `true`

  Include analysis and annotator comments in the PGN moves, when available.
  Example: `12. Bxf6 { [%eval 0.23] } a3 { White is in a pickle. }`
- **`variations`**: `boolean`, default: `true`

  Include non-mainline moves, when available.
  Example: `4. d4 Bb4+ (4... Nc6 5. Nf3 Bb4+ 6. Bd2 (6. Nbd2 O-O 7. O-O) 6... Bd6) 5. Nd2`
- **`orientation`**: `boolean`, default: `false`

  Add a `Orientation` PGN tag with the chapter predefined orientation.
  Example: `[Orientation "white"]`

## Responses

### 200 The PGN representation of the study.

**Headers:**

- **`Access-Control-Allow-Origin`**

  `string`, default: `"'*'"`
- **`Last-Modified`**

  `string`

**Content type:** `application/x-chess-pgn`

`string`

**Example: pgn**

```json
"[Event \"Example study: Chapter 1\"]\n[Date \"2026.10.26\"]\n[Result \"*\"]\n[Variant \"Standard\"]\n[ECO \"?\"]\n[Opening \"?\"]\n[StudyName \"Example study\"]\n[ChapterName \"Chapter 1\"]\n[ChapterURL \"https://lichess.org/study/keq5vaIF/oT4Ug6F7\"]\n[Annotator \"https://lichess.org/@/Bobby\"]\n[UTCDate \"2026.10.26\"]\n[UTCTime \"23:42:40\"]\n\n *\n\n\n[Event \"Opera game\"]\n[Date \"2026.10.26\"]\n[White \"Paul Morphy\"]\n[Black \"Duke Karl / Count Isouard\"]\n[Result \"1-0\"]\n[Variant \"Standard\"]\n[ECO \"C41\"]\n[Opening \"Philidor Defense\"]\n[StudyName \"Example study\"]\n[ChapterName \"Paul Morphy - Duke Karl / Count Isouard\"]\n[ChapterURL \"https://lichess.org/study/keq5vaIF/dLpkgwla\"]\n[Annotator \"https://lichess.org/@/Bobby\"]\n[UTCDate \"2026.10.26\"]\n[UTCTime \"23:42:40\"]\n\n1. e4 e5 2. Nf3 d6 3. d4 Bg4 4. dxe5 Bxf3 5. Qxf3 dxe5 6. Bc4 Nf6 7. Qb3 Qe7 8. Nc3 c6 9. Bg5 b5 10. Nxb5 cxb5 11. Bxb5+ Nbd7 12. O-O-O Rd8 13. Rxd7 Rxd7 14. Rd1 Qe6 15. Bxd7+ Nxd7 16. Qb8+ Nxb8 17. Rd8# { 1-0 White wins. } 1-0\n\n\n[Event \"Scholar's mate\"]\n[Date \"2026.10.26\"]\n[White \"Alice\"]\n[Black \"Bob\"]\n[Result \"1-0\"]\n[Variant \"Standard\"]\n[ECO \"C23\"]\n[Opening \"Bishop's Opening\"]\n[StudyName \"Example study\"]\n[ChapterName \"Alice - Bob\"]\n[ChapterURL \"https://lichess.org/study/keq5vaIF/lIlpub3T\"]\n[Annotator \"https://lichess.org/@/Bobby\"]\n[UTCDate \"2026.10.26\"]\n[UTCTime \"23:42:40\"]\n\n1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# { 1-0 White wins. } 1-0\n"
```

## Schemas

### StudyPgn

----
# Study metadata

- **Method:** `HEAD`
- **Path:** `/api/study/{studyId}.pgn`
- **Operation ID:** `studyAllChaptersHead`
- **Tags:** Studies

Only get the study headers, including `Last-Modified`.

## Effective servers

- `https://lichess.org`
- `https://lichess.dev`
- `http://localhost:{port}`
  - port: `8080`
- `http://l.org`

## Authentication

No authentication required.

## Path parameters

- **`studyId` (required)**: `string`, minLength: `8`, maxLength: `8`

  The study ID

## Responses

### 204 The study headers.

**Headers:**

- **`Access-Control-Allow-Origin`**

  `string`, default: `"'*'"`
- **`Last-Modified`**

