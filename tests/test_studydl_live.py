"""Feature tests against the real Lichess API.

They are skipped unless the environment variable LICHESS_PAT contains a token
with the scope 'study:read'.
"""

import os
import sys
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
