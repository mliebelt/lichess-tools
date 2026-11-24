"""Feature tests against the real Lichess API.

They are skipped unless the environment variable LICHESS_PAT contains a token
with the scope 'study:read'.
"""

import contextlib
import io
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import studydl  # noqa: E402

TOKEN = os.environ.get("LICHESS_PAT", "").strip()


@unittest.skipUnless(TOKEN, "LICHESS_PAT is not set")
class LiveTest(unittest.TestCase):
    def test_account_and_study_list(self):
        username = studydl.get_account_username(TOKEN)
        self.assertTrue(username)
        studies = studydl.list_studies(username, TOKEN)
        for study in studies:
            self.assertEqual(len(study["id"]), 8)

    def test_download_first_study(self):
        username = studydl.get_account_username(TOKEN)
        studies = studydl.list_studies(username, TOKEN)
        if not studies:
            self.skipTest("the account has no studies")
        with tempfile.TemporaryDirectory() as tmp:
            # Silence the output: the list of study titles must not end up in CI logs.
            with contextlib.redirect_stdout(io.StringIO()):
                code = studydl.main(
                    ["--out", tmp, "--user", username, "--interactive"],
                    input_fn=lambda prompt: "1",
                    environ={"LICHESS_PAT": TOKEN},
                )
            self.assertEqual(code, studydl.EXIT_OK)
            files = list(Path(tmp).glob("*.pgn"))
            self.assertEqual(len(files), 1)
            self.assertGreater(files[0].stat().st_size, 0)

    def test_invalid_token_is_reported(self):
        with self.assertRaises(studydl.StudyDlError) as ctx:
            studydl.get_account_username("lip_invalid_token_for_test")
        self.assertIn("401", str(ctx.exception))

    # The since filter tests use fixed dates, never "now", so they are not
    # time dependent. Study titles must not reach the CI log: the tool output
    # is silenced and the assertions only look at counts and study ids.

    def _dry_run(self, argv, tmp):
        username = studydl.get_account_username(TOKEN)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = studydl.main(
                ["--user", username, "--out", tmp, "--dry-run"] + argv,
                environ={"LICHESS_PAT": TOKEN},
            )
        return code, [line for line in out.getvalue().splitlines() if line.startswith("Would save")]

    def test_created_since_old_date_keeps_all_studies(self):
        username = studydl.get_account_username(TOKEN)
        studies = studydl.list_studies(username, TOKEN)
        if not studies:
            self.skipTest("the account has no studies")
        with tempfile.TemporaryDirectory() as tmp:
            code, would = self._dry_run(["--created-since", "2000-01-01"], tmp)
            self.assertEqual(code, studydl.EXIT_OK)
            self.assertEqual(len(would), len(studies))

    def test_future_dates_match_nothing(self):
        argvs = [
            ["--created-since", "2099-01-01"],
            ["--changed-since", "2099-01-01"],
            ["--created-since", "2099-01-01", "--changed-since", "2099-01-01"],
        ]
        username = studydl.get_account_username(TOKEN)
        for argv in argvs:
            with self.subTest(argv=argv):
                with tempfile.TemporaryDirectory() as tmp:
                    out = io.StringIO()
                    with contextlib.redirect_stdout(out):
                        code = studydl.main(
                            ["--user", username, "--out", tmp] + argv,
                            environ={"LICHESS_PAT": TOKEN},
                        )
                    self.assertEqual(code, studydl.EXIT_OK)
                    self.assertFalse(any("Would save" in line for line in out.getvalue().splitlines()))
                    self.assertFalse(list(Path(tmp).glob("*.pgn")))

    def test_created_since_includes_the_boundary_day(self):
        username = studydl.get_account_username(TOKEN)
        studies = studydl.list_studies(username, TOKEN)
        if not studies:
            self.skipTest("the account has no studies")
        study = studies[0]
        day = datetime.fromtimestamp(study["createdAt"] / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        with tempfile.TemporaryDirectory() as tmp:
            code, would = self._dry_run(["--created-since", day], tmp)
            self.assertEqual(code, studydl.EXIT_OK)
            # The id (not the title) identifies the study in the "Would save" line.
            self.assertTrue(
                any("-{}.pgn".format(study["id"]) in line for line in would),
                "the study created on the cutoff day is missing from the matches",
            )


if __name__ == "__main__":
    unittest.main()
