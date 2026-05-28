from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from inbox_app.agents_bridge import build_context
from inbox_app.review import build_review_inbox, format_review_inbox, perform_review_action
from inbox_app.review_server import serve_review_server

RELOAD_POLL_INTERVAL_SECONDS = 0.5
RELOAD_CHILD_ENV = "CE_REVIEW_SERVER_RELOAD"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _reload_watch_paths(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    entrypoint = repo_root / "bin" / "ce-inbox"
    if entrypoint.exists():
        paths.append(entrypoint)
    config_path = repo_root / "config" / "inbox.toml"
    if config_path.exists():
        paths.append(config_path)
    package_root = repo_root / "inbox_app"
    if package_root.exists():
        paths.extend(sorted(package_root.rglob("*.py")))
    return paths


def _reload_snapshot(repo_root: Path) -> dict[str, int]:
    snapshot: dict[str, int] = {}
    for path in _reload_watch_paths(repo_root):
        try:
            snapshot[str(path)] = path.stat().st_mtime_ns
        except FileNotFoundError:
            continue
    return snapshot


def _changed_reload_paths(previous: dict[str, int], current: dict[str, int], repo_root: Path) -> list[str]:
    changed: list[str] = []
    for raw_path in sorted(set(previous) | set(current)):
        if previous.get(raw_path) == current.get(raw_path):
            continue
        path = Path(raw_path)
        try:
            changed.append(str(path.relative_to(repo_root)))
        except ValueError:
            changed.append(str(path))
    return changed


def _terminate_child_process(child: subprocess.Popen) -> None:
    if child.poll() is not None:
        return
    child.terminate()
    try:
        child.wait(timeout=5)
    except subprocess.TimeoutExpired:
        child.kill()
        child.wait(timeout=5)


def _spawn_reload_child(args: argparse.Namespace, repo_root: Path) -> subprocess.Popen:
    env = os.environ.copy()
    env[RELOAD_CHILD_ENV] = "1"
    return subprocess.Popen(
        [
            sys.executable,
            str(repo_root / "bin" / "ce-inbox"),
            "review-server",
            "--host",
            args.host,
            "--port",
            str(args.port),
        ],
        cwd=repo_root,
        env=env,
        start_new_session=True,
    )


def command_review_server_with_reload(args: argparse.Namespace) -> int:
    repo_root = _repo_root()
    snapshot = _reload_snapshot(repo_root)
    print(f"review server autoreload enabled; watching {len(snapshot)} files")
    child = _spawn_reload_child(args, repo_root)
    child_exit_reported = False
    try:
        while True:
            time.sleep(RELOAD_POLL_INTERVAL_SECONDS)
            if child.poll() is not None and not child_exit_reported:
                print(f"review server exited with status {child.returncode}; waiting for changes")
                child_exit_reported = True
            current_snapshot = _reload_snapshot(repo_root)
            if current_snapshot == snapshot:
                continue
            changed = _changed_reload_paths(snapshot, current_snapshot, repo_root)
            snapshot = current_snapshot
            summary = ", ".join(changed[:3])
            if len(changed) > 3:
                summary = f"{summary}, ..."
            if child.poll() is None:
                print(f"code change detected; restarting review server ({summary})")
                _terminate_child_process(child)
            else:
                print(f"code change detected; restarting after failed run ({summary})")
            child = _spawn_reload_child(args, repo_root)
            child_exit_reported = False
    except KeyboardInterrupt:
        _terminate_child_process(child)
        print("review server stopped")
    return 0


def command_review_inbox(args: argparse.Namespace) -> int:
    context = build_context()
    inbox = build_review_inbox(context)
    if args.json:
        print(json.dumps(inbox, indent=2, sort_keys=True))
    else:
        print(format_review_inbox(inbox))
    return 0


def command_review_action(args: argparse.Namespace) -> int:
    context = build_context()
    result = perform_review_action(
        context,
        episode_id=args.episode_id,
        gate_type=args.gate_type,
        item_id=args.item_id,
        decision=args.decision,
        reviewer=args.reviewer,
        notes=args.notes or "",
        tags=args.tag or [],
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def command_review_server(args: argparse.Namespace) -> int:
    if args.reload and os.environ.get(RELOAD_CHILD_ENV) != "1":
        return command_review_server_with_reload(args)
    context = build_context()
    print(f"review server listening on http://{args.host}:{args.port}/review")
    try:
        serve_review_server(
            context,
            host=args.host,
            port=args.port,
            dev_reload_enabled=os.environ.get(RELOAD_CHILD_ENV) == "1",
        )
    except KeyboardInterrupt:
        print("review server stopped")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ce-inbox")
    subparsers = parser.add_subparsers(dest="command", required=True)

    review_inbox_parser = subparsers.add_parser("review-inbox")
    review_inbox_parser.add_argument("--json", action="store_true")

    review_action_parser = subparsers.add_parser("review-action")
    review_action_parser.add_argument("episode_id")
    review_action_parser.add_argument("gate_type")
    review_action_parser.add_argument("item_id", nargs="?")
    review_action_parser.add_argument("--decision", required=True, choices=("approve", "reject", "unapprove", "unreject"))
    review_action_parser.add_argument("--reviewer")
    review_action_parser.add_argument("--notes")
    review_action_parser.add_argument("--tag", action="append", default=[])

    review_server_parser = subparsers.add_parser("review-server")
    review_server_parser.add_argument("--host", default="127.0.0.1")
    review_server_parser.add_argument("--port", type=int, default=8765)
    review_server_parser.add_argument("--reload", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    commands = {
        "review-inbox": command_review_inbox,
        "review-action": command_review_action,
        "review-server": command_review_server,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
