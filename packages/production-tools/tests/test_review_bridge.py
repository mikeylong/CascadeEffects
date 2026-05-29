from __future__ import annotations

import unittest

from orchestration import review, review_brand, review_server
from orchestration.cli import inbox_helper_path
from orchestration.review_bridge import REVIEW_APP_ROOT, review_cli_helper_path


class ReviewBridgeTests(unittest.TestCase):
    def test_review_bridge_modules_import_migrated_review_app(self) -> None:
        for module in (review, review_brand, review_server):
            self.assertTrue(module._MODULE.__name__.startswith("inbox_app."))
            self.assertIn(str(REVIEW_APP_ROOT), str(module._MODULE.__file__))
            self.assertNotIn("Inbox_CascadeEffects", str(module._MODULE.__file__))

    def test_ce_orchestrate_review_helper_uses_apps_review(self) -> None:
        expected = REVIEW_APP_ROOT / "bin" / "ce-inbox"

        self.assertEqual(review_cli_helper_path(), expected)
        self.assertEqual(inbox_helper_path(), expected)
        self.assertIn("apps/review/bin/ce-inbox", str(inbox_helper_path()))
        self.assertNotIn("Inbox_CascadeEffects", str(inbox_helper_path()))


if __name__ == "__main__":
    unittest.main()
