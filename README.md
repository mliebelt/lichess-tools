# Overview

I got yesterday the idea (in a workhop I held about Lichess) to provide some tools to allow something on Lichess that is not easily doable without some techncial background. It therefore bridges the gap between the knowledable API nerd and the normal chess player that uses a computer, but does not know all the options available.

This repository tries the following:

* Provide small, self-contained tools that work out of the box with minimal installation.
* The tools shall fullfil a purpose, so solve a problem to a user.
* The documentation to each tool is "exhaustive" (good enough) to be used. I want to try to have at least the following established:
  * All tools have one command (from the command line to be used) that have a command line interface.
  * That interface displays a help information, if asked for (option `--help`).
  * All possibilities are available through command line options then.

## How to do it

* I want to do all development with the help of LLMs.
* The tools will mainly consist in python scripts and bash/shell scripts as wrapper (if helpful).
* All ideas will be first developed as Github tickets, and given as they are to the LLM then.

## Tools

All tools need Python 3.10 or newer (the versions tested in CI) and nothing else. They work the same on Linux, Mac and Windows.

### studydl.py – save your studies

Saves your Lichess studies as PGN files, one file per study (with all its chapters).

```
python studydl.py --dry-run                         # show what would be saved
python studydl.py                                   # save all own studies into ./studies
python studydl.py --interactive --out ~/chess       # choose from a numbered list (1,3,5-7 / all / q)
python studydl.py --user SomeUser                   # studies of another user (public ones only)
python studydl.py --help                            # all options with examples
```

Existing files are skipped, use `--overwrite` to replace them. Not yet available: filtering by topic and studies you only
contribute to (see the plans).

## Access token

The tools that talk to Lichess read a personal access token from the environment variable `LICHESS_PAT`.
`studydl.py` needs the scope `study:read`. How to create a token:
https://github.com/lichess-org/api-demo/tree/master/example/oauth-personal-token

```
export LICHESS_PAT=lip_xxxxxxxx            # Linux / Mac
set LICHESS_PAT=lip_xxxxxxxx               # Windows cmd
$env:LICHESS_PAT = "lip_xxxxxxxx"          # Windows PowerShell
```

Never commit the token.

## Tests

```
python -m unittest discover -s tests       # unit tests; live tests are skipped without LICHESS_PAT
LICHESS_PAT=lip_xxxxxxxx python -m unittest discover -s tests   # including tests against Lichess
```

The Lichess API facts used by the tools are collected in [lichess-apis.md](lichess-apis.md), the plan per ticket is in
[plans/](plans/).
