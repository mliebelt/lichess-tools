#!/usr/bin/env python3
"""studydl - save your Lichess studies as PGN files on your computer.

Uses only the Python standard library. See plans/1-save-studies.md and
lichess-apis.md for the API endpoints used.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "https://lichess.org"
TOKEN_ENV = "LICHESS_PAT"
TOKEN_DOC_URL = (
    "https://github.com/lichess-org/api-demo/tree/master/example/oauth-personal-token"
)
RATE_LIMIT_WAIT_SECONDS = 60
MAX_RETRIES = 3
MAX_NAME_LENGTH = 80

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2

HELP_EPILOG = """\
examples:
  Show your studies without saving anything:
    studydl.py --dry-run

  Save all your studies into the folder ./studies:
    studydl.py

  Choose interactively which studies to save, into ~/chess/studies:
    studydl.py --interactive --out ~/chess/studies

  Save the studies of another user (private studies are only visible to the owner):
    studydl.py --user SomeUser

  Overwrite files that already exist:
    studydl.py --overwrite

interactive mode:
  A numbered list is shown. Answer with numbers and ranges (1,3,5-7),
  'all' for every study, or 'q' to quit without saving.

access token ({env}):
  The tool needs a personal access token with the scope 'study:read' in the
  environment variable {env}. Create one here (see the page for details):
    {doc}
  Then set it before running the tool:
    Linux / Mac (bash, zsh):  export {env}=lip_xxxxxxxx
    Windows (cmd):            set {env}=lip_xxxxxxxx
    Windows (PowerShell):     $env:{env} = "lip_xxxxxxxx"
""".format(env=TOKEN_ENV, doc=TOKEN_DOC_URL)


class StudyDlError(Exception):
    """An error with a message that can be shown to the user as it is."""


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

def api_get(path, token):
    """GET BASE_URL + path with the bearer token and return the body as bytes.

    On HTTP status 429 wait a minute and try again (up to MAX_RETRIES times).
    All other problems are raised as StudyDlError with a helpful message.
    """
    url = BASE_URL + path
    for attempt in range(MAX_RETRIES + 1):
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": "Bearer " + token,
                "User-Agent": "lichess-tools-studydl",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except urllib.error.HTTPError as err:
            if err.code == 429 and attempt < MAX_RETRIES:
                print(
                    "Lichess asks to slow down (HTTP 429). Waiting {} seconds ...".format(
                        RATE_LIMIT_WAIT_SECONDS
                    ),
                    file=sys.stderr,
                )
                time.sleep(RATE_LIMIT_WAIT_SECONDS)
                continue
            raise StudyDlError(describe_http_error(err.code, path))
        except urllib.error.URLError as err:
            raise StudyDlError(
                "Cannot reach Lichess ({}). Check your internet connection.".format(
                    err.reason
                )
            )
        except OSError as err:  # timeouts and broken connections
            raise StudyDlError("Network problem while calling Lichess: {}".format(err))
    raise StudyDlError("Lichess is still rate limiting us. Try again later.")


def describe_http_error(code, path):
    if code == 401:
        return (
            "Lichess rejected the token (HTTP 401). Check that {env} contains a valid, "
            "not revoked token. See {doc}".format(env=TOKEN_ENV, doc=TOKEN_DOC_URL)
        )
    if code == 403:
        return (
            "Lichess denied access (HTTP 403). The token needs the scope 'study:read'. "
            "See {doc}".format(doc=TOKEN_DOC_URL)
        )
    if code == 404:
        return "Not found (HTTP 404): {}. Check the user name or study id.".format(path)
    if code == 429:
        return "Lichess is still rate limiting us (HTTP 429). Try again later."
    return "Lichess answered with HTTP {} for {}.".format(code, path)


# --------------------------------------------------------------------------
# API calls
# --------------------------------------------------------------------------

def get_account_username(token, get=api_get):
    """GET /api/account -> username of the token owner."""
    try:
        data = json.loads(get("/api/account", token).decode("utf-8"))
        return data["username"]
    except (ValueError, KeyError, TypeError):
        raise StudyDlError("Unexpected answer from /api/account: no user name found.")


def parse_ndjson(text):
    """Parse newline delimited JSON into a list of dicts (empty lines are skipped)."""
    result = []
    for number, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            result.append(json.loads(line))
        except ValueError:
            raise StudyDlError("Cannot read line {} of the Lichess answer.".format(number))
    return result


def list_studies(username, token, get=api_get):
    """GET /api/study/by/{username} -> list of dicts with id, name, createdAt, updatedAt."""
    path = "/api/study/by/" + urllib.parse.quote(username, safe="")
    studies = parse_ndjson(get(path, token).decode("utf-8"))
    for study in studies:
        if "id" not in study or "name" not in study:
            raise StudyDlError("Unexpected answer from Lichess: a study has no id or name.")
    return studies


def download_study(study_id, token, get=api_get):
    """GET /api/study/{studyId}.pgn -> PGN of all chapters as bytes."""
    return get("/api/study/{}.pgn".format(urllib.parse.quote(study_id, safe="")), token)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *("COM{}".format(i) for i in range(1, 10)),
    *("LPT{}".format(i) for i in range(1, 10)),
}


def safe_filename(name, max_length=MAX_NAME_LENGTH):
    """Make a study name usable as part of a file name on Linux, Mac and Windows."""
    cleaned = _INVALID_CHARS.sub("_", name).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)[:max_length].rstrip(" .")
    if not cleaned:
        return "study"
    if cleaned.split(".")[0].upper() in _WINDOWS_RESERVED:
        cleaned = "_" + cleaned
    return cleaned


def study_filename(study):
    return "{}-{}.pgn".format(safe_filename(study["name"]), study["id"])


def format_date(milliseconds):
    if not isinstance(milliseconds, (int, float)):
        return "?"
    moment = datetime.fromtimestamp(milliseconds / 1000, tz=timezone.utc)
    return moment.strftime("%Y-%m-%d")


def format_study_line(number, width, study):
    return "{:>{w}}. {}  [{}, updated {}]".format(
        number, study["name"], study["id"], format_date(study.get("updatedAt")), w=width
    )


def parse_selection(text, count):
    """Parse the answer in interactive mode.

    Returns a sorted list of 0-based indexes, or None if the user wants to quit.
    Raises ValueError (with a message for the user) if the answer is invalid.
    """
    text = text.strip().lower()
    if text in ("q", "quit"):
        return None
    if text == "all":
        return list(range(count))
    if not text:
        raise ValueError("Please enter numbers (e.g. 1,3,5-7), 'all' or 'q'.")
    selected = set()
    for part in text.split(","):
        part = part.strip()
        match = re.fullmatch(r"(\d+)(?:\s*-\s*(\d+))?", part)
        if not match:
            raise ValueError("Cannot understand '{}'. Use e.g. 1,3,5-7.".format(part))
        first = int(match.group(1))
        last = int(match.group(2)) if match.group(2) else first
        if first > last:
            raise ValueError("The range '{}' is the wrong way around.".format(part))
        if first < 1 or last > count:
            raise ValueError("Numbers must be between 1 and {}.".format(count))
        selected.update(range(first - 1, last))
    return sorted(selected)


def choose_interactively(studies, input_fn=input, output=print):
    """Show the numbered list and ask until the answer is valid. None means quit."""
    width = len(str(len(studies)))
    for number, study in enumerate(studies, start=1):
        output(format_study_line(number, width, study))
    while True:
        try:
            answer = input_fn("Which studies to save? (e.g. 1,3,5-7 / all / q): ")
        except EOFError:
            return None
        try:
            indexes = parse_selection(answer, len(studies))
        except ValueError as err:
            output(str(err))
            continue
        if indexes is None:
            return None
        return [studies[i] for i in indexes]


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="studydl.py",
        description=(
            "Save your Lichess studies as PGN files on your computer. "
            "Each study becomes one file (with all its chapters)."
        ),
        epilog=HELP_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--user",
        metavar="NAME",
        help="user whose studies are saved (default: the owner of the access token)",
    )
    parser.add_argument(
        "--type",
        choices=["own"],
        default="own",
        help="which studies to save; only 'own' (studies created by the user) "
        "is available at the moment (default: own)",
    )
    parser.add_argument(
        "--out",
        metavar="DIR",
        default="studies",
        help="folder where the PGN files are written, created if missing "
        "(default: ./studies)",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="show the studies as a numbered list and ask which ones to save",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="only show which studies would be saved, write nothing",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace files that already exist (default: skip them)",
    )
    return parser


def run(args, token, get=api_get, input_fn=input, output=print):
    """Do the work. Returns the exit code. Raises StudyDlError on fatal problems."""
    username = args.user or get_account_username(token, get)
    studies = list_studies(username, token, get)
    if not studies:
        output("No studies found for {}.".format(username))
        return EXIT_OK
    output("Found {} studies of {}.".format(len(studies), username))

    if args.interactive:
        studies = choose_interactively(studies, input_fn, output)
        if studies is None:
            output("Nothing selected, nothing saved.")
            return EXIT_OK
    elif args.dry_run:
        width = len(str(len(studies)))
        for number, study in enumerate(studies, start=1):
            output(format_study_line(number, width, study))

    out_dir = Path(args.out)
    saved = skipped = failed = 0
    for study in studies:
        target = out_dir / study_filename(study)
        if args.dry_run:
            output("Would save {}".format(target))
            continue
        if target.exists() and not args.overwrite:
            output("Skipped (exists): {}".format(target))
            skipped += 1
            continue
        try:
            pgn = download_study(study["id"], token, get)
            out_dir.mkdir(parents=True, exist_ok=True)
            target.write_bytes(pgn)
        except StudyDlError as err:
            print("Failed {} ({}): {}".format(study["id"], study["name"], err), file=sys.stderr)
            failed += 1
            continue
        except OSError as err:
            print("Cannot write {}: {}".format(target, err), file=sys.stderr)
            failed += 1
            continue
        output("Saved: {}".format(target))
        saved += 1

    if args.dry_run:
        output("Dry run: {} studies would be considered, nothing written.".format(len(studies)))
        return EXIT_OK
    output("Done: {} saved, {} skipped, {} failed.".format(saved, skipped, failed))
    return EXIT_FAILED if failed else EXIT_OK


def main(argv=None, get=api_get, input_fn=input, environ=None):
    args = build_parser().parse_args(argv)
    environ = os.environ if environ is None else environ
    token = environ.get(TOKEN_ENV, "").strip()
    if not token:
        print(
            "Error: the environment variable {env} is not set.\n"
            "studydl needs a personal access token with the scope 'study:read'.\n"
            "Create one as described here: {doc}\n"
            "Then set it, for example:\n"
            "  Linux / Mac:         export {env}=lip_xxxxxxxx\n"
            "  Windows (cmd):       set {env}=lip_xxxxxxxx\n"
            "  Windows (PowerShell): $env:{env} = \"lip_xxxxxxxx\"\n"
            "Run 'studydl.py --help' for more information.".format(
                env=TOKEN_ENV, doc=TOKEN_DOC_URL
            ),
            file=sys.stderr,
        )
        return EXIT_USAGE
    try:
        return run(args, token, get, input_fn)
    except StudyDlError as err:
        print("Error: {}".format(err), file=sys.stderr)
        return EXIT_FAILED
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return EXIT_FAILED


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    sys.exit(main())
