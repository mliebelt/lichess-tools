"""Feature tests against the real Lichess API.

They are skipped unless the environment variable LICHESS_PAT contains a token
with the scope 'study:read'.

The study list is the slow call (all studies of the user in one answer), so it is
fetched only once for the whole class and replayed to every run of the tool
(`self.get`). The tests make only four real requests: the account, the study
list, one PGN download and the check with an invalid token.
"""

import contextlib
import io
import os
import sys
import tempfile
import unittest
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import studydl  # noqa: E402

TOKEN = os.environ.get("LICHESS_PAT", "").strip()


@unittest.skipUnless(TOKEN, "LICHESS_PAT is not set")
class LiveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Two real requests, shared by all tests.
        cls.username = studydl.get_account_username(TOKEN)
        cls.list_path = "/api/study/by/" + urllib.parse.quote(cls.username, safe="")
        cls.list_body = studydl.api_get(cls.list_path, TOKEN)
        cls.studies = studydl.list_studies(cls.username, TOKEN, get=lambda path, token: cls.list_body)

    def get(self, path, token):
        """Replay the saved study list, everything else (the PGN) really goes to Lichess."""
        if path == self.list_path:
            return self.list_body
        return studydl.api_get(path, token)

    def run_tool(self, argv, input_fn=input):
        """Run the tool for the user of the token; return exit code and the output lines.

        The output is silenced: study titles must not end up in CI logs, so the
        assertions only look at counts and study ids.
        """
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stdout(out):
                code = studydl.main(
                    ["--user", self.username, "--out", tmp] + argv,
                    get=self.get,
                    input_fn=input_fn,
                    environ={"LICHESS_PAT": TOKEN},
                )
            files = list(Path(tmp).glob("*.pgn"))
            sizes = [f.stat().st_size for f in files]
        return code, out.getvalue().splitlines(), sizes

    def test_account_and_study_list(self):
        self.assertTrue(self.username)
        for study in self.studies:
            self.assertEqual(len(study["id"]), 8)

    def test_download_first_study(self):
        if not self.studies:
            self.skipTest("the account has no studies")
        code, _, sizes = self.run_tool(["--interactive"], input_fn=lambda prompt: "1")
        self.assertEqual(code, studydl.EXIT_OK)
        self.assertEqual(len(sizes), 1)
        self.assertGreater(sizes[0], 0)

    def test_invalid_token_is_reported(self):
        with self.assertRaises(studydl.StudyDlError) as ctx:
            studydl.get_account_username("lip_invalid_token_for_test")
        self.assertIn("401", str(ctx.exception))

    # The since filter tests use fixed dates, never "now", so they are not
    # time dependent. They run on the saved study list and make no request.

    def would_save(self, argv):
        code, lines, sizes = self.run_tool(["--dry-run"] + argv)
        self.assertEqual(sizes, [])
        return code, [line for line in lines if line.startswith("Would save")]

    def test_created_since_old_date_keeps_all_studies(self):
        if not self.studies:
            self.skipTest("the account has no studies")
        code, would = self.would_save(["--created-since", "2000-01-01"])
        self.assertEqual(code, studydl.EXIT_OK)
        self.assertEqual(len(would), len(self.studies))

    def test_future_dates_match_nothing(self):
        argvs = [
            ["--created-since", "2099-01-01"],
            ["--changed-since", "2099-01-01"],
            ["--created-since", "2099-01-01", "--changed-since", "2099-01-01"],
        ]
        for argv in argvs:
            with self.subTest(argv=argv):
                code, lines, sizes = self.run_tool(argv)
                self.assertEqual(code, studydl.EXIT_OK)
                self.assertFalse(any("Would save" in line for line in lines))
                self.assertEqual(sizes, [])

    def test_created_since_includes_the_boundary_day(self):
        if not self.studies:
            self.skipTest("the account has no studies")
        study = self.studies[0]
        day = datetime.fromtimestamp(study["createdAt"] / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        code, would = self.would_save(["--created-since", day])
        self.assertEqual(code, studydl.EXIT_OK)
        # The id (not the title) identifies the study in the "Would save" line.
        self.assertTrue(
            any("-{}.pgn".format(study["id"]) in line for line in would),
            "the study created on the cutoff day is missing from the matches",
        )


if __name__ == "__main__":
    unittest.main()
