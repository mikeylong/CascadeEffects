from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmarks import build_benchmark_report, export_benchmark_suite, render_benchmark_suite
from .config import ensure_runtime_dirs, load_runtime
from .proofs import build_proof_report, export_proof_suite, render_proof_suite
from .runs import build_bootstrap_report, export_scene_stage, refine_from_lookdev, render_scene


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="bin/ceflux")
    parser.add_argument("--repo-root", required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("bootstrap")

    workflow_parser = subparsers.add_parser("workflow")
    workflow_sub = workflow_parser.add_subparsers(dest="workflow_command", required=True)
    workflow_export = workflow_sub.add_parser("export")
    workflow_export.add_argument("scene_id")
    workflow_export.add_argument("--stage", choices=["lookdev", "refine"], required=True)
    workflow_export.add_argument("--seed", type=int)

    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("scene_id")
    render_parser.add_argument("--stage", choices=["lookdev", "refine"], required=True)
    render_parser.add_argument("--seed", type=int)

    benchmark_parser = subparsers.add_parser("benchmark")
    benchmark_sub = benchmark_parser.add_subparsers(dest="benchmark_command", required=True)
    benchmark_export = benchmark_sub.add_parser("export")
    benchmark_export.add_argument("suite_id")
    benchmark_export.add_argument("--case")
    benchmark_export.add_argument("--style")

    benchmark_render = benchmark_sub.add_parser("render")
    benchmark_render.add_argument("suite_id")
    benchmark_render.add_argument("--case")
    benchmark_render.add_argument("--style")

    benchmark_report = benchmark_sub.add_parser("report")
    benchmark_report.add_argument("suite_id")
    benchmark_report.add_argument("--run", required=True)

    proof_parser = subparsers.add_parser("proof")
    proof_sub = proof_parser.add_subparsers(dest="proof_command", required=True)
    proof_export = proof_sub.add_parser("export")
    proof_export.add_argument("suite_id")
    proof_export.add_argument("--case")

    proof_render = proof_sub.add_parser("render")
    proof_render.add_argument("suite_id")
    proof_render.add_argument("--case")

    proof_report = proof_sub.add_parser("report")
    proof_report.add_argument("suite_id")
    proof_report.add_argument("--run", required=True)

    refine_parser = subparsers.add_parser("refine")
    refine_parser.add_argument("scene_id")
    refine_parser.add_argument("--run", required=True)
    refine_parser.add_argument("--pick", type=int, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runtime = load_runtime(Path(args.repo_root))
    ensure_runtime_dirs(runtime)

    if args.command == "bootstrap":
        payload = build_bootstrap_report(runtime)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["ok"] else 1

    if args.command == "workflow" and args.workflow_command == "export":
        payload = export_scene_stage(runtime, scene_id=args.scene_id, stage=args.stage, seed=args.seed)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "render":
        payload = render_scene(runtime, scene_id=args.scene_id, stage=args.stage, seed=args.seed)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "benchmark" and args.benchmark_command == "export":
        payload = export_benchmark_suite(runtime, suite_id=args.suite_id, case_id=args.case, style_id=args.style)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "benchmark" and args.benchmark_command == "render":
        payload = render_benchmark_suite(runtime, suite_id=args.suite_id, case_id=args.case, style_id=args.style)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "benchmark" and args.benchmark_command == "report":
        payload = build_benchmark_report(runtime, suite_id=args.suite_id, run_id=args.run)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "proof" and args.proof_command == "export":
        payload = export_proof_suite(runtime, suite_id=args.suite_id, case_id=args.case)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "proof" and args.proof_command == "render":
        payload = render_proof_suite(runtime, suite_id=args.suite_id, case_id=args.case)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "proof" and args.proof_command == "report":
        payload = build_proof_report(runtime, suite_id=args.suite_id, run_id=args.run)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "refine":
        payload = refine_from_lookdev(runtime, scene_id=args.scene_id, run_id=args.run, pick=args.pick)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    raise SystemExit(f"Unhandled command: {args.command}")
