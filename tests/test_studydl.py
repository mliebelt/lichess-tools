"""Unit tests for studydl.py. They need no network access."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import studydl  # noqa: E402

STUDIES = [
    {"id": "aaaaaaaa", "name": "Openings: Sicilian", "createdAt": 1700000000000, "updatedAt": 1700000100000},
    {"id": "bbbbbbbb", "name": "Endgames", "createdAt": 1700000000000, "updatedAt": 1700000200000},
    {"id": "cccccccc", "name": "Tactics", "createdAt": 1700000000000, "updatedAt": 1700000300000},
]
NDJSON = "\n".join(json.dumps(s) for s in STUDIES) + "\n"


class FakeApi:
    """Replaces studydl.api_get and records the calls."""

    def __init__(self, fail_ids=()):
        self.calls = []
        self.fail_ids = set(fail_ids)

    def __call__(self, path, token):
        self.calls.append(path)
        if path == "/api/account":
            return b'{"id": "me", "username": "Me"}'
        if path.startswith("/api/study/by/"):
            return NDJSON.encode("utf-8")
        if path.endswith(".pgn"):
            study_id = path.rsplit("/", 1)[1][:-4]
            if study_id in self.fail_ids:
                raise studydl.StudyDlError("boom")
            return ("[Event \"x\"]\n\n1. e4 *\n").encode("utf-8")
        raise AssertionError("unexpected path " + path)


def parse(argv):
    return studydl.build_parser().parse_args(argv)


class ParseSelectionTest(unittest.TestCase):
    def test_numbers_and_ranges(self):
        self.assertEqual(studydl.parse_selection("1,3,5-7", 8), [0, 2, 4, 5, 6])

    def test_spaces_and_duplicates(self):
        self.assertEqual(studydl.parse_selection(" 2 , 2, 1 - 2 ", 3), [0, 1])

    def test_all(self):
        self.assertEqual(studydl.parse_selection("ALL", 3), [0, 1, 2])

    def test_quit(self):
        self.assertIsNone(studydl.parse_selection("q", 3))
        self.assertIsNone(studydl.parse_selection("Quit", 3))

    def test_invalid(self):
        for text in ["", "abc", "0", "4", "3-1", "1,,2", "1-9", "-1"]:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    studydl.parse_selection(text, 3)


class SafeFilenameTest(unittest.TestCase):
    def test_invalid_characters_replaced(self):
        self.assertEqual(studydl.safe_filename('a<b>c:d"e/f\\g|h?i*j'), "a_b_c_d_e_f_g_h_i_j")

    def test_trailing_dots_and_spaces(self):
        self.assertEqual(studydl.safe_filename("name. . "), "name")

    def test_empty_becomes_study(self):
        self.assertEqual(studydl.safe_filename("  "), "study")
        self.assertEqual(studydl.safe_filename("..."), "study")

    def test_windows_reserved(self):
        self.assertEqual(studydl.safe_filename("con"), "_con")
        self.assertEqual(studydl.safe_filename("LPT1"), "_LPT1")

    def test_length_limit(self):
        self.assertLessEqual(len(studydl.safe_filename("x" * 500)), studydl.MAX_NAME_LENGTH)

    def test_keeps_unicode(self):
        self.assertEqual(studydl.safe_filename("Endspiel Türme"), "Endspiel Türme")

    def test_study_filename_contains_id(self):
        self.assertEqual(studydl.study_filename(STUDIES[0]), "Openings_ Sicilian-aaaaaaaa.pgn")


class NdjsonTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(studydl.parse_ndjson(NDJSON), STUDIES)

    def test_empty_lines_skipped(self):
        self.assertEqual(studydl.parse_ndjson('\n{"a": 1}\n\n'), [{"a": 1}])

    def test_bad_line(self):
        with self.assertRaises(studydl.StudyDlError) as ctx:
            studydl.parse_ndjson('{"a": 1}\nnot json\n')
        self.assertIn("line 2", str(ctx.exception))

    def test_list_studies_encodes_user_name(self):
        api = FakeApi()
        self.assertEqual(studydl.list_studies("Some User", "tok", api), STUDIES)
        self.assertEqual(api.calls, ["/api/study/by/Some%20User"])

    def test_list_studies_requires_id_and_name(self):
        def get(path, token):
            return b'{"id": "x"}\n'
        with self.assertRaises(studydl.StudyDlError):
            studydl.list_studies("me", "tok", get)


class HttpErrorTest(unittest.TestCase):
    def test_messages(self):
        self.assertIn("401", studydl.describe_http_error(401, "/p"))
        self.assertIn("study:read", studydl.describe_http_error(403, "/p"))
        self.assertIn("/p", studydl.describe_http_error(404, "/p"))
        self.assertIn("500", studydl.describe_http_error(500, "/p"))

    def _http_error(self, code):
        # An empty body (not None) so that close() works on all Python versions.
        err = urllib.error.HTTPError("https://lichess.org/p", code, "msg", {}, io.BytesIO())
        self.addCleanup(err.close)
        return err

    def test_api_get_maps_http_error(self):
        with mock.patch("urllib.request.urlopen", side_effect=self._http_error(403)):
            with self.assertRaises(studydl.StudyDlError) as ctx:
                studydl.api_get("/p", "tok")
        self.assertIn("study:read", str(ctx.exception))

    def test_api_get_network_error(self):
        with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("no route")):
            with self.assertRaises(studydl.StudyDlError) as ctx:
                studydl.api_get("/p", "tok")
        self.assertIn("internet", str(ctx.exception))

    def test_api_get_sends_bearer_token(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b"ok"
        with mock.patch("urllib.request.urlopen", return_value=response) as urlopen:
            self.assertEqual(studydl.api_get("/p", "secret"), b"ok")
        request = urlopen.call_args[0][0]
        self.assertEqual(request.get_header("Authorization"), "Bearer secret")
        self.assertEqual(request.full_url, "https://lichess.org/p")

    def test_api_get_retries_on_429(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b"ok"
        effects = [self._http_error(429), response]
        with mock.patch("urllib.request.urlopen", side_effect=effects), \
                mock.patch("time.sleep") as sleep, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(studydl.api_get("/p", "tok"), b"ok")
        sleep.assert_called_once_with(studydl.RATE_LIMIT_WAIT_SECONDS)

    def test_api_get_gives_up_after_retries(self):
        effects = [self._http_error(429)] * (studydl.MAX_RETRIES + 1)
        with mock.patch("urllib.request.urlopen", side_effect=effects), \
                mock.patch("time.sleep"), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(studydl.StudyDlError):
                studydl.api_get("/p", "tok")


class RunTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.out = Path(self._tmp.name) / "out"
        self.lines = []

    def run_tool(self, argv, api=None, inputs=()):
        api = api or FakeApi()
        answers = iter(inputs)
        args = parse(list(argv) + ["--out", str(self.out)])
        with contextlib.redirect_stderr(io.StringIO()):
            code = studydl.run(args, "tok", api, lambda prompt: next(answers), self.lines.append)
        return code, api

    def files(self):
        return sorted(p.name for p in self.out.glob("*.pgn")) if self.out.exists() else []

    def test_saves_all_using_account_user(self):
        code, api = self.run_tool([])
        self.assertEqual(code, studydl.EXIT_OK)
        self.assertEqual(len(self.files()), 3)
        self.assertEqual(api.calls[0], "/api/account")
        self.assertIn("/api/study/by/Me", api.calls)

    def test_user_option_skips_account_call(self):
        _, api = self.run_tool(["--user", "Other"])
        self.assertNotIn("/api/account", api.calls)
        self.assertIn("/api/study/by/Other", api.calls)

    def test_existing_files_skipped_unless_overwrite(self):
        self.run_tool([])
        target = self.out / studydl.study_filename(STUDIES[1])
        target.write_text("old")
        _, api = self.run_tool([])
        self.assertEqual(target.read_text(), "old")
        self.assertFalse([c for c in api.calls if c.endswith(".pgn")])
        self.run_tool(["--overwrite"])
        self.assertIn("1. e4", target.read_text())

    def test_dry_run_writes_nothing_and_downloads_nothing(self):
        code, api = self.run_tool(["--dry-run"])
        self.assertEqual(code, studydl.EXIT_OK)
        self.assertFalse(self.out.exists())
        self.assertFalse([c for c in api.calls if c.endswith(".pgn")])
        self.assertTrue(any("Would save" in line for line in self.lines))

    def test_interactive_selection(self):
        code, _ = self.run_tool(["-i"], inputs=["1,3"])
        self.assertEqual(code, studydl.EXIT_OK)
        self.assertEqual(
            self.files(),
            sorted([studydl.study_filename(STUDIES[0]), studydl.study_filename(STUDIES[2])]),
        )

    def test_interactive_reprompts_on_invalid_answer(self):
        self.run_tool(["-i"], inputs=["nonsense", "2"])
        self.assertEqual(self.files(), [studydl.study_filename(STUDIES[1])])

    def test_interactive_quit(self):
        code, _ = self.run_tool(["-i"], inputs=["q"])
        self.assertEqual(code, studydl.EXIT_OK)
        self.assertEqual(self.files(), [])

    def test_failed_download_gives_error_code_but_continues(self):
        code, _ = self.run_tool([], api=FakeApi(fail_ids=["bbbbbbbb"]))
        self.assertEqual(code, studydl.EXIT_FAILED)
        self.assertEqual(len(self.files()), 2)

    def test_no_studies(self):
        def get(path, token):
            return b""
        args = parse(["--user", "x", "--out", str(self.out)])
        self.assertEqual(studydl.run(args, "tok", get, input, self.lines.append), studydl.EXIT_OK)
        self.assertTrue(any("No studies" in line for line in self.lines))


class MainTest(unittest.TestCase):
    def test_missing_token_explains_how_to_set_it(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = studydl.main([], environ={})
        self.assertEqual(code, studydl.EXIT_USAGE)
        text = err.getvalue()
        self.assertIn("LICHESS_PAT", text)
        self.assertIn("export", text)
        self.assertIn("oauth-personal-token", text)

    def test_blank_token_counts_as_missing(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(studydl.main([], environ={"LICHESS_PAT": "  "}), studydl.EXIT_USAGE)

    def test_api_error_gives_message_and_error_code(self):
        def get(path, token):
            raise studydl.StudyDlError("nope")
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = studydl.main(["--user", "x"], get=get, environ={"LICHESS_PAT": "t"})
        self.assertEqual(code, studydl.EXIT_FAILED)
        self.assertIn("nope", err.getvalue())

    def test_help(self):
        for flag in ("-h", "--help"):
            with self.subTest(flag=flag):
                out = io.StringIO()
                with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as ctx:
                    studydl.main([flag], environ={})
                self.assertEqual(ctx.exception.code, 0)
                text = out.getvalue()
                for expected in ("--user", "--out", "--interactive", "--dry-run",
                                 "--overwrite", "examples:", "LICHESS_PAT", "study:read"):
                    self.assertIn(expected, text)

    def test_unknown_option_is_a_usage_error(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as ctx:
            studydl.main(["--bogus"], environ={})
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
