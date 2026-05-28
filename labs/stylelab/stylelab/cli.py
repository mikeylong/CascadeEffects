from __future__ import annotations

import argparse
import json
from pathlib import Path

from .boards import build_motion_reel, build_still_contact_sheet
from .config import ensure_runtime_dirs, load_runtime
from .evaluation import run_evaluation
from .io import list_scene_paths, list_short_paths, read_json
from .manifests import ALLOWED_MODES, ALLOWED_PRESETS, load_profile, load_scene, load_short
from .motion import render_motion
from .rendering import render_still
from .shorts import build_short


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="bin/cestyle")
    parser.add_argument("--repo-root", required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("bootstrap")

    still_parser = subparsers.add_parser("still")
    still_sub = still_parser.add_subparsers(dest="still_command", required=True)
    still_render = still_sub.add_parser("render")
    still_render.add_argument("scene_id")
    still_render.add_argument("--mode", choices=sorted(ALLOWED_MODES), required=True)

    motion_parser = subparsers.add_parser("motion")
    motion_sub = motion_parser.add_subparsers(dest="motion_command", required=True)
    motion_render = motion_sub.add_parser("render")
    motion_render.add_argument("scene_id")
    motion_render.add_argument("--preset", choices=sorted(ALLOWED_PRESETS), required=True)

    board_parser = subparsers.add_parser("board")
    board_sub = board_parser.add_subparsers(dest="board_command", required=True)
    board_sub.add_parser("build")

    short_parser = subparsers.add_parser("short")
    short_sub = short_parser.add_subparsers(dest="short_command", required=True)
    short_build = short_sub.add_parser("build")
    short_build.add_argument("short_id")

    subparsers.add_parser("eval")
    return parser.parse_args()


def _load_profiles(runtime) -> dict[str, dict]:
    profiles: dict[str, dict] = {}
    for path in sorted(runtime.profiles_root.glob("*.json")):
        profile = load_profile(path)
        profiles[str(profile["id"])] = profile
    return profiles


def _scene_path(runtime, scene_id: str) -> Path:
    path = runtime.scenes_root / f"{scene_id}.json"
    if not path.exists():
        raise SystemExit(f"Unknown scene id: {scene_id}")
    return path


def _short_path(runtime, short_id: str) -> Path:
    path = runtime.shorts_root / f"{short_id}.json"
    if not path.exists():
        raise SystemExit(f"Unknown short id: {short_id}")
    return path


def command_bootstrap(runtime) -> int:
    ensure_runtime_dirs(runtime)
    payload = {
        "ok": True,
        "repo_root": str(runtime.repo_root),
        "python": str(runtime.stylelab_python),
        "ai_root": str(runtime.ai_root),
        "scene_count": len(list_scene_paths(runtime.scenes_root)),
        "short_count": len(list_short_paths(runtime.shorts_root)),
        "profile_count": len(list(runtime.profiles_root.glob("*.json"))),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_still_render(runtime, args: argparse.Namespace) -> int:
    scene_path = _scene_path(runtime, args.scene_id)
    scene = load_scene(scene_path)
    profiles = _load_profiles(runtime)
    profile = profiles[scene["style_profile"]]
    result = render_still(runtime, scene_path, scene, profile, mode=args.mode)
    print(json.dumps({"image_path": str(result.image_path), "manifest_path": str(result.manifest_path), "prompt": result.prompt}, indent=2, sort_keys=True))
    return 0


def command_motion_render(runtime, args: argparse.Namespace) -> int:
    scene_path = _scene_path(runtime, args.scene_id)
    scene = load_scene(scene_path)
    profiles = _load_profiles(runtime)
    profile = profiles[scene["style_profile"]]
    result = render_motion(runtime, scene_path, scene, profile, preset=args.preset)
    print(
        json.dumps(
            {
                "output_path": str(result.output_path),
                "manifest_path": str(result.manifest_path),
                "poster_path": str(result.poster_path),
                "still_path": str(result.still_path),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def command_board_build(runtime) -> int:
    scene_paths = list_scene_paths(runtime.scenes_root)
    still_contact_sheet = build_still_contact_sheet(runtime, scene_paths)
    motion_reel = build_motion_reel(runtime, scene_paths)
    print(json.dumps({"still_contact_sheet": str(still_contact_sheet), "motion_reel": str(motion_reel)}, indent=2, sort_keys=True))
    return 0


def command_short_build(runtime, args: argparse.Namespace) -> int:
    short_path = _short_path(runtime, args.short_id)
    short_manifest = load_short(short_path, scenes_root=runtime.scenes_root)
    profiles = _load_profiles(runtime)
    result = build_short(runtime, short_path, short_manifest, profiles)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def command_eval(runtime) -> int:
    scene_paths = list_scene_paths(runtime.scenes_root)
    profiles = _load_profiles(runtime)
    output_path = run_evaluation(runtime, scene_paths, profiles)
    print(json.dumps(read_json(output_path), indent=2, sort_keys=True))
    return 0


def main() -> int:
    args = parse_args()
    runtime = load_runtime(Path(args.repo_root).expanduser().resolve())
    ensure_runtime_dirs(runtime)

    if args.command == "bootstrap":
        return command_bootstrap(runtime)
    if args.command == "still" and args.still_command == "render":
        return command_still_render(runtime, args)
    if args.command == "motion" and args.motion_command == "render":
        return command_motion_render(runtime, args)
    if args.command == "board" and args.board_command == "build":
        return command_board_build(runtime)
    if args.command == "short" and args.short_command == "build":
        return command_short_build(runtime, args)
    if args.command == "eval":
        return command_eval(runtime)
    raise SystemExit(f"Unhandled command: {args.command}")
