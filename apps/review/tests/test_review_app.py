from __future__ import annotations

from pathlib import Path
import re
from types import SimpleNamespace
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request

from inbox_app.agents_bridge import (
    AGENTS_ROOT,
    build_context,
    load_inbox_config,
    resolve_production_tools_root,
)
from inbox_app.cli import _reload_watch_paths, build_parser
from inbox_app.review_brand import load_signal_brand_theme
from inbox_app.review_server import build_review_server, render_review_page


def _root_css_variable(html: str, name: str) -> str:
    root_match = re.search(r":root\s*\{(?P<body>.*?)\n\s*\}", html, re.DOTALL)
    if not root_match:
        raise AssertionError("Rendered review page is missing a :root CSS block.")
    value_match = re.search(rf"{re.escape(name)}:\s*(?P<value>[^;]+);", root_match.group("body"))
    if not value_match:
        raise AssertionError(f"Rendered review page is missing {name}.")
    return value_match.group("value").strip()


def _fetch(url: str, *, range_header: str | None = None) -> tuple[int, object, bytes]:
    headers = {"Range": range_header} if range_header else {}
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, response.headers, response.read()
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, exc.headers, exc.read()
        finally:
            exc.close()


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

    def test_review_server_parser_supports_reload(self) -> None:
        parser = build_parser()

        args = parser.parse_args(["review-server", "--reload", "--port", "9876"])

        self.assertEqual(args.command, "review-server")
        self.assertTrue(args.reload)
        self.assertEqual(args.port, 9876)

    def test_reload_watch_paths_include_review_python_sources(self) -> None:
        review_root = Path(__file__).resolve().parents[1]
        paths = _reload_watch_paths(review_root)

        self.assertTrue(any(path.name == "review_server.py" for path in paths))
        self.assertTrue(any(path.name == "cli.py" for path in paths))

    def test_review_page_base_theme_keeps_dark_surfaces_readable(self) -> None:
        context = build_context()
        theme = load_signal_brand_theme(context)
        html = render_review_page(title="Review Desk", theme=theme)

        self.assertIn("color-scheme: dark;", html)
        self.assertNotEqual(_root_css_variable(html, "--paper"), _root_css_variable(html, "--text-primary"))
        self.assertNotEqual(_root_css_variable(html, "--paper"), _root_css_variable(html, "--muted"))

    def test_review_page_uses_neutral_theme_overrides(self) -> None:
        context = build_context()
        theme = load_signal_brand_theme(context)
        html = render_review_page(title="Review Desk", theme=theme)

        self.assertEqual(_root_css_variable(html, "--paper"), "#171717")
        self.assertEqual(_root_css_variable(html, "--paper-strong"), "rgba(62, 62, 62, 0.98)")
        self.assertEqual(_root_css_variable(html, "--signal"), "#D8D8D8")
        self.assertEqual(_root_css_variable(html, "--alert"), "#E8E8E8")
        self.assertIn("#191919", _root_css_variable(html, "--body-bg"))
        self.assertIn("#353535", _root_css_variable(html, "--stage-bg"))
        self.assertNotIn("#78DCE8", html)
        self.assertNotIn("#5D568E", html)
        self.assertNotIn("#FF6F61", html)

    def test_asset_route_supports_byte_ranges(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            asset_root = Path(temporary_directory)
            asset_path = asset_root / "sample.bin"
            asset_path.write_bytes(b"0123456789")
            context = SimpleNamespace(channel={"paths": {"test_root": str(asset_root)}})
            server = build_review_server(context, port=0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                host, port = server.server_address
                query = urllib.parse.urlencode({"path": str(asset_path)})
                url = f"http://{host}:{port}/api/review/assets?{query}"

                status, headers, body = _fetch(url)
                self.assertEqual(status, 200)
                self.assertEqual(headers["Accept-Ranges"], "bytes")
                self.assertEqual(headers["Content-Length"], "10")
                self.assertEqual(body, b"0123456789")

                status, headers, body = _fetch(url, range_header="bytes=2-5")
                self.assertEqual(status, 206)
                self.assertEqual(headers["Accept-Ranges"], "bytes")
                self.assertEqual(headers["Content-Range"], "bytes 2-5/10")
                self.assertEqual(headers["Content-Length"], "4")
                self.assertEqual(body, b"2345")

                status, headers, body = _fetch(url, range_header="bytes=7-")
                self.assertEqual(status, 206)
                self.assertEqual(headers["Content-Range"], "bytes 7-9/10")
                self.assertEqual(body, b"789")

                status, headers, body = _fetch(url, range_header="bytes=-3")
                self.assertEqual(status, 206)
                self.assertEqual(headers["Content-Range"], "bytes 7-9/10")
                self.assertEqual(body, b"789")

                status, headers, body = _fetch(url, range_header="bytes=99-100")
                self.assertEqual(status, 416)
                self.assertEqual(headers["Accept-Ranges"], "bytes")
                self.assertEqual(headers["Content-Range"], "bytes */10")
                self.assertEqual(headers["Content-Length"], "0")
                self.assertEqual(body, b"")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
