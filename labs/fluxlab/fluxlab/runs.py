from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .config import RuntimeConfig
from .io import read_json, timestamp_slug, write_json
from .manifests import ALLOWED_SCENE_IDS, STAGE_DEFAULTS, load_scene, save_scene, scene_path
from .prompts import compile_negative_prompt, compile_positive_prompt
from .workflows import export_workflow_files


def candidate_seeds(base_seed: int, batch_size: int) -> list[int]:
    return [base_seed + offset for offset in range(batch_size)]


def resolve_seed(scene: dict[str, Any], stage: str, explicit_seed: int | None = None) -> int:
    if explicit_seed is not None:
        return explicit_seed
    selected_seed = scene.get("selected_seed")
    if isinstance(selected_seed, int):
        return selected_seed
    default_seed = 10000 + sum(ord(char) for char in str(scene["id"]))
    if stage == "lookdev":
        return default_seed
    raise ValueError("refine stage requires an explicit seed or a scene selected_seed.")


def output_prefix(runtime: RuntimeConfig, scene_id: str, stage: str, run_id: str) -> str:
    return f"{runtime.output_namespace}/{scene_id}/{run_id}/{stage}/{scene_id}"


def build_bootstrap_report(runtime: RuntimeConfig) -> dict[str, Any]:
    required_assets = {
        "prompt_canon": runtime.prompts_path.exists(),
        "raw_template": runtime.raw_template_path.exists(),
        "api_template": runtime.api_template_path.exists(),
    }
    for scene_id in sorted(ALLOWED_SCENE_IDS):
        required_assets[f"scene::{scene_id}"] = (runtime.scenes_root / f"{scene_id}.json").exists()
    required_models = {name: path.exists() for name, path in runtime.model_paths.items()}
    server_reachable = False
    server_error = ""
    try:
        with urllib.request.urlopen(f"{runtime.comfy_api_url}/system_stats", timeout=1.5) as response:
            if response.status == 200:
                server_reachable = True
    except Exception as exc:  # noqa: BLE001
        server_error = str(exc)
    missing_assets = [name for name, present in required_assets.items() if not present]
    missing_models = [name for name, present in required_models.items() if not present]
    return {
        "ok": not missing_assets and not missing_models,
        "repo_root": str(runtime.repo_root),
        "comfy_root": str(runtime.comfy_root),
        "comfy_api_url": runtime.comfy_api_url,
        "required_assets": required_assets,
        "required_models": {name: str(path) for name, path in runtime.model_paths.items()},
        "required_models_present": required_models,
        "missing_assets": missing_assets,
        "missing_models": missing_models,
        "server_reachable": server_reachable,
        "server_error": server_error,
    }


def maybe_queue_prompt(runtime: RuntimeConfig, api_workflow_path: Path) -> dict[str, Any]:
    bundle = read_json(api_workflow_path)
    request = urllib.request.Request(
        url=f"{runtime.comfy_api_url}/prompt",
        data=json.dumps({"prompt": bundle["prompt"]}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {"attempted": True, "queued": True, "response": payload}
    except urllib.error.URLError as exc:
        return {"attempted": True, "queued": False, "error": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"attempted": True, "queued": False, "error": str(exc)}


def export_scene_stage(
    runtime: RuntimeConfig,
    *,
    scene_id: str,
    stage: str,
    seed: int | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    scene_file = scene_path(runtime.scenes_root, scene_id)
    scene = load_scene(scene_file)
    stage_defaults = STAGE_DEFAULTS[stage]
    resolved_seed = resolve_seed(scene, stage, explicit_seed=seed)
    export_run_id = run_id or timestamp_slug()
    prefix = output_prefix(runtime, scene_id, stage, export_run_id)
    export_dir = runtime.exports_root / scene_id / export_run_id
    positive_prompt = compile_positive_prompt(scene)
    negative_prompt = compile_negative_prompt(scene)
    paths = export_workflow_files(
        runtime,
        export_dir,
        positive_prompt=positive_prompt,
        negative_prompt=negative_prompt,
        width=stage_defaults["width"],
        height=stage_defaults["height"],
        batch_size=stage_defaults["batch_size"],
        seed=resolved_seed,
        filename_prefix=prefix,
        scene_id=scene_id,
        stage=stage,
    )
    return {
        "scene_id": scene_id,
        "stage": stage,
        "run_id": export_run_id,
        "seed": resolved_seed,
        "width": stage_defaults["width"],
        "height": stage_defaults["height"],
        "batch_size": stage_defaults["batch_size"],
        "positive_prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "filename_prefix": prefix,
        "ui_workflow_path": str(paths["ui_path"]),
        "api_workflow_path": str(paths["api_path"]),
        "candidate_seeds": candidate_seeds(resolved_seed, stage_defaults["batch_size"]),
    }


def render_scene(
    runtime: RuntimeConfig,
    *,
    scene_id: str,
    stage: str,
    seed: int | None = None,
    source_run_id: str | None = None,
    selected_index: int | None = None,
) -> dict[str, Any]:
    payload = export_scene_stage(runtime, scene_id=scene_id, stage=stage, seed=seed)
    queue_result = maybe_queue_prompt(runtime, Path(payload["api_workflow_path"]))
    payload["queue"] = queue_result
    payload["source_run_id"] = source_run_id
    payload["selected_index"] = selected_index
    run_manifest_path = runtime.runs_root / scene_id / f"{payload['run_id']}.json"
    payload["run_manifest_path"] = str(run_manifest_path)
    write_json(run_manifest_path, payload)

    scene_file = scene_path(runtime.scenes_root, scene_id)
    scene = load_scene(scene_file)
    scene["outputs"][stage] = {
        "run_id": payload["run_id"],
        "run_manifest_path": str(run_manifest_path),
        "ui_workflow_path": payload["ui_workflow_path"],
        "api_workflow_path": payload["api_workflow_path"],
        "filename_prefix": payload["filename_prefix"],
        "queue": queue_result,
    }
    scene["selected_seed"] = payload["seed"]
    save_scene(scene_file, scene)
    return payload


def refine_from_lookdev(
    runtime: RuntimeConfig,
    *,
    scene_id: str,
    run_id: str,
    pick: int,
) -> dict[str, Any]:
    run_manifest_path = runtime.runs_root / scene_id / f"{run_id}.json"
    lookdev_manifest = read_json(run_manifest_path)
    if lookdev_manifest["stage"] != "lookdev":
        raise ValueError(f"Run `{run_id}` is not a lookdev run.")
    seeds = list(lookdev_manifest.get("candidate_seeds", []))
    if pick < 0 or pick >= len(seeds):
        raise ValueError(f"pick must be between 0 and {max(len(seeds) - 1, 0)}.")
    chosen_seed = int(seeds[pick])
    lookdev_manifest["selected_index"] = pick
    lookdev_manifest["selected_seed"] = chosen_seed
    write_json(run_manifest_path, lookdev_manifest)

    scene_file = scene_path(runtime.scenes_root, scene_id)
    scene = load_scene(scene_file)
    scene["selected_seed"] = chosen_seed
    scene.setdefault("outputs", {})["lookdev"] = {
        **scene.get("outputs", {}).get("lookdev", {}),
        "selected_index": pick,
        "selected_seed": chosen_seed,
        "selected_from_run_id": run_id,
    }
    save_scene(scene_file, scene)

    return render_scene(
        runtime,
        scene_id=scene_id,
        stage="refine",
        seed=chosen_seed,
        source_run_id=run_id,
        selected_index=pick,
    )
