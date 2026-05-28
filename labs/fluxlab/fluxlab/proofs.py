from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import RuntimeConfig
from .io import read_json, timestamp_slug, write_json
from .runs import candidate_seeds, maybe_queue_prompt
from .workflows import export_workflow_files

PROOF_STAGE = "proof"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def _require_keys(payload: dict[str, Any], keys: list[str], label: str) -> None:
    missing = [key for key in keys if key not in payload]
    if missing:
        raise ValueError(f"{label} is missing required keys: {', '.join(missing)}")


def proof_suite_path(root: Path, suite_id: str) -> Path:
    return root / f"{suite_id}.json"


def _validate_style(style: dict[str, Any], *, label: str) -> None:
    _require_keys(
        style,
        [
            "id",
            "source_master_prompt_path",
            "source_negative_prompt_path",
            "positive_style_prompt",
            "negative_prompt",
        ],
        label,
    )
    for key in ("id", "source_master_prompt_path", "source_negative_prompt_path", "positive_style_prompt", "negative_prompt"):
        value = str(style[key]).strip()
        if not value:
            raise ValueError(f"{label} `{key}` must be a non-empty string.")


def _validate_case(case: dict[str, Any], *, label: str) -> None:
    _require_keys(case, ["id", "archetype", "prompt_body", "base_seed"], label)
    for key in ("id", "archetype", "prompt_body"):
        value = str(case[key]).strip()
        if not value:
            raise ValueError(f"{label} `{key}` must be a non-empty string.")
    if not isinstance(case["base_seed"], int):
        raise ValueError(f"{label} `base_seed` must be an integer.")


def _validate_render_overrides(render_overrides: dict[str, Any], *, label: str) -> None:
    _require_keys(render_overrides, ["width", "height", "batch_size", "steps"], label)
    for key in ("width", "height", "batch_size", "steps"):
        value = render_overrides[key]
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{label} `{key}` must be a positive integer.")


def validate_proof_suite(suite: dict[str, Any], *, path: Path | None = None) -> None:
    label = f"proof suite `{path.name}`" if path else "proof suite"
    _require_keys(suite, ["suite_id", "styles", "cases", "render_overrides"], label)
    if str(suite["suite_id"]).strip() == "":
        raise ValueError(f"{label} `suite_id` must be a non-empty string.")
    styles = suite["styles"]
    cases = suite["cases"]
    render_overrides = suite["render_overrides"]
    if not isinstance(styles, list) or not styles:
        raise ValueError(f"{label} `styles` must be a non-empty list.")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"{label} `cases` must be a non-empty list.")
    if not isinstance(render_overrides, dict):
        raise ValueError(f"{label} `render_overrides` must be an object.")
    _validate_render_overrides(render_overrides, label=label)

    style_ids: set[str] = set()
    for style in styles:
        if not isinstance(style, dict):
            raise ValueError(f"{label} styles entries must be objects.")
        _validate_style(style, label=label)
        style_id = style["id"]
        if style_id in style_ids:
            raise ValueError(f"{label} has duplicate style id `{style_id}`.")
        style_ids.add(style_id)

    case_ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError(f"{label} cases entries must be objects.")
        _validate_case(case, label=label)
        case_id = case["id"]
        if case_id in case_ids:
            raise ValueError(f"{label} has duplicate case id `{case_id}`.")
        case_ids.add(case_id)


def load_proof_suite(path: Path) -> dict[str, Any]:
    suite = read_json(path)
    validate_proof_suite(suite, path=path)
    return suite


def load_proof_suite_by_id(root: Path, suite_id: str) -> tuple[Path, dict[str, Any]]:
    path = proof_suite_path(root, suite_id)
    if not path.exists():
        raise ValueError(f"Proof suite `{suite_id}` does not exist at `{path}`.")
    return path, load_proof_suite(path)


def _select_entries(entries: list[dict[str, Any]], entry_id: str | None, *, label: str) -> list[dict[str, Any]]:
    if entry_id is None:
        return list(entries)
    selected = [entry for entry in entries if entry["id"] == entry_id]
    if not selected:
        raise ValueError(f"{label} `{entry_id}` is not defined in this suite.")
    return selected


def _compile_positive_prompt(style_prompt: str, prompt_body: str) -> str:
    return ", ".join(part for part in (style_prompt.strip(), prompt_body.strip()) if part)


def proof_output_prefix(
    runtime: RuntimeConfig,
    *,
    suite_id: str,
    run_id: str,
    case_id: str,
    style_id: str,
) -> str:
    stem = f"{case_id}__{style_id}"
    return f"{runtime.output_namespace}/proofs/{suite_id}/{run_id}/{case_id}/{style_id}/{stem}"


def _proof_export_dir(runtime: RuntimeConfig, *, suite_id: str, run_id: str, case_id: str, style_id: str) -> Path:
    return runtime.exports_root / "proofs" / suite_id / run_id / case_id / style_id


def _proof_run_manifest_path(runtime: RuntimeConfig, *, suite_id: str, run_id: str) -> Path:
    return runtime.runs_root / "proofs" / suite_id / f"{run_id}.json"


def _proof_report_json_path(runtime: RuntimeConfig, *, suite_id: str, run_id: str) -> Path:
    return runtime.reports_root / "proofs" / suite_id / f"{run_id}.json"


def _proof_report_markdown_path(runtime: RuntimeConfig, *, suite_id: str, run_id: str) -> Path:
    return runtime.reports_root / "proofs" / suite_id / f"{run_id}.md"


def _build_job(
    runtime: RuntimeConfig,
    *,
    suite_id: str,
    run_id: str,
    case: dict[str, Any],
    style: dict[str, Any],
    render_overrides: dict[str, int],
) -> dict[str, Any]:
    positive_prompt = _compile_positive_prompt(style["positive_style_prompt"], case["prompt_body"])
    negative_prompt = str(style["negative_prompt"]).strip()
    filename_prefix = proof_output_prefix(
        runtime,
        suite_id=suite_id,
        run_id=run_id,
        case_id=case["id"],
        style_id=style["id"],
    )
    export_dir = _proof_export_dir(
        runtime,
        suite_id=suite_id,
        run_id=run_id,
        case_id=case["id"],
        style_id=style["id"],
    )
    artifact_name = f"{case['id']}__{style['id']}"
    workflow_paths = export_workflow_files(
        runtime,
        export_dir,
        positive_prompt=positive_prompt,
        negative_prompt=negative_prompt,
        width=render_overrides["width"],
        height=render_overrides["height"],
        batch_size=render_overrides["batch_size"],
        seed=case["base_seed"],
        filename_prefix=filename_prefix,
        scene_id=artifact_name,
        stage=PROOF_STAGE,
        steps=render_overrides["steps"],
    )
    return {
        "suite_id": suite_id,
        "case_id": case["id"],
        "style_id": style["id"],
        "archetype": case["archetype"],
        "prompt_body": case["prompt_body"],
        "base_seed": case["base_seed"],
        "candidate_seeds": candidate_seeds(case["base_seed"], render_overrides["batch_size"]),
        "positive_style_prompt": style["positive_style_prompt"],
        "negative_prompt": negative_prompt,
        "positive_prompt": positive_prompt,
        "source_master_prompt_path": style["source_master_prompt_path"],
        "source_negative_prompt_path": style["source_negative_prompt_path"],
        "width": render_overrides["width"],
        "height": render_overrides["height"],
        "batch_size": render_overrides["batch_size"],
        "steps": render_overrides["steps"],
        "filename_prefix": filename_prefix,
        "ui_workflow_path": str(workflow_paths["ui_path"]),
        "api_workflow_path": str(workflow_paths["api_path"]),
        "queue": None,
    }


def export_proof_suite(
    runtime: RuntimeConfig,
    *,
    suite_id: str,
    case_id: str | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    suite_path, suite = load_proof_suite_by_id(runtime.proof_suites_root, suite_id)
    export_run_id = run_id or timestamp_slug()
    selected_cases = _select_entries(suite["cases"], case_id, label="Case")
    jobs = [
        _build_job(
            runtime,
            suite_id=suite_id,
            run_id=export_run_id,
            case=case,
            style=style,
            render_overrides=suite["render_overrides"],
        )
        for case in selected_cases
        for style in suite["styles"]
    ]
    payload = {
        "suite_id": suite_id,
        "stage": PROOF_STAGE,
        "run_id": export_run_id,
        "suite_manifest_path": str(suite_path),
        "filters": {"case_id": case_id},
        "render_overrides": suite["render_overrides"],
        "styles": suite["styles"],
        "cases": selected_cases,
        "jobs": jobs,
    }
    run_manifest_path = _proof_run_manifest_path(runtime, suite_id=suite_id, run_id=export_run_id)
    payload["run_manifest_path"] = str(run_manifest_path)
    write_json(run_manifest_path, payload)
    return payload


def render_proof_suite(
    runtime: RuntimeConfig,
    *,
    suite_id: str,
    case_id: str | None = None,
) -> dict[str, Any]:
    payload = export_proof_suite(runtime, suite_id=suite_id, case_id=case_id)
    for job in payload["jobs"]:
        job["queue"] = maybe_queue_prompt(runtime, Path(job["api_workflow_path"]))
    write_json(Path(payload["run_manifest_path"]), payload)
    return payload


def _discover_image_paths(runtime: RuntimeConfig, filename_prefix: str) -> list[str]:
    output_root = runtime.comfy_root / "output"
    prefix_path = output_root / filename_prefix
    parent = prefix_path.parent
    if not parent.exists():
        return []
    return [
        str(candidate)
        for candidate in sorted(parent.glob(f"{prefix_path.name}*"))
        if candidate.is_file() and candidate.suffix.lower() in IMAGE_SUFFIXES
    ]


def _build_case_report(case: dict[str, Any], styles: list[dict[str, Any]], jobs_by_key: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    style_reports = []
    for style in styles:
        job = jobs_by_key[(case["id"], style["id"])]
        style_reports.append(
            {
                "style_id": style["id"],
                "source_master_prompt_path": job["source_master_prompt_path"],
                "source_negative_prompt_path": job["source_negative_prompt_path"],
                "positive_prompt": job["positive_prompt"],
                "negative_prompt": job["negative_prompt"],
                "candidate_seeds": job["candidate_seeds"],
                "width": job["width"],
                "height": job["height"],
                "batch_size": job["batch_size"],
                "steps": job["steps"],
                "filename_prefix": job["filename_prefix"],
                "ui_workflow_path": job["ui_workflow_path"],
                "api_workflow_path": job["api_workflow_path"],
                "queue": job.get("queue"),
                "image_paths": job["image_paths"],
                "review": {"notes": ""},
            }
        )
    return {
        "case_id": case["id"],
        "archetype": case["archetype"],
        "prompt_body": case["prompt_body"],
        "base_seed": case["base_seed"],
        "styles": style_reports,
    }


def _render_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        f"# Proof Report: {report['suite_id']}",
        "",
        f"- Run ID: `{report['run_id']}`",
        f"- Stage: `{report['stage']}`",
        f"- Suite manifest: `{report['suite_manifest_path']}`",
        "",
    ]
    for case in report["cases"]:
        lines.extend(
            [
                f"## {case['case_id']}",
                "",
                f"- Archetype: `{case['archetype']}`",
                f"- Prompt body: {case['prompt_body']}",
                f"- Base seed: `{case['base_seed']}`",
                "",
            ]
        )
        for style in case["styles"]:
            image_paths = style["image_paths"] or ["(none found yet)"]
            lines.extend(
                [
                    f"### {style['style_id']}",
                    "",
                    f"- Source master prompt: `{style['source_master_prompt_path']}`",
                    f"- Source negative prompt: `{style['source_negative_prompt_path']}`",
                    f"- Positive prompt: {style['positive_prompt']}",
                    f"- Negative prompt: {style['negative_prompt']}",
                    f"- Candidate seeds: `{', '.join(str(seed) for seed in style['candidate_seeds'])}`",
                    f"- Render params: `{style['width']}x{style['height']}`, batch `{style['batch_size']}`, steps `{style['steps']}`",
                    f"- Filename prefix: `{style['filename_prefix']}`",
                    f"- UI workflow: `{style['ui_workflow_path']}`",
                    f"- API workflow: `{style['api_workflow_path']}`",
                    "- Image paths:",
                ]
            )
            lines.extend(f"  - `{image_path}`" for image_path in image_paths)
            lines.extend(
                [
                    "- Review notes: ",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def build_proof_report(runtime: RuntimeConfig, *, suite_id: str, run_id: str) -> dict[str, Any]:
    run_manifest_path = _proof_run_manifest_path(runtime, suite_id=suite_id, run_id=run_id)
    run_manifest = read_json(run_manifest_path)
    jobs_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for job in run_manifest["jobs"]:
        job_with_outputs = dict(job)
        job_with_outputs["image_paths"] = _discover_image_paths(runtime, job["filename_prefix"])
        jobs_by_key[(job["case_id"], job["style_id"])] = job_with_outputs

    cases = [
        _build_case_report(case, run_manifest["styles"], jobs_by_key)
        for case in run_manifest["cases"]
    ]
    report = {
        "suite_id": run_manifest["suite_id"],
        "run_id": run_manifest["run_id"],
        "stage": run_manifest["stage"],
        "suite_manifest_path": run_manifest["suite_manifest_path"],
        "run_manifest_path": str(run_manifest_path),
        "cases": cases,
    }
    json_path = _proof_report_json_path(runtime, suite_id=suite_id, run_id=run_id)
    markdown_path = _proof_report_markdown_path(runtime, suite_id=suite_id, run_id=run_id)
    write_json(json_path, report)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(_render_markdown_report(report), encoding="utf-8")
    return report | {"report_json_path": str(json_path), "report_markdown_path": str(markdown_path)}
