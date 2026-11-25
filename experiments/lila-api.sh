#!/bin/bash
# lila-api.sh - small curl wrapper to explore the Lichess study API by hand.
#
# Talks to exactly two servers, chosen with the -l flag (no way to point it elsewhere,
# so a token can never leak to another host):
#   prod    https://lichess.org       (default) - what the API does TODAY
#   local   http://localhost:9663     - our dev lila with new endpoints
#
# Token:
#   prod    uses LICHESS_PAT (your real token)
#   local   uses LICHESS_LOCAL_PAT (a token you create at http://localhost:9663/account/token)
# Both are sent as "Authorization: Bearer ...". Without a token, anonymous calls still work
# where the API allows it.
#
# Usage:
#   ./lila-api.sh list <username>          GET /api/study/by/<username>     (NDJSON per study)
#   ./lila-api.sh member                   GET /api/study/member            (new endpoint: only local!)
#   ./lila-api.sh pgn <studyId>            GET /api/study/<studyId>.pgn     (first lines only)
#   ./lila-api.sh raw <METHOD> <path>      anything else, e.g.: raw GET /api/user/<username>
#   ./lila-api.sh whoami                   GET /api/user/me                 (shows WHICH token is used)
#
# Examples:
#   ./lila-api.sh list someuser                          # public studies of a user (prod)
#   ./lila-api.sh -l list someuser                       # same on the local dev server
#   ./lila-api.sh -l member                              # our new endpoint, local, needs local PAT
#   ./lila-api.sh -l raw GET /api/study/by/someuser      # see the HTTP status explicitly
#   LICHESS_LOCAL_PAT=xxxx ./lila-api.sh -l member
#
# Every call prints a first line: "<server> HTTP <code> (<time>)" so you SEE the status code,
# then the body (pretty limited in size).

set -u

BASE_PROD="https://lichess.org"
BASE_LOCAL="http://localhost:9663"
EXTRA="${LICHESS_API_EXTRA:-}"   # spare place for extra curl options

usage() { sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'; }

SERVER="prod"
case "${1:-}" in
  -l) SERVER="local"; shift ;;
  -h|--help|help|"") usage; exit 0 ;;
esac

case "$SERVER" in
  prod)  BASE="$BASE_PROD";  TOKEN="${LICHESS_PAT:-}" ;;
  local) BASE="$BASE_LOCAL"; TOKEN="${LICHESS_LOCAL_PAT:-}" ;;
esac

call() {  # call <METHOD> <path> [pipe-filter]
  local method="$1" path="$2" filter="${3:-}"
  local args=(-sS -o /tmp/lila-api-body -w "HTTP %{http_code} (%{time_total}s)\n" -X "$method")
  [ -n "$TOKEN" ] && args+=(-H "Authorization: Bearer $TOKEN")
  local tokLabel="none"; [ -n "$TOKEN" ] && tokLabel="set"
  # shellcheck disable=SC2086
  echo "== $SERVER $method $BASE$path (token: $tokLabel)"
  # shellcheck disable=SC2086
  curl "${args[@]}" $EXTRA "$BASE$path"
  if [ -s /tmp/lila-api-body ]; then
    if [ -n "$filter" ]; then head -c 800 /tmp/lila-api-body | eval "$filter"; else head -c 800 /tmp/lila-api-body; echo; fi
  fi
}

case "${1:-}" in
  list)   [ -n "${2:-}" ] || { echo "usage: $0 list <username>"; exit 1; }; call GET "/api/study/by/$2" "cat" ;;
  member) call GET "/api/study/member" "cat" ;;
  pgn)    [ -n "${2:-}" ] || { echo "usage: $0 pgn <studyId>"; exit 1; }; call GET "/api/study/$2.pgn" "head -8" ;;
  whoami) call GET "/api/user/me" "cat" ;;
  raw)    [ -n "${3:-}" ] || { echo "usage: $0 raw <METHOD> <path>"; exit 1; }; shift; call "$1" "$2" "cat" ;;
  *) usage; exit 1 ;;
esac
