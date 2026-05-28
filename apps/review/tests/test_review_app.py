from __future__ import annotations

import unittest

from inbox_app.agents_bridge import (
    AGENTS_ROOT,
    build_context,
    load_inbox_config,
    resolve_production_tools_root,
)
from inbox_app.cli import build_parser


class ReviewAppTests(unittest.TestCase):
    def test_config_resolves_production_tools_root(self) -> None:
        config = load_inbox_config()

        self.assertIn("production_tools_root", config)
        self.assertEqual(resolve_production_tools_root(), AGENTS_ROOT)

    def test_context_loads_registry_config_from_production_tools_root(self) -> None:
        context = build_context()

        self.assertEqual(context.root, AGENTS_ROOT)
        self.assertEqual(
            context.channel["paths"]["episodes_root"],
            "/Users/mike/CascadeEffects/episodes/season-02",
        )

    def test_legacy_cli_parser_still_supports_underlying_review_actions(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            ["review-action", "ep10-citicorp-center", "audio", "--decision", "approve"]
        )

        self.assertEqual(args.command, "review-action")
        self.assertEqual(args.episode_id, "ep10-citicorp-center")
        self.assertEqual(args.decision, "approve")


if __name__ == "__main__":
    unittest.main()
